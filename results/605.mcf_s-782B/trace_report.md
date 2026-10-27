# Trace report: 605.mcf_s-782B

## Experimental setup

- Warmup: 100,000 instructions for the current priority runs.
- Simulation: 1,000,000 instructions for the current priority runs.
- Verify each raw log for its actual settings before final reporting.

## Performance comparison

| Configuration | Status | IPC | Cycles | IPC speedup | Cycle reduction | Useful PF | Useless PF |
|---|---|---:|---:|---:|---:|---:|---:|
| Baseline | Metrics extracted | 0.07123 | 14040010 | 1.0 | 0.0% | 0 | 0 |
| A: IP-stride | Metrics extracted | 0.1098 | 9105637 | 1.5415 | 35.15% | 41800 | 257 |
| B: Next-line | Metrics extracted | 0.09867 | 10134742 | 1.3852 | 27.82% | 42154 | 78062 |
| C: SPP-dev | Metrics extracted | 0.1057 | 9457558 | 1.4839 | 32.64% | 16523 | 974 |
| I-POP prototype | Metrics extracted | 0.1036 | 9657121 | 1.4544 | 31.22% | 51730 | 144840 |
| A+B | Combination not yet validated/run |  |  |  | % |  |  |
| A+C | Combination not yet validated/run |  |  |  | % |  |  |
| B+C | Combination not yet validated/run |  |  |  | % |  |  |
| A+B+C | Combination not yet validated/run |  |  |  | % |  |  |

## Raw log references

- **Baseline**: `logs/baseline/Baseline__SPEC2017_605.mcf_s-782B__Simulation_Log.txt`
- **A: IP-stride**: `logs/ip_stride/ip_stride__SPEC2017_605.mcf_s-782B__Simulation_Log.txt`
- **B: Next-line**: `logs/next_line/next_line__SPEC2017_605.mcf_s-782B__Simulation_Log.txt`
- **C: SPP-dev**: `logs/spp_dev/spp_dev__SPEC2017_605.mcf_s-782B__Simulation_Log.txt`
- **I-POP prototype**: `logs/I_POP_Adaptive_Controller__SPEC2017_605.mcf_s-782B__Simulation_Log.txt`

## Interpretation

Interpret results only after checking that the configuration, simulation length, and parsed metrics are valid. Combination rows will be populated after their runs complete. The I-POP entry represents the current prototype, not a verified faithful implementation of the full paper.
