#!/usr/bin/env python3
import csv, glob, os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

OUT = "results_ckpt2/figs"
os.makedirs(OUT, exist_ok=True)
rows = list(csv.DictReader(open("results_ckpt2/summary.csv")))
def get(tr, arm, f="ipc"):
    for r in rows:
        if r["trace"] == tr and r["arm"] == arm:
            return float(r[f])
    return None
TRACES = ["gcc", "mcf", "lbm", "xz"]

# --- Fig 1: IPC vs fixed window length (your Figure 19(d)) ---
sweep = [("A3", 1024), ("S2048", 2048), ("S4096", 4096), ("S8192", 8192)]
plt.figure(figsize=(7, 4.5))
for tr in TRACES:
    xs, ys = [], []
    for arm, w in sweep:
        v = get(tr, arm)
        if v is not None:
            xs.append(w); ys.append(v / get(tr, "A3"))
    if xs:
        plt.plot(xs, ys, "o-", label=tr)
    a4 = get(tr, "A4")
    if a4 is not None:
        plt.axhline(a4 / get(tr, "A3"), ls="--", lw=0.8, alpha=0.5)
plt.xscale("log", base=2); plt.xlabel("Control window (L2 demand accesses)")
plt.ylabel("IPC, normalised to 1K window"); plt.legend(); plt.grid(alpha=0.3)
plt.title("Performance vs fixed control-window length")
plt.tight_layout(); plt.savefig(f"{OUT}/fig1_window_sweep.png", dpi=150)

# --- Fig 2: window length over time, adaptive (A4) ---
plt.figure(figsize=(7, 4.5))
for tr in TRACES:
    p = f"results_ckpt2/windows/{tr}.A4.csv"
    if not os.path.exists(p):
        continue
    d = list(csv.DictReader(open(p)))
    plt.plot([int(x["window_index"]) for x in d],
             [int(x["window_len"]) for x in d], lw=0.9, label=tr)
plt.yscale("log", base=2); plt.xlabel("Window index")
plt.ylabel("Window length"); plt.legend(); plt.grid(alpha=0.3)
plt.title("Adaptive control-window length over execution")
plt.tight_layout(); plt.savefig(f"{OUT}/fig2_window_over_time.png", dpi=150)

# --- Fig 3: the 2x2 ---
arms = ["R4", "A1", "A2", "A3", "A4"]
labels = ["static all-on", "acc+fixed", "acc+adapt", "PE+fixed", "PE+adapt"]
plt.figure(figsize=(8, 4.5))
w = 0.15
for i, tr in enumerate(TRACES):
    vals = [(get(tr, a) or 0) / (get(tr, "R1") or 1) for a in arms]
    plt.bar([j + i * w for j in range(len(arms))], vals, w, label=tr)
plt.xticks([j + 1.5 * w for j in range(len(arms))], labels)
plt.ylabel("IPC speedup over ip_stride (R1)"); plt.legend(); plt.grid(axis="y", alpha=0.3)
plt.axhline(1.0, color="k", lw=0.8)
plt.title("Control signal x window policy")
plt.tight_layout(); plt.savefig(f"{OUT}/fig3_2x2.png", dpi=150)

# --- Spearman: accuracy vs IPC speedup, per trace ---
def spearman(x, y):
    n = len(x)
    if n < 3: return float("nan")
    def rank(v):
        s = sorted(range(n), key=lambda i: v[i]); r = [0]*n
        for pos, i in enumerate(s): r[i] = pos + 1
        return r
    rx, ry = rank(x), rank(y)
    d2 = sum((rx[i]-ry[i])**2 for i in range(n))
    return 1 - 6*d2/(n*(n*n-1))

print("\nSpearman(prefetch accuracy, IPC speedup) across arms, per trace:")
for tr in TRACES:
    sub = [r for r in rows if r["trace"] == tr and r["arm"] in ("R1","R2","R3","R4","A1","A3")]
    if len(sub) < 3: continue
    acc = [float(r["pf_accuracy"]) for r in sub]
    spd = [float(r["speedup_vs_R0"]) for r in sub]
    print(f"  {tr:5s} rho = {spearman(acc, spd):+.2f}   (n={len(sub)})")
print(f"\nFigures -> {OUT}/")
