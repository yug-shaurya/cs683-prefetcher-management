# I-POP Adaptive Prototype Analysis: 602.gcc_s-2226B

## 1. Experimental setup

- Simulator: ChampSim
- Prefetcher: I-POP adaptive prototype
- Trace: `../traces/602.gcc_s-2226B.champsimtrace.xz`
- Warmup instructions: 100000
- Simulation instruction limit: 1000000
- Completion marker: SUCCESS
- Raw log: `logs/I_POP_Adaptive_Controller__SPEC2017_602.gcc_s-2226B__Simulation_Log.txt`

## 2. Performance

| Metric | Measured result |
|---|---:|
| Instructions reported in ROI | 1000000 |
| IPC | 0.198 |
| Cycles | 5051262 |
| Average L2/LLC miss latency (cycles) | 69.65 |

## 3. Prefetch statistics

| Metric | Measured result |
|---|---:|
| Requested | 144587 |
| Issued | 144545 |
| Useful | 68711 |
| Useless | 2836 |
| Counter source | L2C |

These counters are copied from the matching prefetch-statistics line in the raw log. Check the counter source before comparing values across experiments.

## 4. Interpretation and limitations

IPC is instructions completed per cycle; higher IPC generally indicates better throughput under the same simulation setup. Prefetch counts alone do not establish performance improvement: useful prefetches, useless prefetches, memory traffic, latency, and IPC should be considered together.

This is an adaptive prototype, not evidence of a complete reproduction of the I-POP paper. The report does not infer controller states, phase-by-phase decisions, or paper-specific internal metrics unless they are explicitly recorded in the raw log.

## 5. Reproducibility

Use the raw log listed above as the source of truth. Confirm that the baseline and comparison configurations use the same trace, warmup length, simulation length, and ChampSim settings before drawing performance conclusions.
