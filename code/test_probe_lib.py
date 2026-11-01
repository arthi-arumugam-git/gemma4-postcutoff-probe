import json, pathlib, probe_lib as P
PATCH = """diff --git a/pkg/a.py b/pkg/a.py
--- a/pkg/a.py
+++ b/pkg/a.py
@@ -1,3 +1,5 @@ def f():
 x = 1
-y = 2
+y = 3
+z = 4
 return x
diff --git a/tests/test_a.py b/tests/test_a.py
--- a/tests/test_a.py
+++ b/tests/test_a.py
@@ -1,1 +1,5 @@
+a
+b
+c
+d
"""
def test_split_skips_tests_and_halves():
    rows = P.setA_rows([{"instance_id": "t1", "problem_statement": "Fix y\nmore", "patch": PATCH}])
    assert len(rows) == 1 and rows[0]["file"] == "pkg/a.py" and rows[0]["title"] == "Fix y"
    assert rows[0]["prefix"] == " x = 1\n-y = 2" and rows[0]["gold_remainder"] == "+y = 3\n+z = 4\n return x"
def test_split_matches_setB_rule():
    r = json.loads(open(pathlib.Path(__file__).parent / "probe/setB_probe_inputs.jsonl").readline())
    assert len(r["prefix"].splitlines()) == r["n_lines"] // 2
def test_scores():
    g = "+y = 3\n+z = 4"
    assert P.score(g, g) == {"lcs": 1.0, "exact5": 1.0}
    assert P.score("", g) == {"lcs": 0.0, "exact5": 0.0}
    assert 0 < P.lcs_ratio("+y = 3", g) < 1
def test_stats():
    obs, p = P.perm_test([1.0]*20, [0.0]*20, n=2000); assert obs == 1.0 and p < 0.01
    obs, p = P.perm_test([0.5]*20, [0.5]*20, n=2000); assert p > 0.5
    lo, hi = P.bootstrap_ci([1.0, 0.9]*10, [0.1, 0.0]*10, n=2000); assert lo > 0.5
def test_task_means():
    assert P.task_means([{"task": "a", "lcs": 1}, {"task": "a", "lcs": 0}, {"task": "b", "lcs": 1}]) == [0.5, 1.0]
