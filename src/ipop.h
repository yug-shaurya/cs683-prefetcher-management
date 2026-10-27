#ifndef PREFETCHER_IPOP_H
#define PREFETCHER_IPOP_H

#include <cstdint>

#include "address.h"
#include "modules.h"

struct ipop : public champsim::modules::prefetcher {
  // Tunables
  static constexpr uint64_t PHASE_LENGTH = 1024;
  static constexpr unsigned MIN_DEGREE = 1;
  static constexpr unsigned MAX_DEGREE = 8;

  // Existing adaptation state
  uint64_t phase_accesses = 0;
  uint64_t phase_useful = 0;
  uint64_t phase_issued = 0;
  uint64_t completed_phases = 0;

  // Cumulative statistics for final reporting
  uint64_t total_accesses = 0;
  uint64_t demand_accesses = 0;
  uint64_t useful_prefetches = 0;
  uint64_t prefetch_attempts = 0;
  uint64_t prefetch_accepted = 0;
  unsigned degree = 1;

  using champsim::modules::prefetcher::prefetcher;

  uint32_t prefetcher_cache_operate(champsim::address addr, champsim::address ip, uint8_t cache_hit,
                                    bool useful_prefetch, access_type type, uint32_t metadata_in);
  uint32_t prefetcher_cache_fill(champsim::address addr, long set, long way, uint8_t prefetch,
                                 champsim::address evicted_addr, uint32_t metadata_in);
  void prefetcher_final_stats();
};

#endif
