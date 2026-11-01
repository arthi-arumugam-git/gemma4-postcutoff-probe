#!/usr/bin/env python3
"""Mine candidate post-cutoff SWE tasks from merged GitHub PRs (paper-track resource).

A candidate = merged PR, merged after --since, that changes at least one non-test .py file
AND at least one test file. Output is a JSONL of candidates (metadata only, no Kaggle data).
Fail-to-pass / pass-to-pass verification happens later in the sandbox (gemma4h), not here.

Usage: python mine_prs.py --repo fastapi/fastapi --since 2026-01-01 --limit 40 --out cands.jsonl
Requires: gh CLI authenticated (read-only API calls).
"""
import argparse, json, subprocess, sys

def gh(path):
    out = subprocess.run(["gh", "api", path], capture_output=True, text=True)
    if out.returncode != 0:
        raise RuntimeError(out.stderr.strip())
    return json.loads(out.stdout)

def is_test(p):
    name = p.rsplit("/", 1)[-1]
    return p.endswith(".py") and ("/tests/" in "/" + p or name.startswith("test_") or name.endswith("_test.py"))

def classify(files):
    src = [f["filename"] for f in files if f["filename"].endswith(".py") and not is_test(f["filename"])]
    tst = [f["filename"] for f in files if is_test(f["filename"])]
    return src, tst

def mine(repo, since, limit, max_pages=10):
    found = []
    for page in range(1, max_pages + 1):
        prs = gh(f"repos/{repo}/pulls?state=closed&sort=updated&direction=desc&per_page=50&page={page}")
        if not prs:
            break
        for pr in prs:
            m = pr.get("merged_at")
            if not m or m[:10] < since:
                continue
            files = gh(f"repos/{repo}/pulls/{pr['number']}/files?per_page=100")
            src, tst = classify(files)
            if not src or not tst or len(src) > 5:
                continue
            found.append({
                "repo": repo, "pr": pr["number"], "url": pr["html_url"], "title": pr["title"],
                "merged_at": m, "base_sha": pr["base"]["sha"], "merge_sha": pr.get("merge_commit_sha"),
                "src_files": src, "test_files": tst,
                "additions": sum(f["additions"] for f in files), "deletions": sum(f["deletions"] for f in files),
                "license_check": "TODO", "verified": False,
            })
            if len(found) >= limit:
                return found
        if prs[-1]["updated_at"][:10] < since:
            break
    return found

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True); ap.add_argument("--since", required=True)
    ap.add_argument("--limit", type=int, default=40); ap.add_argument("--out", default="-")
    a = ap.parse_args()
    rows = mine(a.repo, a.since, a.limit)
    fh = sys.stdout if a.out == "-" else open(a.out, "a")
    for r in rows:
        fh.write(json.dumps(r) + "\n")
    print(f"{a.repo}: {len(rows)} candidates since {a.since}", file=sys.stderr)
