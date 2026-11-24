#ifndef PREFETCHER_IPOP_H
#define PREFETCHER_IPOP_H

#include <cstdint>
#include <cstddef>
#include <deque>
#include <fstream>
#include <string>
#include <unordered_map>

#include "address.h"
#include "modules.h"

struct ipop : public champsim::modules::prefetcher {
  static constexpr unsigned MIN_DEGREE = 1;
  static constexpr unsigned MAX_DEGREE = 8;
  static constexpr std::size_t PFHT_MAX = 512;
  static constexpr std::size_t POHT_MAX = 8192;

  // Tunables (set from environment in prefetcher_initialize)
  uint64_t window_len = 1024;
  uint64_t window_min = 256;
  uint64_t window_max = 8192;
  double thr_up = 0.25;
  double thr_down = 0.05;
  double pe_up = 0.5;
  double pe_down = -0.5;
  bool adaptive = false;
  int policy = 0;
  double alpha = 1.0;
  double lat_k = 166.7;
  double delta_hi = 0.10;
  double delta_lo = 0.02;
  std::string log_path;

  // Per-window state
  uint64_t phase_accesses = 0;
  uint64_t phase_useful = 0;
  uint64_t phase_issued = 0;
  uint64_t phase_pq_full = 0;
  uint64_t completed_phases = 0;
  uint64_t window_index = 0;

  // PE accumulators, reset every window
  double win_upf = 0.0;
  double win_poll = 0.0;
  double win_lat = 0.0;
  double lat_sum = 0.0;
  uint64_t lat_count = 0;

  // Adaptive-window state
  double prev_signal = 0.0;
  bool have_prev = false;

  // Cumulative statistics
  uint64_t total_accesses = 0;
  uint64_t demand_accesses = 0;
  uint64_t useful_prefetches = 0;
  uint64_t prefetch_attempts = 0;
  uint64_t prefetch_accepted = 0;
  uint64_t pq_full_events = 0;
  uint64_t poht_inserts = 0;
  uint64_t cum_upf_events = 0;
  uint64_t cum_poll_events = 0;
  unsigned degree = 1;

  // PfHT: prefetches in flight or resident, keyed by block number
  struct pfht_entry {
    uint64_t issue_time;
    uint64_t fill_time;
    bool filled;
  };
  std::unordered_map<uint64_t, pfht_entry> pfht;
  std::deque<uint64_t> pfht_fifo;

  // PoHT: lines evicted by our prefetches, keyed by block number
  std::unordered_map<uint64_t, uint64_t> poht;
  std::deque<uint64_t> poht_fifo;

  std::ofstream wlog;

  using champsim::modules::prefetcher::prefetcher;

  uint64_t now_cycles() const;

  void prefetcher_initialize();
  uint32_t prefetcher_cache_operate(champsim::address addr, champsim::address ip, uint8_t cache_hit,
                                    bool useful_prefetch, access_type type, uint32_t metadata_in);
  uint32_t prefetcher_cache_fill(champsim::address addr, long set, long way, uint8_t prefetch,
                                 champsim::address evicted_addr, uint32_t metadata_in);
  void prefetcher_final_stats();
};

#endif
