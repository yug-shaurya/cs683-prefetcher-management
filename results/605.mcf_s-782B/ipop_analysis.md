# I-POP Adaptive Prototype Analysis: 605.mcf_s-782B

## 1. Experimental setup

- Simulator: ChampSim
- Prefetcher: I-POP adaptive prototype
- Trace: `../traces/605.mcf_s-782B.champsimtrace.xz`
- Warmup instructions: 100000
- Simulation instruction limit: 1000000
- Completion marker: SUCCESS
- Raw log: `logs/I_POP_Adaptive_Controller__SPEC2017_605.mcf_s-782B__Simulation_Log.txt`

## 2. Performance

| Metric | Measured result |
|---|---:|
| Instructions reported in ROI | 1000002 |
| IPC | 0.1036 |
| Cycles | 9657121 |
| Average L2/LLC miss latency (cycles) | 102.2 |

## 3. Prefetch statistics

| Metric | Measured result |
|---|---:|
| Requested | 268995 |
| Issued | 268995 |
| Useful | 51730 |
| Useless | 144840 |
| Counter source | L2C |

These counters are copied from the matching prefetch-statistics line in the raw log. Check the counter source before comparing values across experiments.

## 4. Interpretation and limitations

IPC is instructions completed per cycle; higher IPC generally indicates better throughput under the same simulation setup. Prefetch counts alone do not establish performance improvement: useful prefetches, useless prefetches, memory traffic, latency, and IPC should be considered together.

This is an adaptive prototype, not evidence of a complete reproduction of the I-POP paper. The report does not infer controller states, phase-by-phase decisions, or paper-specific internal metrics unless they are explicitly recorded in the raw log.

## 5. Reproducibility

Use the raw log listed above as the source of truth. Confirm that the baseline and comparison configurations use the same trace, warmup length, simulation length, and ChampSim settings before drawing performance conclusions.
