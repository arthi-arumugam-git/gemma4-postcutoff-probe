"""Generate probe_gemma4_kaggle.ipynb: Gemma 4 greedy prefix completion on set A (Kaggle dev
tasks.jsonl, never leaves Kaggle) and set B (embedded), scored per prereg.md. Run attached to
the gemma-4-developer-agent competition with a Gemma 4 model input added."""
import json, pathlib
H = pathlib.Path(__file__).parent
def cell(src, kind="code"):
    c = {"cell_type": kind, "metadata": {}, "source": src}
    if kind == "code": c.update(outputs=[], execution_count=None)
    return c
cells = [
 cell("# Gemma 4 memorization probe (prereg.md primary measure)\n"
      "Set A = competition dev tasks (local only). Set B = post-cutoff verified keeps (embedded).\n"
      "Greedy, max 256 new tokens, same prompt for both sets. Output: /kaggle/working/results/.\n"
      "Set MODEL_ID below to the attached model path (E2B first, then E4B).", "markdown"),
 cell("%%writefile /kaggle/working/probe_lib.py\n" + (H/"probe_lib.py").read_text()),
 cell("%%writefile /kaggle/working/setB_probe_inputs.jsonl\n" + (H/"probe/setB_probe_inputs.jsonl").read_text()),
 cell("""import glob, json, os, sys, time
sys.path.insert(0, '/kaggle/working'); import probe_lib as P
MODEL_ID = os.environ.get('MODEL_ID') or (sorted(glob.glob('/kaggle/input/**/config.json', recursive=True) or [''])[0].rsplit('/',1)[0])
TASKS = (glob.glob('/kaggle/input/**/tasks.jsonl', recursive=True) or [None])[0]
print('model', MODEL_ID, '| tasks', TASKS)
A = P.setA_rows([json.loads(l) for l in open(TASKS)])
B = [dict(json.loads(l), task=None) for l in open('/kaggle/working/setB_probe_inputs.jsonl')]
for r in B: r['task'] = f"{r['repo']}#{r['pr']}"
print('set A hunks', len(A), 'tasks', len({r['task'] for r in A}), '| set B hunks', len(B), 'tasks', len({r['task'] for r in B}))
LIMIT = int(os.environ.get('LIMIT', '0'))  # smoke: LIMIT=10
if LIMIT: A, B = A[:LIMIT], B[:LIMIT]"""),
 cell("""# Backend: vLLM handles the compressed-tensors QAT checkpoints; fall back to transformers.
try:
    from vllm import LLM, SamplingParams
    llm = LLM(MODEL_ID, max_model_len=4096, gpu_memory_utilization=0.85)
    sp = SamplingParams(temperature=0, max_tokens=256)
    def gen(prompts): return [o.outputs[0].text for o in llm.generate(prompts, sp)]
    BACKEND = 'vllm'
except Exception as e:
    print('vllm unavailable:', repr(e)[:200])
    import torch
    from transformers import AutoTokenizer, AutoModelForCausalLM
    tok = AutoTokenizer.from_pretrained(MODEL_ID)
    mdl = AutoModelForCausalLM.from_pretrained(MODEL_ID, torch_dtype='auto', device_map='auto')
    def gen(prompts):
        out = []
        for p in prompts:
            ids = tok(p, return_tensors='pt').to(mdl.device)
            g = mdl.generate(**ids, max_new_tokens=256, do_sample=False)
            out.append(tok.decode(g[0, ids['input_ids'].shape[1]:], skip_special_tokens=True))
        return out
    BACKEND = 'transformers'
print('backend', BACKEND)"""),
 cell("""os.makedirs('/kaggle/working/results', exist_ok=True)
tag = os.path.basename(MODEL_ID.rstrip('/'))
def run(rows, name):
    t = time.time(); preds = gen([P.prompt(r) for r in rows])
    scored = [dict(task=r['task'], file=r['file'], n_lines=r['n_lines'], **P.score(p, r['gold_remainder'])) for r, p in zip(rows, preds)]
    with open(f'/kaggle/working/results/{tag}_{name}_hunks.jsonl', 'w') as f:
        for s, p in zip(scored, preds): f.write(json.dumps(dict(s, pred=p if name == 'B' else None)) + '\\n')  # set A preds stay off the output (dev data)
    print(name, len(rows), 'hunks in', round(time.time()-t), 's'); return scored
SA, SB = run(A, 'A'), run(B, 'B')"""),
 cell("""summary = {'model': MODEL_ID, 'backend': BACKEND, 'limit': LIMIT, 'n_hunks': [len(SA), len(SB)]}
for key in ('lcs', 'exact5'):
    a, b = P.task_means(SA, key), P.task_means(SB, key)
    obs, p = P.perm_test(a, b); lo, hi = P.bootstrap_ci(a, b)
    summary[key] = {'mean_A': sum(a)/len(a), 'mean_B': sum(b)/len(b), 'n_tasks': [len(a), len(b)],
                    'diff_A_minus_B': obs, 'p_one_sided': p, 'ci95': [lo, hi],
                    'role': 'primary' if key == 'lcs' else 'primary (exact-match)'}
json.dump(summary, open(f'/kaggle/working/results/{tag}_summary.json', 'w'), indent=2)
print(json.dumps(summary, indent=2))"""),
]
nb = {"cells": cells, "metadata": {"kernelspec": {"name": "python3", "display_name": "Python 3"}}, "nbformat": 4, "nbformat_minor": 5}
json.dump(nb, open(H/"probe_gemma4_kaggle.ipynb", "w"), indent=1)
print("wrote probe_gemma4_kaggle.ipynb", len(cells), "cells")
