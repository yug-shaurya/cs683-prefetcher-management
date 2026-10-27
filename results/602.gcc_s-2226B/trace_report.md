# Trace report: 602.gcc_s-2226B

## Experimental setup

- Warmup: 100,000 instructions for the current priority runs.
- Simulation: 1,000,000 instructions for the current priority runs.
- Verify each raw log for its actual settings before final reporting.

## Performance comparison

| Configuration | Status | IPC | Cycles | IPC speedup | Cycle reduction | Useful PF | Useless PF |
|---|---|---:|---:|---:|---:|---:|---:|
| Baseline | Metrics extracted | 0.0774 | 12919804 | 1.0 | 0.0% | 0 | 0 |
| A: IP-stride | Metrics extracted | 0.1847 | 5412802 | 2.3863 | 58.1% | 57334 | 210 |
| B: Next-line | Metrics extracted | 0.1486 | 6731385 | 1.9199 | 47.9% | 68271 | 1342 |
| C: SPP-dev | Metrics extracted | 0.3896 | 2566649 | 5.0336 | 80.13% | 49439 | 89 |
| I-POP prototype | Metrics extracted | 0.198 | 5051262 | 2.5581 | 60.9% | 68711 | 2836 |
| A+B | Combination not yet validated/run |  |  |  | % |  |  |
| A+C | Combination not yet validated/run |  |  |  | % |  |  |
| B+C | Combination not yet validated/run |  |  |  | % |  |  |
| A+B+C | Combination not yet validated/run |  |  |  | % |  |  |

## Raw log references

- **Baseline**: `logs/baseline/Baseline__SPEC2017_602.gcc_s-2226B__Simulation_Log.txt`
- **A: IP-stride**: `logs/ip_stride/ip_stride__SPEC2017_602.gcc_s-2226B__Simulation_Log.txt`
- **B: Next-line**: `logs/next_line/next_line__SPEC2017_602.gcc_s-2226B__Simulation_Log.txt`
- **C: SPP-dev**: `logs/spp_dev/spp_dev__SPEC2017_602.gcc_s-2226B__Simulation_Log.txt`
- **I-POP prototype**: `logs/I_POP_Adaptive_Controller__SPEC2017_602.gcc_s-2226B__Simulation_Log.txt`

## Interpretation

Interpret results only after checking that the configuration, simulation length, and parsed metrics are valid. Combination rows will be populated after their runs complete. The I-POP entry represents the current prototype, not a verified faithful implementation of the full paper.
