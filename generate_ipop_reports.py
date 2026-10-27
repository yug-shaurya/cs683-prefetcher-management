from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent
LOG_DIR = ROOT / "logs"
RESULTS_DIR = ROOT / "results"

traces = {
    "400.perlbench-41B": "400_perlbench",
    "602.gcc_s-2226B": "602.gcc_s-2226B",
    "605.mcf_s-782B": "605.mcf_s-782B",
    "619.lbm_s-2676B": "619.lbm_s-2676B",
    "657.xz_s-2302B": "657.xz_s-2302B",
}

def extract(pattern, text, default="Not found"):
    match = re.search(pattern, text, re.IGNORECASE)
    return match.group(1).strip() if match else default

def parse_log(path):
    text = path.read_text(errors="replace")

    metrics = {
        "instructions": extract(
            r"CPU 0 cumulative IPC:\s*[\d.]+\s+instructions:\s*(\d+)", text
        ),
        "IPC": extract(r"CPU 0 cumulative IPC:\s*([\d.]+)", text),
        "cycles": extract(
            r"CPU 0 cumulative IPC:\s*[\d.]+\s+instructions:\s*\d+\s+cycles:\s*(\d+)",
            text,
        ),
        "warmup": extract(r"Warmup Instructions:\s*(\d+)", text),
        "simulation_length": extract(r"Simulation Instructions:\s*(\d+)", text),
    }

    # Prefer L2C statistics; fall back to LLC if the log uses that label.
    prefetch_line = None
    for line in text.splitlines():
        if "PREFETCH REQUESTED:" in line and (
            "cpu0->cpu0_L2C" in line or "cpu0->LLC" in line
        ):
            prefetch_line = line
            if "cpu0->cpu0_L2C" in line:
                break

    if prefetch_line:
        for name in ("requested", "issued", "useful", "useless"):
            match = re.search(
                rf"{name.upper()}:\s*(\d+)", prefetch_line, re.IGNORECASE
            )
            metrics[name] = match.group(1) if match else "Not found"
        metrics["prefetch_counter_source"] = (
            "L2C" if "cpu0->cpu0_L2C" in prefetch_line else "LLC"
        )
    else:
        for name in ("requested", "issued", "useful", "useless"):
            metrics[name] = "Not found"
        metrics["prefetch_counter_source"] = "Not found"

    metrics["average_l2_miss_latency"] = extract(
        r"cpu0->cpu0_L2C AVERAGE MISS LATENCY:\s*([\d.]+)", text
    )
    if metrics["average_l2_miss_latency"] == "Not found":
        metrics["average_l2_miss_latency"] = extract(
            r"cpu0->LLC AVERAGE MISS LATENCY:\s*([\d.]+)", text
        )

    metrics["trace"] = extract(r"CPU 0 runs\s+(.+)", text)
    metrics["completed"] = "SUCCESS" if "ChampSim completed all CPUs" in text else "Check log"
    return metrics

def fmt(value, unit=""):
    return f"{value}{unit}" if value != "Not found" else value

created = 0

for trace_dir, benchmark in traces.items():
    candidates = [
        LOG_DIR / f"I_POP_Adaptive_Controller__SPEC2017_{benchmark}__Simulation_Log.txt",
        LOG_DIR / f"I_POP_Adaptive_Controller__SPEC2017_{trace_dir.replace('-', '_')}__Simulation_Log.txt",
    ]

    # Perlbench's historical log name differs from the other traces.
    if trace_dir.startswith("400."):
        candidates.insert(
            0, LOG_DIR / "I_POP_Adaptive_Controller__SPEC2017_400_perlbench__Simulation_Log.txt"
        )

    log_path = next((p for p in candidates if p.exists()), None)
    if log_path is None:
        print(f"SKIP: No I-POP simulation log found for {trace_dir}")
        continue

    m = parse_log(log_path)
    out_dir = RESULTS_DIR / trace_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    report = out_dir / "ipop_analysis.md"

    report.write_text(f"""# I-POP Adaptive Prototype Analysis: {trace_dir}

## 1. Experimental setup

- Simulator: ChampSim
- Prefetcher: I-POP adaptive prototype
- Trace: `{m['trace']}`
- Warmup instructions: {m['warmup']}
- Simulation instruction limit: {m['simulation_length']}
- Completion marker: {m['completed']}
- Raw log: `{log_path.relative_to(ROOT)}`

## 2. Performance

| Metric | Measured result |
|---|---:|
| Instructions reported in ROI | {m['instructions']} |
| IPC | {m['IPC']} |
| Cycles | {m['cycles']} |
| Average L2/LLC miss latency (cycles) | {m['average_l2_miss_latency']} |

## 3. Prefetch statistics

| Metric | Measured result |
|---|---:|
| Requested | {m['requested']} |
| Issued | {m['issued']} |
| Useful | {m['useful']} |
| Useless | {m['useless']} |
| Counter source | {m['prefetch_counter_source']} |

These counters are copied from the matching prefetch-statistics line in the raw log. Check the counter source before comparing values across experiments.

## 4. Interpretation and limitations

IPC is instructions completed per cycle; higher IPC generally indicates better throughput under the same simulation setup. Prefetch counts alone do not establish performance improvement: useful prefetches, useless prefetches, memory traffic, latency, and IPC should be considered together.

This is an adaptive prototype, not evidence of a complete reproduction of the I-POP paper. The report does not infer controller states, phase-by-phase decisions, or paper-specific internal metrics unless they are explicitly recorded in the raw log.

## 5. Reproducibility

Use the raw log listed above as the source of truth. Confirm that the baseline and comparison configurations use the same trace, warmup length, simulation length, and ChampSim settings before drawing performance conclusions.
""")

    created += 1
    print(f"Created: {report.relative_to(ROOT)}")

print(f"\nFinished. Reports created: {created}/{len(traces)}")
print("Existing CSV files and raw simulation logs were not modified.")
