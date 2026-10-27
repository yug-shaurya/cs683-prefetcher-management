#include "ipop.h"

#include <algorithm>
#include <iostream>

#include "cache.h"

uint32_t ipop::prefetcher_cache_operate(
    champsim::address addr,
    champsim::address ip,
    uint8_t cache_hit,
    bool useful_prefetch,
    access_type type,
    uint32_t metadata_in)
{
  ++total_accesses;

  const bool is_demand =
      type == access_type::LOAD || type == access_type::RFO;

  if (is_demand)
    ++demand_accesses;

  if (useful_prefetch)
    ++useful_prefetches;

  if (is_demand)
    ++phase_accesses;

  if (phase_accesses >= PHASE_LENGTH) {
    const double usefulness =
        phase_issued == 0
            ? 0.0
            : static_cast<double>(phase_useful) /
                  static_cast<double>(phase_issued);

    if (usefulness >= 0.25)
      degree = std::min(MAX_DEGREE, degree + 1);
    else if (usefulness < 0.05)
      degree = std::max(MIN_DEGREE, degree - 1);

    ++completed_phases;
    phase_accesses = 0;
    phase_useful = 0;
    phase_issued = 0;
  }

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
  return metadata_in;
}

void ipop::prefetcher_final_stats()
{
  std::cout << "\n===== IPOP Prefetcher Statistics =====\n";
  std::cout << "Total callback accesses: " << total_accesses << '\n';
  std::cout << "Demand accesses (LOAD + RFO): " << demand_accesses << '\n';
  std::cout << "Useful-prefetch observations: " << useful_prefetches << '\n';
  std::cout << "Prefetch attempts: " << prefetch_attempts << '\n';
  std::cout << "Prefetch requests accepted: " << prefetch_accepted << '\n';
  std::cout << "Completed phases: " << completed_phases << '\n';
  std::cout << "Final prefetch degree: " << degree << '\n';
  std::cout << "======================================\n";
}
