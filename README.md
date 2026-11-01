# Gemma 4 post-cutoff memorization probe: release bundle

Code, task list, and raw outputs behind the paper `paper/PAPER_SUBMIT.pdf`.

- `data/VERIFIED_KEEPS.jsonl`: fail-to-pass verified bug-fix tasks (set A pre-cutoff, set B post-cutoff), metadata only, from MIT / BSD-3-Clause repos.
- `code/`: task mining (`mine_prs.py`), fail-to-pass verification (`verify_f2p.py`, Kaggle notebook), probe input builder and library (`build_probe_inputs.py`, `probe_lib.py`, tests), the Kaggle probe notebook, and the figure/results generators.
- `results/`: per-hunk model outputs for both sets and `1_summary.json` with the reported statistics.
- `paper/`: the submitted PDF, Figure 1, and the pre-registration note.

Reproduce the numbers: run `code/probe_gemma4_kaggle.ipynb` on Kaggle, then `python code/gen_results_section.py` against the produced summary JSON.
