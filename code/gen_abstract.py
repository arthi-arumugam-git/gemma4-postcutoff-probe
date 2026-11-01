"""Render ABSTRACT.md (and a title) from the Kaggle probe summary JSON, reusing gen_results_section.verdict.
Usage: python3 gen_abstract.py <model>_summary.json
Every number comes from the summary; nothing else is claimed."""
import json, sys
from gen_results_section import fmt, verdict, ALPHA

def pretty_model(m):
    """Display name for a Kaggle model path (e.g. .../gemma-4-e2b-it/1 -> Gemma 4 E2B-it)."""
    base = [p for p in m.strip("/").split("/") if not p.isdigit()][-1]
    if base.startswith("gemma-4-"):
        size, _, rest = base[len("gemma-4-"):].partition("-")
        return "Gemma 4 " + size.upper() + ("-" + rest if rest else "")
    return base


def title(s):
    sig = s["lcs"]["p_one_sided"] < ALPHA and s["lcs"]["ci95"][0] > 0
    return (f"Does {pretty_model(s['model'])} remember pre-cutoff bug fixes? "
            + ("A small but significant memorization signal" if sig else "No memorization signal on pre- vs post-cutoff Python fixes"))

def render(s):
    nA, nB = s["n_hunks"]; l = s["lcs"]; e = s["exact5"]
    smoke = f" This is a smoke run (LIMIT={s['limit']}); treat numbers as preliminary." if s.get("limit") else ""
    return "\n".join(["## Abstract", "",
        f"Benchmarks built from public repositories may reward recall instead of repair. We probe {pretty_model(s['model'])} "
        f"with greedy completion of real Python bug-fix hunks, comparing set A ({nA} hunks from fixes likely before the model's "
        f"training cutoff) with set B ({nB} hunks from fixes after it). Mean normalized LCS is {fmt(l['mean_A'])} on A and "
        f"{fmt(l['mean_B'])} on B (difference {fmt(l['diff_A_minus_B'])}, 95% CI [{fmt(l['ci95'][0])}, {fmt(l['ci95'][1])}], "
        f"one-sided permutation p = {fmt(l['p_one_sided'], 4)}); exact next-5-line match is {fmt(e['mean_A'])} vs {fmt(e['mean_B'])}. "
        f"On LCS, {verdict(l)}.{smoke} We release the probe, splits, and scoring code.", ""])

if __name__ == "__main__":
    s = json.load(open(sys.argv[1]))
    open("ABSTRACT.md", "w").write(render(s)); open("TITLE.txt", "w").write(title(s) + "\n")
    print(title(s)); print(render(s))
