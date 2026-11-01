"""Build prefix-prompt memorization-probe inputs for set B (prereg.md primary measure).

For each clean set-B task (VERIFIED_KEEPS.jsonl, no paper_flags), fetch the gold source
diff (base_sha..merge_sha, src_files only) from the GitHub compare API, and for each
hunk split its lines 50/50 into prompt prefix and gold remainder. No model is run here.
Output: probe/setB_probe_inputs.jsonl (one row per hunk).
"""
import json, subprocess, sys, pathlib

HERE = pathlib.Path(__file__).parent
OUT = HERE / "probe" / "setB_probe_inputs.jsonl"

def compare(repo, base, head):
    r = subprocess.run(["gh", "api", f"repos/{repo}/compare/{base}...{head}"],
                       capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError(r.stderr.strip()[:200])
    return json.loads(r.stdout)

def hunks(patch):
    cur = None
    for line in patch.splitlines():
        if line.startswith("@@"):
            if cur: yield cur
            cur = {"header": line, "lines": []}
        elif cur is not None:
            cur["lines"].append(line)
    if cur: yield cur

def main():
    rows = [json.loads(l) for l in open(HERE / "VERIFIED_KEEPS.jsonl")]
    rows = [r for r in rows if not r.get("paper_flags")]
    done = set()
    if OUT.exists():
        for l in open(OUT):
            d = json.loads(l); done.add((d["repo"], d["pr"]))
    errs = 0
    with open(OUT, "a") as f:
        for r in rows:
            key = (r["repo"], r["pr"])
            if key in done: continue
            try:
                c = compare(r["repo"], r["base_sha"], r["merge_sha"])
            except Exception as e:
                errs += 1; print("ERR", key, e, file=sys.stderr); continue
            src = set(r["src_files"])
            for fobj in c.get("files", []):
                if fobj["filename"] not in src or "patch" not in fobj: continue
                for i, h in enumerate(hunks(fobj["patch"])):
                    n = len(h["lines"]); k = n // 2
                    if n < 4: continue
                    f.write(json.dumps({
                        "repo": r["repo"], "pr": r["pr"], "title": r["title"],
                        "file": fobj["filename"], "hunk_idx": i, "header": h["header"],
                        "n_lines": n, "prefix": "\n".join(h["lines"][:k]),
                        "gold_remainder": "\n".join(h["lines"][k:]),
                    }) + "\n")
            f.flush()
    print(f"tasks={len(rows)} errors={errs}")

if __name__ == "__main__":
    main()
