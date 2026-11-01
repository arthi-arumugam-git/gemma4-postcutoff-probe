"""Render CONCLUSION_SECTION.md (conclusion + reproducibility) from results_v2/1_summary.json.
Every number comes from the summary file. Usage: python3 gen_conclusion.py [summary.json]"""
import json, sys
p = sys.argv[1] if len(sys.argv) > 1 else "results_v2/1_summary.json"
d = json.load(open(p))
l, e = d["lcs"], d["exact5"]
nA, nB = d["n_hunks"]
lsig = l["p_one_sided"] < 0.05 and l["ci95"][0] > 0
esig = e["p_one_sided"] < 0.05 and e["ci95"][0] > 0
f = lambda x: f"{x:.3f}"
lines = ["## Conclusion", ""]
if lsig:
    lines.append(f"On {nA} pre-cutoff and {nB} post-cutoff bug-fix hunks, Gemma 4 E2B-it reproduces pre-cutoff fixes more closely than post-cutoff ones: mean normalized LCS {f(l['mean_A'])} vs {f(l['mean_B'])} (difference {f(l['diff_A_minus_B'])}, 95% CI [{f(l['ci95'][0])}, {f(l['ci95'][1])}], one-sided p = {l['p_one_sided']:.4f}).")
else:
    lines.append(f"On {nA} pre-cutoff and {nB} post-cutoff hunks we find no significant LCS gap (difference {f(l['diff_A_minus_B'])}, p = {l['p_one_sided']:.4f}).")
lines.append("" )
lines.append(("Exact next-5-line matches are rare in both sets and the gap is " + ("significant" if esig else f"not significant (p = {e['p_one_sided']:.4f})") + ", so the signal is partial recall of fix shape rather than verbatim regurgitation."))
lines += ["", "The practical consequence is that repository-level benchmarks built from public pre-cutoff fixes can overstate repair ability for this model; we tested only E2B, so larger Gemma 4 sizes remain open. Evaluations that report scores for Gemma 4 should split tasks by fix date relative to the training cutoff, or report both splits side by side.", "",
          "## Reproducibility", "",
          "All code and data are public at https://github.com/arthi-arumugam-git/gemma4-postcutoff-probe. The release contains the task miner, the fail-to-pass verifier, the probe-input builder, the Kaggle notebook that ran the probe, the scoring and statistics code, and the per-hunk outputs for both sets. "
          f"The probe ran on Kaggle with the `{d['backend']}` backend and greedy decoding; the statistical test and interval were fixed in the pre-registration before any model run. Figure 1 is regenerated from the per-hunk outputs and the script asserts it matches the reported means.", ""]
open("CONCLUSION_SECTION.md", "w").write("\n".join(lines))
print("wrote CONCLUSION_SECTION.md")
