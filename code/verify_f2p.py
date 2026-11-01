"""Fail-to-pass / pass-to-pass verifier for Gemma 4 paper keeps.
Run INSIDE the gemma4h sandbox (Kaggle notebook), not on the box.
For each keep: clone repo at base_sha, apply PR test files from merge_sha,
run F2P candidates (expect FAIL), then check out merge_sha src and rerun (expect PASS).
Writes keeps_verified.jsonl with verified=true/false and observed statuses.
Usage: python verify_f2p.py keeps_f2p.jsonl keeps_verified.jsonl [--workdir /kaggle/working/f2p]
"""
import json, subprocess, sys, os, argparse

def sh(cmd, cwd=None, timeout=900):
    p = subprocess.run(cmd, cwd=cwd, shell=True, capture_output=True, text=True, timeout=timeout)
    return p.returncode, p.stdout[-4000:] + p.stderr[-4000:]

def run_tests(repo_dir, tests):
    status = {}
    for t in tests:
        rc, _ = sh(f"python -m pytest -x -q {t!r} -p no:cacheprovider", cwd=repo_dir, timeout=600)
        status[t] = "PASS" if rc == 0 else "FAIL"
    return status

def verify(task, workdir):
    name = task["repo"].replace("/", "__") + f"_{task['pr']}"
    d = os.path.join(workdir, name)
    if not os.path.isdir(d):
        sh(f"git clone --quiet https://github.com/{task['repo']}.git {d}", timeout=1200)
    sh(f"git fetch --quiet origin {task['merge_sha']} {task['base_sha']}", cwd=d)
    sh(f"git checkout --quiet -f {task['base_sha']}", cwd=d)
    sh("python -m pip install -q -e . pytest", cwd=d, timeout=1200)
    tf = " ".join(task["test_files"])
    sh(f"git checkout --quiet {task['merge_sha']} -- {tf}", cwd=d)
    tests = task.get("fail_to_pass_candidates", [])
    before = run_tests(d, tests)
    sf = " ".join(task["src_files"])
    sh(f"git checkout --quiet {task['merge_sha']} -- {sf}", cwd=d)
    after = run_tests(d, tests)
    f2p = [t for t in tests if before[t] == "FAIL" and after[t] == "PASS"]
    rc_full, _ = sh(f"python -m pytest -q {tf} -p no:cacheprovider", cwd=d)
    out = dict(task, before=before, after=after, FAIL_TO_PASS=f2p,
               test_files_green_after=(rc_full == 0), verified=bool(f2p) and rc_full == 0)
    sh("git checkout --quiet -f .", cwd=d)
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("inp"); ap.add_argument("out")
    ap.add_argument("--workdir", default="/kaggle/working/f2p")
    a = ap.parse_args()
    os.makedirs(a.workdir, exist_ok=True)
    tasks = [json.loads(l) for l in open(a.inp) if l.strip()]
    with open(a.out, "w") as fo:
        for t in tasks:
            try:
                r = verify(t, a.workdir)
            except Exception as e:
                r = dict(t, verified=False, error=str(e)[:500])
            fo.write(json.dumps(r) + "\n"); fo.flush()
            print(t["repo"], t["pr"], "verified" if r.get("verified") else "NOT verified", r.get("FAIL_TO_PASS"))

if __name__ == "__main__":
    main()
