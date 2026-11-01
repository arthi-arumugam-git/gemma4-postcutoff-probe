"""Memorization-probe core (prereg.md primary measure). Pure Python, no model.
Shared by the box tests and the Kaggle notebook so set A and set B use identical
splitting, prompting and scoring.
"""
import json, random, re

MIN_LINES = 4

def hunks(patch):
    """Yield (file, hunk_idx, header, lines) from a unified diff."""
    file = None; cur = None; idx = 0
    for line in patch.splitlines():
        if line.startswith("diff --git "):
            if cur: yield cur
            cur = None; idx = 0
            m = re.search(r" b/(.+)$", line); file = m.group(1) if m else None
        elif line.startswith("@@"):
            if cur: yield cur
            cur = (file, idx, line, []); idx += 1
        elif cur is not None and not line.startswith(("--- ", "+++ ")):
            cur[3].append(line)
    if cur: yield cur

def is_test_path(p):
    return bool(p) and (p.startswith(("tests/", "test/")) or "/tests/" in p or p.split("/")[-1].startswith("test_"))

def split_rows(task_id, title, patch):
    """50/50 line split per hunk, same rule as build_probe_inputs.py (set B)."""
    out = []
    for file, i, header, lines in hunks(patch):
        if is_test_path(file) or len(lines) < MIN_LINES: continue
        k = len(lines) // 2
        out.append({"task": task_id, "title": title, "file": file, "hunk_idx": i,
                    "header": header, "n_lines": len(lines),
                    "prefix": "\n".join(lines[:k]), "gold_remainder": "\n".join(lines[k:])})
    return out

def setA_rows(tasks):
    """tasks: dicts from Kaggle tasks.jsonl (instance_id, problem_statement, patch)."""
    rows = []
    for t in tasks:
        title = (t.get("problem_statement") or "").strip().splitlines()[0][:200] if t.get("problem_statement") else ""
        rows += split_rows(t["instance_id"], title, t["patch"])
    return rows

def prompt(row):
    return (f"Pull request: {row['title']}\nFile: {row['file']}\n{row['header']}\n"
            f"Continue this unified diff hunk exactly.\n{row['prefix']}\n")

def _tok(s):
    return re.findall(r"\w+|[^\w\s]", s)

def lcs_ratio(pred, gold):
    a, b = _tok(pred), _tok(gold)
    if not b: return 0.0
    prev = [0] * (len(b) + 1)
    for x in a:
        cur = [0]
        for j, y in enumerate(b):
            cur.append(prev[j] + 1 if x == y else max(prev[j + 1], cur[j]))
        prev = cur
    return prev[-1] / len(b)

def exact5(pred, gold):
    norm = lambda s: [l.rstrip() for l in s.splitlines()][:5]
    g = norm(gold); return float(bool(g) and norm(pred)[:len(g)] == g)

def score(pred, gold):
    return {"lcs": lcs_ratio(pred, gold), "exact5": exact5(pred, gold)}

def task_means(scored, key="lcs"):
    """Average hunks within a task so big diffs don't dominate (unit = task)."""
    by = {}
    for r in scored: by.setdefault(r["task"], []).append(r[key])
    return [sum(v) / len(v) for v in by.values()]

def perm_test(a, b, n=10000, seed=0):
    """One-sided H1: mean(a) > mean(b). Returns observed diff and p."""
    rng = random.Random(seed); obs = sum(a)/len(a) - sum(b)/len(b)
    pool = a + b; na = len(a); hits = 0
    for _ in range(n):
        rng.shuffle(pool)
        d = sum(pool[:na])/na - sum(pool[na:])/(len(pool)-na)
        hits += d >= obs
    return obs, (hits + 1) / (n + 1)

def bootstrap_ci(a, b, n=10000, seed=1):
    rng = random.Random(seed); ds = []
    for _ in range(n):
        sa = [rng.choice(a) for _ in a]; sb = [rng.choice(b) for _ in b]
        ds.append(sum(sa)/len(sa) - sum(sb)/len(sb))
    ds.sort(); return ds[int(0.025*n)], ds[int(0.975*n)]
