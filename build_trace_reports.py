from pathlib import Path
import csv
import re

ROOT = Path.cwd()
LOGS = ROOT / "logs"
RESULTS = ROOT / "results"

TRACES = {
    "400.perlbench-41B": "400.perlbench-41B",
    "602.gcc_s-2226B": "602.gcc_s-2226B",
    "605.mcf_s-782B": "605.mcf_s-782B",
    "619.lbm_s-2676B": "619.lbm_s-2676B",
    "657.xz_s-2302B": "657.xz_s-2302B",
}

CONFIGS = {
    "baseline": "Baseline",
    "ip_stride": "A: IP-stride",
    "next_line": "B: Next-line",
    "spp_dev": "C: SPP-dev",
    "ipop": "I-POP prototype",
}

def identify_trace(path):
    name = path.name.lower()
    parent = str(path.parent).lower()

    for key in TRACES:
        if key.lower() in name or key.lower() in parent:
            return key

    # Perlbench uses a shorter filename in some older logs.
    if "perlbench" in name or "perlbench" in parent:
        return "400.perlbench-41B"

    return None

def identify_config(path):
    name = path.name.lower()
    parent = str(path.parent).lower()

    if "i_pop" in name or "ipop" in name or "i_pop" in parent:
        return "ipop"
    if "baseline" in name or "/baseline/" in parent:
        return "baseline"
    if "ip_stride" in name or "/ip_stride/" in parent:
        return "ip_stride"
    if "next_line" in name or "/next_line/" in parent:
        return "next_line"
    if "spp_dev" in name or "/spp_dev/" in parent:
        return "spp_dev"

    return None

def extract(path):
    text = path.read_text(errors="replace")

    ipc_matches = re.findall(
        r"CPU 0 cumulative IPC:\s*([\d.]+)"
        r"\s+instructions:\s*(\d+)\s+cycles:\s*(\d+)", text
    )
    pf_matches = re.findall(
        r"cpu0->cpu0_L2C PREFETCH REQUESTED:\s*(\d+)"
        r"\s+ISSUED:\s*(\d+)\s+USEFUL:\s*(\d+)"
        r"\s+USELESS:\s*(\d+)", text
    )

    ipc, instructions, cycles = (
        ipc_matches[-1] if ipc_matches else ("", "", "")
    )
    requested, issued, useful, useless = (
        pf_matches[-1] if pf_matches else ("", "", "", "")
    )

    return {
        "ipc": float(ipc) if ipc else None,
        "instructions": instructions,
        "cycles": int(cycles) if cycles else None,
        "prefetch_requested": requested,
        "prefetch_issued": issued,
        "prefetch_useful": useful,
        "prefetch_useless": useless,
        "log_file": str(path.relative_to(ROOT)),
    }

# Find simulation logs; ignore summaries and configuration-debug logs.
log_files = [
    p for p in LOGS.rglob("*")
    if p.is_file()
    and (
        p.name.endswith(".log")
        or p.name.endswith("Simulation_Log.txt")
    )
    and "config_abc_verbose" not in p.name
]

data = {}
for path in log_files:
    trace = identify_trace(path)
    config = identify_config(path)
    if not trace or not config:
        continue

    row = extract(path)
    row["trace"] = trace
    row["configuration"] = config

    # Prefer a detailed Simulation_Log over an older duplicate log.
    key = (trace, config)
    previous = data.get(key)
    if previous is None or (
        path.name.endswith("Simulation_Log.txt")
        and not previous["log_file"].endswith("Simulation_Log.txt")
    ):
        data[key] = row

all_rows = []

