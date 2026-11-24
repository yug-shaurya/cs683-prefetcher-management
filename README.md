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

I-POP recomputes PE on a fixed window of 1K L2 demand accesses. Figure 19(d)
sweeps that phase length from 1K to 8K and reports I-POP as insensitive to it;
Bandit is the scheme that degrades as the phase lengthens, because of its
adjustment lag. The paper fixes the window at 1K on that basis.

This project asks two things. Does that insensitivity hold on a different
configuration? And does adapting the window help anyway - shorter when
prefetcher behaviour shifts, longer when it is stable - given that the paper
itself notes shorter phases reduce lag but cost overhead?

## Current status (Checkpoint II)

Implemented:

- PE metric, all three terms in cycles. I_UPF from measured per-prefetch
  latencies, I_POLL from recorded evictions, I_LAT from MSHR occupancy
- Prefetch Holding Table (512 entries), Pollution Holding Table (8192 entries)
- Fixed-window PE controller and adaptive control window
- Every tunable read from the environment at module initialisation, so one
  binary produces all twelve experimental arms and each run echoes its own
  settings into its log

Not implemented:

- Per-prefetcher attribution. PE is aggregate over all L2 prefetches, so the
  controller throttles one global degree rather than enabling or disabling
  individual prefetchers
- Control Engine state machine (ON / WA / OFF)

The accuracy-threshold controller from Checkpoint I is retained as a
comparison arm. It is structurally Alecto's Proficiency/Deficiency Boundary
design, which is the scheme I-POP argues against, and it is here as a
baseline rather than as an implementation of I-POP.

## Methodology

10M warmup and 50M simulation instructions, against Checkpoint I's 100K and
1M. Baselined against `ip_stride`, which is an IP-indexed stride prefetcher
and stands in for the paper's PC-Stride reference; its throttling is not
replicated. Four SPEC CPU2017 traces spanning 3.6 to 133 L2 MPKI.

54 runs in `results_ckpt2/`, summarised in `results_ckpt2/summary.csv`.
Per-window controller traces in `results_ckpt2/windows/`.

## Findings

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

**Accuracy anti-predicts IPC.** On 602.gcc_s the Spearman correlation between
prefetch accuracy and speedup over ip_stride, across six configurations, is
-1.00: a perfect inversion at every step. `next_line` is 97.0% accurate and is
the worst configuration on the trace at 0.76x; `spp_dev` is 5.3% accurate and
is the best at 2.15x. On 619.lbm_s rho is -0.79. On 605.mcf_s and 657.xz_s it
is approximately zero, and those are the two traces where prefetching changes
little either way. The paper reports accuracy averaging rho = 0.21 across its
76 workloads and failing to correlate positively on 29% of them.

**The paper's phase-length robustness replicates here.** Sweeping the fixed
window from 1K to 8K gives 0.91 / 0.90 / 0.90 / 0.90 on 605.mcf_s, 1.01 flat
on 619.lbm_s and 0.97 flat on 657.xz_s. On 602.gcc_s it is flat from 1K to 4K
at 1.53-1.54 and drops to 1.44 at 8K. So I-POP's reported insensitivity to
phase length holds on a smaller L2, a weaker branch predictor and slower DRAM
than the paper's configuration. This was not the expected result and it is
reported as a reproduction.

**The adaptive window works as a mechanism but does not help.** Given a
256-8192 range under one policy, it spends 85% of its windows at the 8192
maximum on 602.gcc_s and 82-99% at the 256 minimum on the other three.
Lowering the floor to 64 confirmed it was binding: gcc still parks at the
maximum, the other three go straight to 64, widening the spread to 128x. So
the mechanism does respond to real differences between workloads.

It does not convert into performance: 1.56 against 1.53 on gcc, within noise,
and 0.84 against 0.91 on mcf. That follows from the finding above - window
length is not a lever that moves performance much on this configuration.
Dropping the floor to 64 made mcf worse still, 0.76, with L2 traffic rising
from 413 to 576 MPKI.

**My I_LAT deviates from the paper and suppresses PE on streaming
workloads.** On 619.lbm_s the PE controller never moved off degree 1 across
605 windows. Lowering the up-threshold from 20 to 2 produced a numerically
identical run, so this is not threshold calibration. The per-window means show
why: I_LAT averages 251,830 cycles against I_UPF's 88,583, a ratio of 2.84, so
PE is roughly -163,000 in every window. On 602.gcc_s the same ratio is 0.05
and PE is comfortably positive.

Comparing against Section III-D and Table III of the paper, my implementation
differs in three ways, all of which inflate I_LAT:

