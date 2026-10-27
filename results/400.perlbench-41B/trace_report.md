# Trace report: 400.perlbench-41B

## Experimental setup

- Warmup: 100,000 instructions for the current priority runs.
- Simulation: 1,000,000 instructions for the current priority runs.
- Verify each raw log for its actual settings before final reporting.

## Performance comparison

| Configuration | Status | IPC | Cycles | IPC speedup | Cycle reduction | Useful PF | Useless PF |
|---|---|---:|---:|---:|---:|---:|---:|
| Baseline | Metrics extracted | 1.422 | 703385 | 1.0 | 0.0% | 0 | 0 |
| A: IP-stride | Metrics extracted | 1.422 | 703385 | 1.0 | 0.0% | 0 | 0 |
| B: Next-line | Metrics extracted | 1.425 | 701862 | 1.0021 | 0.22% | 8 | 0 |
| C: SPP-dev | Metrics extracted | 1.422 | 703008 | 1.0 | 0.05% | 0 | 0 |
| I-POP prototype | Metrics extracted | 1.425 | 701862 | 1.0021 | 0.22% | 8 | 0 |
| A+B | Combination not yet validated/run |  |  |  | % |  |  |
| A+C | Combination not yet validated/run |  |  |  | % |  |  |
| B+C | Combination not yet validated/run |  |  |  | % |  |  |
| A+B+C | Combination not yet validated/run |  |  |  | % |  |  |

## Raw log references

- **Baseline**: `logs/baseline_perlbench.log`
- **A: IP-stride**: `logs/ip_stride_perlbench.log`
- **B: Next-line**: `logs/next_line_perlbench.log`
- **C: SPP-dev**: `logs/spp_dev_perlbench.log`
- **I-POP prototype**: `logs/I_POP_Adaptive_Controller__SPEC2017_400_perlbench__Simulation_Log.txt`

## Interpretation

Interpret results only after checking that the configuration, simulation length, and parsed metrics are valid. Combination rows will be populated after their runs complete. The I-POP entry represents the current prototype, not a verified faithful implementation of the full paper.