for trace in TRACES:
    out_dir = RESULTS / trace
    out_dir.mkdir(parents=True, exist_ok=True)

    rows = []
    baseline = data.get((trace, "baseline"))
    baseline_ipc = baseline["ipc"] if baseline else None
    baseline_cycles = baseline["cycles"] if baseline else None

    for config, label in CONFIGS.items():
        row = data.get((trace, config))

        if row is None:
            rows.append({
                "configuration": label,
                "status": "Not yet run / matching log not found",
                "ipc": "",
                "cycles": "",
                "ipc_speedup_vs_baseline": "",
                "cycle_reduction_vs_baseline_pct": "",
                "prefetch_requested": "",
                "prefetch_issued": "",
                "prefetch_useful": "",
                "prefetch_useless": "",
                "raw_log": "",
            })
            continue

        ipc = row["ipc"]
        cycles = row["cycles"]

        speedup = (
            ipc / baseline_ipc
            if ipc is not None and baseline_ipc
            else None
        )
        cycle_reduction = (
            100 * (baseline_cycles - cycles) / baseline_cycles
            if cycles is not None and baseline_cycles
            else None
        )

        entry = {
            "configuration": label,
            "status": "Metrics extracted" if ipc is not None else
                      "Log found; expected metrics not parsed",
            "ipc": ipc if ipc is not None else "",
            "cycles": cycles if cycles is not None else "",
            "ipc_speedup_vs_baseline": round(speedup, 4)
                if speedup is not None else "",
            "cycle_reduction_vs_baseline_pct": round(cycle_reduction, 2)
                if cycle_reduction is not None else "",
            "prefetch_requested": row["prefetch_requested"],
            "prefetch_issued": row["prefetch_issued"],
            "prefetch_useful": row["prefetch_useful"],
            "prefetch_useless": row["prefetch_useless"],
            "raw_log": row["log_file"],
        }
        rows.append(entry)

        master_entry = dict(entry)
        master_entry["trace"] = trace
        all_rows.append(master_entry)

    # Future combination slots; no results are fabricated.
    for label in ["A+B", "A+C", "B+C", "A+B+C"]:
        rows.append({
            "configuration": label,
            "status": "Combination not yet validated/run",
            "ipc": "",
            "cycles": "",
            "ipc_speedup_vs_baseline": "",
            "cycle_reduction_vs_baseline_pct": "",
            "prefetch_requested": "",
            "prefetch_issued": "",
            "prefetch_useful": "",
            "prefetch_useless": "",
            "raw_log": "",
        })

    fields = [
        "configuration", "status", "ipc", "cycles",
        "ipc_speedup_vs_baseline", "cycle_reduction_vs_baseline_pct",
        "prefetch_requested", "prefetch_issued",
        "prefetch_useful", "prefetch_useless", "raw_log",
    ]

    csv_path = out_dir / "trace_comparison.csv"
    with csv_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    md_path = out_dir / "trace_report.md"
    with md_path.open("w") as f:
        f.write(f"# Trace report: {trace}\n\n")
        f.write("## Experimental setup\n\n")
        f.write("- Warmup: 100,000 instructions for the current priority runs.\n")
        f.write("- Simulation: 1,000,000 instructions for the current priority runs.\n")
        f.write("- Verify each raw log for its actual settings before final reporting.\n\n")
        f.write("## Performance comparison\n\n")
        f.write("| Configuration | Status | IPC | Cycles | IPC speedup | Cycle reduction | Useful PF | Useless PF |\n")
        f.write("|---|---|---:|---:|---:|---:|---:|---:|\n")

        for r in rows:
            f.write(
                f"| {r['configuration']} | {r['status']} "
                f"| {r['ipc']} | {r['cycles']} "
                f"| {r['ipc_speedup_vs_baseline']} "
                f"| {r['cycle_reduction_vs_baseline_pct']}% "
                f"| {r['prefetch_useful']} | {r['prefetch_useless']} |\n"
            )

        f.write("\n## Raw log references\n\n")
        for r in rows:
            if r["raw_log"]:
                f.write(f"- **{r['configuration']}**: `{r['raw_log']}`\n")

        f.write("\n## Interpretation\n\n")
        f.write(
            "Interpret results only after checking that the configuration, "
            "simulation length, and parsed metrics are valid. "
            "Combination rows will be populated after their runs complete. "
            "The I-POP entry represents the current prototype, not a verified "
            "faithful implementation of the full paper.\n"
        )

    print(f"{trace}: wrote {csv_path.relative_to(ROOT)}")
    print(f"  Report: {md_path.relative_to(ROOT)}")

# Master CSV for configurations whose logs were found.
master_path = RESULTS / "comparison" / "master_comparison.csv"
master_path.parent.mkdir(parents=True, exist_ok=True)

master_fields = [
    "trace", "configuration", "status", "ipc", "cycles",
    "ipc_speedup_vs_baseline", "cycle_reduction_vs_baseline_pct",
    "prefetch_requested", "prefetch_issued",
    "prefetch_useful", "prefetch_useless", "raw_log",
]
with master_path.open("w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=master_fields)
    writer.writeheader()
    writer.writerows(all_rows)

print(f"\nMaster comparison: {master_path.relative_to(ROOT)}")
print("\nExisting results were preserved; no simulations were run.")
print("Check every report for missing or unparsed metrics.")
