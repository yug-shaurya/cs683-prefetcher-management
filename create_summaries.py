from pathlib import Path
import csv
import re

ROOT = Path.cwd()
LOGS = ROOT / "logs"
RESULTS = ROOT / "results"

PREFETCHERS = ["baseline", "ip_stride", "next_line", "spp_dev", "ipop"]

def classify(path):
    name = path.name.lower()
    parent = path.parent.name.lower()

    if "ipop" in name or "i_pop" in name or "ipop" in parent:
        return "ipop"
    if "baseline" in name or parent == "baseline":
        return "baseline"
    if "ip_stride" in name or parent == "ip_stride":
        return "ip_stride"
    if "next_line" in name or parent == "next_line":
        return "next_line"
    if "spp_dev" in name or parent == "spp_dev":
        return "spp_dev"

    return None

def extract_metrics(path):
    text = path.read_text(errors="replace")

    ipc_matches = re.findall(
        r"CPU 0 cumulative IPC:\s*([\d.]+)"
        r"\s+instructions:\s*(\d+)\s+cycles:\s*(\d+)",
        text,
    )

    prefetch_matches = re.findall(
        r"cpu0->cpu0_L2C PREFETCH REQUESTED:\s*(\d+)"
        r"\s+ISSUED:\s*(\d+)\s+USEFUL:\s*(\d+)"
        r"\s+USELESS:\s*(\d+)",
        text,
    )

    ipc, instructions, cycles = (
        ipc_matches[-1] if ipc_matches else ("", "", "")
    )

    requested, issued, useful, useless = (
        prefetch_matches[-1]
        if prefetch_matches
        else ("", "", "", "")
    )

    benchmark = path.name
    benchmark = re.sub(r"__Simulation_Log\.txt$", "", benchmark)
    benchmark = re.sub(r"^I_POP_Adaptive_Controller__", "", benchmark)
    benchmark = re.sub(r"^Baseline__", "", benchmark)
    benchmark = re.sub(r"^ip_stride__", "", benchmark)
    benchmark = re.sub(r"^next_line__", "", benchmark)
    benchmark = re.sub(r"^spp_dev__", "", benchmark)
    benchmark = re.sub(r"^SPEC2017_", "", benchmark)
    benchmark = re.sub(r"^baseline_", "", benchmark)
    benchmark = re.sub(r"^ip_stride_", "", benchmark)
    benchmark = re.sub(r"^next_line_", "", benchmark)
    benchmark = re.sub(r"^spp_dev_", "", benchmark)
    benchmark = re.sub(r"\.log$", "", benchmark)

    return {
        "benchmark": benchmark,
        "log_file": str(path.relative_to(ROOT)),
        "ipc": ipc,
        "instructions": instructions,
        "cycles": cycles,
        "l2_prefetch_requested": requested,
        "l2_prefetch_issued": issued,
        "l2_prefetch_useful": useful,
        "l2_prefetch_useless": useless,
    }

all_logs = [
    p for p in LOGS.rglob("*")
    if p.is_file()
    and (
        p.name.endswith(".log")
        or p.name.endswith("Simulation_Log.txt")
    )
]

records = {name: [] for name in PREFETCHERS}

for path in all_logs:
    category = classify(path)
    if category:
        row = extract_metrics(path)
        row["prefetcher"] = category
        records[category].append(row)

for category in PREFETCHERS:
    out_dir = RESULTS / category
    out_dir.mkdir(parents=True, exist_ok=True)

    rows = sorted(records[category], key=lambda r: r["benchmark"])

    csv_path = out_dir / f"{category}_summary.csv"
    txt_path = out_dir / f"{category}_summary.txt"

    columns = [
        "prefetcher", "benchmark", "ipc", "instructions", "cycles",
        "l2_prefetch_requested", "l2_prefetch_issued",
        "l2_prefetch_useful", "l2_prefetch_useless", "log_file",
    ]

    with csv_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)

    with txt_path.open("w") as f:
        f.write(f"{category.upper()} — SIMULATION SUMMARY\n")
        f.write("=" * 76 + "\n\n")
        f.write("Simulation settings: check the original run command/log.\n")
        f.write("These summaries extract recorded metrics; they do not rerun simulations.\n\n")

        if not rows:
            f.write("No matching log files were found for this configuration.\n")
        else:
            for row in rows:
                f.write(f"Benchmark: {row['benchmark']}\n")
                f.write(f"  IPC: {row['ipc'] or 'NOT FOUND'}\n")
                f.write(f"  Instructions: {row['instructions'] or 'NOT FOUND'}\n")
                f.write(f"  Cycles: {row['cycles'] or 'NOT FOUND'}\n")
                f.write(f"  L2 prefetch requested: {row['l2_prefetch_requested'] or 'NOT FOUND'}\n")
                f.write(f"  L2 prefetch issued: {row['l2_prefetch_issued'] or 'NOT FOUND'}\n")
                f.write(f"  L2 prefetch useful: {row['l2_prefetch_useful'] or 'NOT FOUND'}\n")
                f.write(f"  L2 prefetch useless: {row['l2_prefetch_useless'] or 'NOT FOUND'}\n")
                f.write(f"  Raw log: {row['log_file']}\n\n")

    print(f"{category:12} | {len(rows):2} logs | {csv_path.relative_to(ROOT)}")

print("\nSummary generation finished.")
print("Check the log counts above; zero means no matching logs were detected.")
