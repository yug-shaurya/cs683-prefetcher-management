#!/usr/bin/env python3
import json, glob, os, csv

ARMS = ["R0","R1","R2","R3","R4","A1","A2","A3","A4","S2048","S4096","S8192","T1","T1a","W64"]
TRACES = ["gcc","mcf","lbm","xz"]

def total(cache, field):
    s = 0
    for t in ("LOAD","RFO","WRITE","TRANSLATION","PREFETCH"):
        if t in cache:
            s += sum(cache[t].get(field, [0]))
    return s

def demand(cache, field):
    s = 0
    for t in ("LOAD","RFO"):
        if t in cache:
            s += sum(cache[t].get(field, [0]))
    return s

rows = []
for tr in TRACES:
    for arm in ARMS:
        p = f"results_ckpt2/{tr}.{arm}.json"
        if not os.path.exists(p):
            continue
        r = json.load(open(p))
        if isinstance(r, list):
            r = r[-1]
        roi = r["roi"]
        core = roi["cores"][0]
        l2 = roi["cpu0_L2C"]
        llc = roi["LLC"]
        instr = core["instructions"]
        kinstr = instr / 1000.0
        issued = l2.get("prefetch issued", 0)
        useful = l2.get("useful prefetch", 0)
        useless = l2.get("useless prefetch", 0)
        rows.append({
            "trace": tr,
            "arm": arm,
            "ipc": instr / core["cycles"],
            "instructions": instr,
            "l2_mpki": total(l2, "miss") / kinstr,
            "l2_demand_mpki": demand(l2, "miss") / kinstr,
            "llc_mpki": total(llc, "miss") / kinstr,
            "l2_miss_latency": l2.get("miss latency", 0),
            "pf_issued": issued,
            "pf_useful": useful,
            "pf_useless": useless,
            "pf_accuracy": (useful / issued) if issued else 0.0,
        })

# speedup over R0 and over R1 (the PC-Stride-equivalent reference)
for base in ("R0", "R1"):
    ref = {r["trace"]: r["ipc"] for r in rows if r["arm"] == base}
    for r in rows:
        b = ref.get(r["trace"])
        r[f"speedup_vs_{base}"] = (r["ipc"] / b) if b else float("nan")

if rows:
    cols = list(rows[0].keys())
    with open("results_ckpt2/summary.csv", "w", newline="") as f:
        w = csv.DictWriter(f, cols)
        w.writeheader()
        w.writerows(rows)
    print(f"{len(rows)} rows -> results_ckpt2/summary.csv\n")
    for r in rows:
        print(f"{r['trace']:5s} {r['arm']:6s} IPC={r['ipc']:.4f} "
              f"vsR0={r['speedup_vs_R0']:.2f} vsR1={r['speedup_vs_R1']:.2f} "
              f"L2MPKI={r['l2_mpki']:6.1f} acc={r['pf_accuracy']*100:5.1f}%")
else:
    print("no results yet")
    
