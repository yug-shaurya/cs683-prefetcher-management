#include "ipop.h"

#include <algorithm>
#include <cmath>
#include <cstdlib>
#include <iostream>
#include <string>

#include "cache.h"

namespace
{
uint64_t env_u64(const char* k, uint64_t d)
{
  const char* v = std::getenv(k);
  return v ? std::strtoull(v, nullptr, 10) : d;
}

double env_dbl(const char* k, double d)
{
  const char* v = std::getenv(k);
  return v ? std::strtod(v, nullptr) : d;
}
} // namespace

uint64_t ipop::now_cycles() const
{
  return static_cast<uint64_t>(intern_->current_time.time_since_epoch() / intern_->clock_period);
}

void ipop::prefetcher_initialize()
{
  window_len = env_u64("IPOP_WINDOW", 1024);
  window_min = env_u64("IPOP_WMIN", 256);
  window_max = env_u64("IPOP_WMAX", 8192);
  thr_up = env_dbl("IPOP_THR_UP", 0.25);
  thr_down = env_dbl("IPOP_THR_DOWN", 0.05);
  pe_up = env_dbl("IPOP_PE_UP", 0.5);
  pe_down = env_dbl("IPOP_PE_DOWN", -0.5);
  adaptive = env_u64("IPOP_ADAPTIVE", 0) != 0;
  alpha = env_dbl("IPOP_ALPHA", 1.0);
  lat_k = env_dbl("IPOP_K", 27.9);
  delta_hi = env_dbl("IPOP_DELTA_HI", 0.10);
  delta_lo = env_dbl("IPOP_DELTA_LO", 0.02);

  const char* p = std::getenv("IPOP_POLICY");
  policy = (p != nullptr && std::string(p) == "pe") ? 1 : 0;

  const char* lp = std::getenv("IPOP_LOG");
  if (lp != nullptr) {
    log_path = lp;
    wlog.open(log_path);
    if (wlog.is_open()) {
      wlog << "window_index,window_len,demand_accesses,signal,degree,pf_requested,"
           << "upf,poll,lat,pe,upf_events,poll_events,pq_full\n";
    }
  }
}

uint32_t ipop::prefetcher_cache_operate(
    champsim::address addr,
    champsim::address ip,
    uint8_t cache_hit,
    bool useful_prefetch,
    access_type type,
    uint32_t metadata_in)
{
  ++total_accesses;

  const uint64_t now = now_cycles();
  const uint64_t blk = champsim::block_number{addr}.to<uint64_t>();

  const bool is_demand = type == access_type::LOAD || type == access_type::RFO;

  if (is_demand)
    ++demand_accesses;

  if (useful_prefetch)
    ++useful_prefetches;

  // ---- I_UPF: a demand hit a line one of our prefetches brought in ----
  if (useful_prefetch) {
    auto it = pfht.find(blk);
    if (it != pfht.end()) {
      const uint64_t start = it->second.issue_time;
      const uint64_t end = it->second.filled ? it->second.fill_time : now;
      if (end > start) {
        const double lat = static_cast<double>(end - start);
        win_upf += lat;
        lat_sum += lat;
        ++lat_count;
      }
      ++cum_upf_events;
      pfht.erase(it);
    }
  }

  // ---- I_POLL: a demand miss on a line one of our prefetches evicted ----
  if (is_demand && cache_hit == 0) {
    auto it = poht.find(blk);
    if (it != poht.end()) {
      const double avg_lat = lat_count > 0 ? (lat_sum / static_cast<double>(lat_count)) : lat_k;
      win_poll += avg_lat;
      ++cum_poll_events;
      poht.erase(it);
    }
  }

  if (is_demand)
    ++phase_accesses;

  // ===================== window boundary =====================
  if (phase_accesses >= window_len) {
    double signal = 0.0;
    double pe = 0.0;

    if (policy == 0) {
      signal = phase_issued == 0
                   ? 0.0
                   : static_cast<double>(phase_useful) / static_cast<double>(phase_issued);
      if (signal >= thr_up)
        degree = std::min(MAX_DEGREE, degree + 1);
      else if (signal < thr_down)
        degree = std::max(MIN_DEGREE, degree - 1);
    } else {
      // PE in cycles, normalised per prefetch issued so the signal does not
      // grow simply because a higher degree issued more prefetches.
      pe = win_upf - win_poll - alpha * win_lat;
      const uint64_t denom = phase_issued > 0 ? phase_issued : 1;
      signal = pe / static_cast<double>(denom);
      if (signal > pe_up)
        degree = std::min(MAX_DEGREE, degree + 1);
      else if (signal < pe_down)
        degree = std::max(MIN_DEGREE, degree - 1);
    }

    // ---- adaptive window ----
    if (adaptive && have_prev) {
      const double d = std::fabs(signal - prev_signal);
      if (d > delta_hi)
        window_len = std::max(window_min, window_len / 2);
      else if (d < delta_lo)
        window_len = std::min(window_max, window_len * 2);
    }
    prev_signal = signal;
    have_prev = true;

    ++completed_phases;
    ++window_index;

    if (wlog.is_open()) {
      wlog << window_index << ',' << window_len << ',' << demand_accesses << ','
           << signal << ',' << degree << ',' << intern_->sim_stats.pf_requested << ','
           << win_upf << ',' << win_poll << ',' << win_lat << ',' << pe << ','
           << cum_upf_events << ',' << cum_poll_events << ',' << phase_pq_full << '\n';
    }

    phase_accesses = 0;
    phase_useful = 0;
    phase_issued = 0;
    phase_pq_full = 0;
    win_upf = 0.0;
    win_poll = 0.0;
    win_lat = 0.0;
  }
  // ===========================================================

  if (useful_prefetch)
    ++phase_useful;

  champsim::block_number block{addr};

  for (unsigned distance = 1; distance <= degree; ++distance) {
    champsim::address pf_addr{block + distance};

    // Do not prefetch across a 4 KB page boundary.
    if (champsim::page_number{pf_addr} != champsim::page_number{addr})
      break;

    ++prefetch_attempts;

    if (prefetch_line(pf_addr, true, metadata_in)) {
      ++phase_issued;
      ++prefetch_accepted;

      const uint64_t pf_blk = champsim::block_number{pf_addr}.to<uint64_t>();
      pfht[pf_blk] = pfht_entry{now, 0, false};
      pfht_fifo.push_back(pf_blk);
      while (pfht_fifo.size() > PFHT_MAX) {
        const uint64_t old = pfht_fifo.front();
        pfht_fifo.pop_front();
        pfht.erase(old);
      }

      // ---- I_LAT: demand requests in flight when we add traffic ----
      long inflight = 0;
      for (const auto& e : intern_->MSHR) {
        if (e.type == access_type::LOAD || e.type == access_type::RFO)
          ++inflight;
      }
      win_lat += static_cast<double>(inflight) * lat_k;
    } else {
      ++pq_full_events;
      ++phase_pq_full;
      win_lat += lat_k;
    }
  }

  return metadata_in;
}

