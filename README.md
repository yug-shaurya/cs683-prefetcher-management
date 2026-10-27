# Adaptive Runtime Management of Multiple Hardware Prefetchers

CS683 Advanced Computer Architecture course project, IIT Bombay.
Yugratna Shaurya (24b3941).

Baseline paper: Y. Lin et al., "I-POP: Ignite Positive Prefetchers", HPCA 2026.

## What this project is about

I-POP manages several hardware prefetchers at runtime. It computes a
Prefetch Effectiveness (PE) score per prefetcher and uses it to enable,
disable or throttle each one. PE aggregates three things: latency saved by
useful prefetches, latency lost to cache pollution, and delay imposed on
in-flight demand requests.

I-POP recomputes PE on a fixed window of 1K L2 demand accesses. The paper's
own Figure 19(d) shows performance varying with window length from 1K to 8K,
and yet the window stays a fixed constant. This project asks whether adapting
the window helps: shorter when prefetcher behaviour shifts, longer when it is
stable.

## Current status (Checkpoint I)

Done:

- No-prefetch baseline
- ip_stride, next_line and spp_dev evaluated individually at L2
- All three running simultaneously
- IPC, prefetch accuracy, useful/useless counts, DRAM traffic collected
- An adaptive controller that adjusts prefetch degree once per window

Not done yet:

- The PE metric itself
- Prefetch Holding Table / Pollution Holding Table
- Per-prefetcher attribution
- The Control Engine state machine

A note on the controller in `src/`: it throttles on prefetch accuracy against
two fixed thresholds. That is structurally Alecto's Proficiency/Deficiency
Boundary design, which is the scheme I-POP argues against. It is here as a
comparison baseline, not as an implementation of I-POP.

## Findings so far

**A ChampSim configuration bug.** Asking for three prefetchers at L2 generated
eighteen. `config/util.py`'s `chain()` concatenates list values when merging
dictionaries, and a cache gets merged with itself three times during
configuration assembly, so the prefetcher list grows 3 to 6 to 12 to 18.

It fails silently. Duplicate types in `std::tuple<Ps...>` are legal C++ and
ChampSim drives prefetchers with a `std::apply` fold over that tuple, so the
build compiles and runs six independent copies of each prefetcher. No crash,
no warning. Reproduced on a clean upstream clone. Fix is in `patches/`.

Bare string syntax in the JSON is unaffected. A list is affected at any
length, including a single-element list.

**Accuracy does not predict IPC.** On 602.gcc_s the Spearman correlation
between prefetch accuracy and IPC speedup across four configurations is -0.80.
spp_dev is 5.4% accurate and gives 5.03x; next_line is 97.2% accurate and
gives 1.92x. The paper reports accuracy averaging rho = 0.21 across its 76
workloads and failing to correlate positively on 29% of them.

**A fixed window is not uniformly suitable.** At 1024 L2 demand accesses, the
controller completed 0 windows on 400.perlbench, 75 on 602.gcc_s and 153 on
605.mcf_s. One setting, a 153x spread in control decisions. On perlbench the
controller never acted at all.

## Layout

    src/        prefetcher module (ipop.cc, ipop.h)
    configs/    ChampSim configuration JSONs
    patches/    required patch to ChampSim's configuration generator
    results/    per-trace statistics and comparison CSVs
    logs/       raw simulation logs
    docs/       proposal and checkpoint presentation

ChampSim itself is not committed here. `patches/champsim-commit.txt` has the
commit it was built from.

## Reproducing

    git clone https://github.com/ChampSim/ChampSim.git champsim
    cd champsim
    git checkout $(cat ../patches/champsim-commit.txt)
    git apply ../patches/champsim-config-dedupe.patch
    mkdir -p prefetcher/ipop && cp ../src/ipop.* prefetcher/ipop/
    ./config.sh ../configs/champsim_ipop.json
    make -j$(nproc)

Check the generated L2 prefetcher list before trusting a multi-prefetcher run:

    awk '/\.name\("cpu0_L2C"\)/,/lower_translate/' .csconfig/core_inst.cc.inc | grep 'prefetcher<'

It should list each prefetcher exactly once.

Traces are not included. These are the standard SPEC CPU 2017 ChampSim traces.

## Caveats

The numbers here are not comparable with the paper's:

- Baseline is no prefetching, not PC-Stride with throttling, so speedups look
  much larger than the paper's ~10%
- 100K warmup and 1M simulation instructions, against 50M and 200M
- L2 is 512 KB 8-way, against 2 MB 16-way; bimodal branch predictor instead of
  perceptron; DRAM at 3200 MT/s instead of 4800
- Three traces, of which two are usable (400.perlbench has 0.088 L2 MPKI and
  fails the paper's >= 1 LLC MPKI selection criterion)

Known issues not yet resolved:

- The prefetcher module counts roughly 17K more accepted prefetches than the
  cache reports as requested, consistently on both traces. Probably prefetch
  queue duplicate merging, unverified.
- Some controller results came from two different builds and need re-running
  on one binary.

## Next

Per-prefetcher attribution via prefetch metadata, then PfHT and PoHT for the
I_UPF and I_POLL terms, then the Control Engine, then the adaptive window
itself. I_LAT needs MSHR and DRAM-mapping visibility that a prefetcher module
does not have, so it will be approximated and the bias documented.
