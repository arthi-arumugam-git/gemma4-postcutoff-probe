"""Render RESULTS_SECTION.md from the Kaggle probe summary JSON.

Usage: python3 gen_results_section.py <model>_summary.json [out.md]
Only reports numbers present in the summary; makes no claim the data does not support.
"""
import json, sys

def pretty_model(m):
    """Display name for a Kaggle model path (e.g. .../gemma-4-e2b-it/1 -> Gemma 4 E2B-it)."""
    base = [p for p in m.strip("/").split("/") if not p.isdigit()][-1]
    if base.startswith("gemma-4-"):
        size, _, rest = base[len("gemma-4-"):].partition("-")
        return "Gemma 4 " + size.upper() + ("-" + rest if rest else "")
    return base


ALPHA = 0.05

def fmt(x, d=3):
    return f"{x:.{d}f}"

def verdict(m):
    lo, hi = m["ci95"]
    if m["p_one_sided"] < ALPHA and lo > 0:
        return "set A (pre-cutoff) scores higher than set B (post-cutoff), consistent with memorization of pre-cutoff code"
    if m["p_one_sided"] < ALPHA:
        return "the one-sided test is significant but the 95% interval includes zero, so the evidence is weak"
    return "no significant A-over-B gap, so we find no evidence of memorization at this sample size"

def render(s):
    out = ["## Results", ""]
    nA, nB = s["n_hunks"]
    out.append(f"Model {pretty_model(s['model'])} ({s['backend']} backend, greedy decoding). "
               f"We scored {nA} hunks in set A and {nB} hunks in set B"
               + (f" (smoke run, LIMIT={s['limit']})." if s.get("limit") else "."))
    out += ["", "| Metric | Set A mean | Set B mean | A minus B | 95% CI | p (one-sided) | Tasks A/B |",
            "|---|---|---|---|---|---|---|"]
    for key, label in (("lcs", "Normalized LCS"), ("exact5", "Exact next-5-lines")):
        m = s[key]; lo, hi = m["ci95"]
        out.append(f"| {label} | {fmt(m['mean_A'])} | {fmt(m['mean_B'])} | {fmt(m['diff_A_minus_B'])} | "
                   f"[{fmt(lo)}, {fmt(hi)}] | {fmt(m['p_one_sided'], 4)} | {m['n_tasks'][0]}/{m['n_tasks'][1]} |")
    out.append("")
    for key, label in (("lcs", "On normalized LCS"), ("exact5", "On exact match")):
        out.append(f"{label}, {verdict(s[key])}.")
    out += ["", "Task-level means are compared with a permutation test (A > B) and a bootstrap 95% interval, as pre-registered in `prereg.md`.", "",
            "![Figure 1. Left: per-task mean LCS for set A and set B (box = quartiles, dots = tasks). Right: A minus B difference with bootstrap 95% CI.](fig1_lcs.png)", ""]
    return "\n".join(out)

if __name__ == "__main__":
    s = json.load(open(sys.argv[1]))
    md = render(s)
    if len(sys.argv) > 2:
        open(sys.argv[2], "w").write(md)
    print(md)