uint32_t ipop::prefetcher_cache_fill(
    champsim::address addr,
    long set,
    long way,
    uint8_t prefetch,
    champsim::address evicted_addr,
    uint32_t metadata_in)
{
  const uint64_t now = now_cycles();

  if (prefetch != 0) {
    const uint64_t blk = champsim::block_number{addr}.to<uint64_t>();
    auto it = pfht.find(blk);
    if (it != pfht.end()) {
      it->second.fill_time = now;
      it->second.filled = true;
    }

    if (evicted_addr.to<uint64_t>() != 0) {
      const uint64_t victim = champsim::block_number{evicted_addr}.to<uint64_t>();
      poht[victim] = now;
      poht_fifo.push_back(victim);
      ++poht_inserts;
      while (poht_fifo.size() > POHT_MAX) {
        const uint64_t old = poht_fifo.front();
        poht_fifo.pop_front();
        poht.erase(old);
      }
    }
  }

  return metadata_in;
}

void ipop::prefetcher_final_stats()
{
  std::cout << "\n===== IPOP Prefetcher Statistics =====\n";
  std::cout << "Config: policy=" << (policy != 0 ? "pe" : "accuracy")
            << " window=" << window_len
            << " adaptive=" << adaptive
            << " wmin=" << window_min
            << " wmax=" << window_max
            << " thr_up=" << thr_up
            << " thr_down=" << thr_down
            << " pe_up=" << pe_up
            << " pe_down=" << pe_down
            << " alpha=" << alpha
            << " k=" << lat_k
            << " delta_hi=" << delta_hi
            << " delta_lo=" << delta_lo << '\n';
  std::cout << "Total callback accesses: " << total_accesses << '\n';
  std::cout << "Demand accesses (LOAD + RFO): " << demand_accesses << '\n';
  std::cout << "Useful-prefetch observations: " << useful_prefetches << '\n';
  std::cout << "Prefetch attempts: " << prefetch_attempts << '\n';
  std::cout << "Prefetch requests accepted: " << prefetch_accepted << '\n';
  std::cout << "PQ-full drops: " << pq_full_events << '\n';
  std::cout << "PoHT inserts: " << poht_inserts << '\n';
  std::cout << "I_UPF attribution events: " << cum_upf_events << '\n';
  std::cout << "I_POLL attribution events: " << cum_poll_events << '\n';
  std::cout << "Mean measured prefetch latency: "
            << (lat_count > 0 ? lat_sum / static_cast<double>(lat_count) : 0.0)
            << " cycles over " << lat_count << " samples\n";
  std::cout << "Completed windows: " << completed_phases << '\n';
  std::cout << "Final prefetch degree: " << degree << '\n';
  std::cout << "Cache pf_requested: " << intern_->sim_stats.pf_requested << '\n';
  std::cout << "Cache pf_issued: " << intern_->sim_stats.pf_issued << '\n';
  std::cout << "======================================\n";
}
