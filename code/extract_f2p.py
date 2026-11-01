"""For keep_bugfix tasks: fill license, and extract candidate FAIL_TO_PASS test names
(test functions added/modified in the PR's test-file patches) via GitHub API. Read-only."""
import json, re, subprocess, sys
LIC={"Textualize/rich":"MIT","pallets/click":"BSD-3-Clause","pallets/flask":"BSD-3-Clause","pallets/werkzeug":"BSD-3-Clause"}
rows=[json.loads(l) for l in open("triaged.jsonl")]
out=[]
for r in rows:
    r["license_check"]=LIC.get(r["repo"],"TODO")
    if r.get("triage")!="keep_bugfix": continue
    try:
        files=json.loads(subprocess.run(["gh","api",f"repos/{r['repo']}/pulls/{r['pr']}/files?per_page=100"],capture_output=True,text=True,timeout=40).stdout)
    except Exception as e:
        print("ERR",r["pr"],e,file=sys.stderr); files=[]
    names=set()
    for f in files:
        if f["filename"] not in r["test_files"]: continue
        for line in (f.get("patch") or "").splitlines():
            m=re.match(r"^[+ ].*?def (test_\w+)",line) if line.startswith("+") else None
            if m: names.add(f"{f['filename']}::{m.group(1)}")
        # hunk headers naming the enclosing test
        for m in re.finditer(r"^@@.*@@ .*def (test_\w+)",f.get("patch") or "",re.M):
            names.add(f"{f['filename']}::{m.group(1)}")
    r["fail_to_pass_candidates"]=sorted(names)
    out.append(r)
with open("triaged.jsonl","w") as fh:
    for r in rows: fh.write(json.dumps(r)+"\n")
with open("keeps_f2p.jsonl","w") as fh:
    for r in out: fh.write(json.dumps(r)+"\n")
for r in out: print(r["repo"],r["pr"],len(r["fail_to_pass_candidates"]),r["fail_to_pass_candidates"][:3])