| | Paper | This implementation |
|---|---|---|
| When measured | at data return, only if demand requests remain in the MSHR | at prefetch issue |
| Per prefetch | `N_Delay += 1`; where several demands are affected, only the maximum induced delay is accumulated | `n_inflight x k` |
| Single-core | `T_NoC = 0`, so only the DRAM bus and bank terms contribute | `k` charged regardless |

The overcounting is worst exactly where the MSHR is busiest, which is why a
streaming workload is the case that breaks. lbm's prefetches are 56.1%
accurate, the highest figure in this study, and the metric calls them harmful.

The other two terms are faithful: Equations 2 and 3 compute I_UPF and I_POLL
from average LLC and DRAM latencies, which is what this implementation does.

**Management loses to not managing.** On all four traces the best
configuration is a single prefetcher or the three running unmanaged. The best
managed arm costs between 2% and 27% of the available speedup and never
recovers it. On 602.gcc_s the controller cuts prefetch traffic from 847 to
roughly 270 MPKI and raises accuracy from 7.4% to 26%, losing more than a
quarter of the speedup doing so: where bandwidth is not the binding
constraint, coverage is worth more than precision.

**I_POLL is approximately zero on this configuration.** 29,047 evictions by
prefetch fills were recorded and one subsequent demand miss was attributed to
them, unchanged at 8x table capacity. This L2 takes 3,501,609 LOAD misses
against 1,733 hits on gcc after 10M warmup, a 0.05% hit rate, so there is
almost no reuse for a prefetch to displace. The paper's 2 MB 16-way L2 would
expose pollution that a 512 KB 8-way cache structurally cannot.

## Resolved from Checkpoint I

The ~17K discrepancy between module-counted and cache-reported prefetches was
hypothesised as prefetch-queue duplicate merging. That was wrong.
`CACHE::begin_phase()` constructs fresh `sim_stats` and `roi_stats` at every
phase transition, so the cache's counters cover the simulation phase only
while the module's spanned warmup plus simulation. With
`--warmup-instructions 0` the two agree exactly (13,874 each); with 200K
warmup the gap is the warmup phase's prefetches. Every run now reports both
counter sets.

## Layout

    src/            prefetcher module (ipop.cc, ipop.h)
    configs/        ChampSim configuration JSONs
    patches/        required patch to ChampSim's configuration generator
    results/        Checkpoint I statistics (100K/1M, superseded)
    results_ckpt2/  Checkpoint II statistics (10M/50M)
    logs/           raw simulation logs
    docs/           proposal and checkpoint presentations
    collect.py      builds results_ckpt2/summary.csv from the run JSONs
    figures.py      plots and Spearman correlations
    run_*.sh        experiment queues

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

Experimental arms are selected entirely by environment variable, so one binary
covers the whole matrix:

    IPOP_POLICY     accuracy | pe
    IPOP_ADAPTIVE   0 | 1
    IPOP_WINDOW     initial or fixed window length
    IPOP_WMIN       adaptive floor (default 256)
    IPOP_WMAX       adaptive ceiling (default 8192)
    IPOP_PE_UP      PE threshold to raise degree
    IPOP_PE_DOWN    PE threshold to lower degree
    IPOP_ALPHA      I_LAT weight in PE
    IPOP_K          cycles charged per in-flight demand (default 27.9)
    IPOP_DELTA_HI   window shortens above this signal delta
    IPOP_DELTA_LO   window lengthens below this signal delta
    IPOP_LOG        path for the per-window CSV trace

Traces are not included. These are the standard SPEC CPU 2017 ChampSim traces.

## Caveats

The numbers here are not directly comparable with the paper's:

- L2 is 512 KB 8-way against 2 MB 16-way; bimodal branch predictor instead of
  perceptron; DRAM at 3200 MT/s instead of 4800
- 10M warmup and 50M simulation against 50M and 200M
- Four traces against 76. No geometric means are reported, and differences
  under roughly 2% are inside the noise floor at this run length and are not
  claimed
- ip_stride stands in for PC-Stride but does not replicate its throttling

Known limitations:

- PE is aggregate, not per-prefetcher, so the controller cannot do what
  I-POP's Control Engine does
- I_LAT does not match Section III-D (see Findings); it is measured at issue
  rather than at data return, sums rather than maxes across affected demands,
  and ignores that `T_NoC` is zero in single-core. Sensitivity to alpha and k
  has not been swept
- The adaptive-window thresholds were set from observed signal ranges rather
  than swept

## Next

Fix I_LAT to match Section III-D: measure at data return rather than at
issue, accumulate the maximum induced delay rather than the sum, and drop the
interconnect term in single-core. Until that is corrected, PE is suppressed on
streaming workloads regardless of how useful the prefetches are, so nothing
downstream of it can be trusted on those traces.

Then per-prefetcher attribution via prefetch metadata and the Control Engine
state machine, which together are the difference between throttling one global
degree and managing prefetchers individually.
