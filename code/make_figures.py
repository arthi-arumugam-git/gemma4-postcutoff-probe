"""Figure 1 for the Gemma 4 memorization paper, from Kaggle v2 outputs only.

Per-task mean LCS (hunks averaged within a task) for set A (competition dev tasks) vs
set B (post-cutoff fixes), with the summary JSON's mean difference and bootstrap CI.
Run: .venv/bin/python make_figures.py
"""
import json, statistics, random
from collections import defaultdict
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

R = "results_v2"
summ = json.load(open(f"{R}/1_summary.json"))

def per_task(path):
    d = defaultdict(list)
    for line in open(path):
        h = json.loads(line)
        d[h["task"]].append(h["lcs"])
    return [statistics.mean(v) for v in d.values()]

A, B = per_task(f"{R}/1_A_hunks.jsonl"), per_task(f"{R}/1_B_hunks.jsonl")
mA, mB = statistics.mean(A), statistics.mean(B)
# Sanity: must reproduce the Kaggle summary exactly, else aggregation differs.
assert abs(mA - summ["lcs"]["mean_A"]) < 1e-9 and abs(mB - summ["lcs"]["mean_B"]) < 1e-9, (mA, mB)
assert (len(A), len(B)) == tuple(summ["lcs"]["n_tasks"])

lo, hi = summ["lcs"]["ci95"]; diff = summ["lcs"]["diff_A_minus_B"]; p = summ["lcs"]["p_one_sided"]
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9, 3.6), gridspec_kw={"width_ratios": [2, 1]})
rng = random.Random(0)
for i, (vals, lab) in enumerate([(A, f"Set A (n={len(A)} tasks)"), (B, f"Set B (n={len(B)} tasks)")]):
    ax1.boxplot(vals, positions=[i], widths=0.5, showfliers=False)
    ax1.scatter([i + rng.uniform(-0.18, 0.18) for _ in vals], vals, s=6, alpha=0.4)
ax1.set_xticks([0, 1], [f"Set A\n(n={len(A)})", f"Set B\n(n={len(B)})"])
ax1.set_ylabel("Per-task mean LCS ratio")
ax1.set_title("Hunk reconstruction similarity by task")
ax2.errorbar([0], [diff], yerr=[[diff - lo], [hi - diff]], fmt="o", capsize=6)
ax2.axhline(0, color="grey", lw=0.8, ls="--")
ax2.set_xticks([0], ["A minus B"]); ax2.set_xlim(-0.6, 0.6)
ax2.set_ylabel("Difference in mean LCS")
ax2.set_title(f"diff {diff:.3f}, 95% CI [{lo:.3f}, {hi:.3f}]\none-sided p = {p:.4f}", fontsize=9)
fig.tight_layout()
fig.savefig("fig1_lcs.png", dpi=200); fig.savefig("fig1_lcs.pdf")
print(f"A {mA:.4f} B {mB:.4f} diff {diff:.4f} -> fig1_lcs.png/.pdf")
