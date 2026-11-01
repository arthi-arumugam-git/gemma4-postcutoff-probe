# Pre-registration: memorization probe (Gemma 4 paper track)
Written Oct 28 2026, 2:00 PM IST, BEFORE any probe has been run. No results exist yet. Every number in the paper must come from results/*.json produced after this file.

## Question
Do Gemma 4 models show stronger memorization signals on the public dev tasks (popular repos, pre-Jan-2025 history likely in pretraining) than on our post-cutoff mined tasks from the same repos?
Verified cutoff: January 2025 (Gemma 4 model card; arXiv 2607.02770 sec 2.4). Post-cutoff set = keeps_verified.jsonl (merged 2026, after F2P/P2P verification).

## Task sets
- A (dev): the public dev tasks from the Kaggle competition, used only locally, never redistributed.
- B (post-cutoff, same repos): verified keeps from rich / click / flask / werkzeug (target n >= 10 after verification; currently 12 unverified candidates).
- C (control): post-cutoff tasks from repos not in the dev set, if mined in time. Optional.

## Primary measure (fixed now)
Reference-patch completion under prefix prompting: give the model the issue/PR title plus the first 50% of lines of the gold diff hunk; greedy-decode the rest (temperature 0, max 256 tokens). Score = longest common token subsequence ratio vs. the gold remainder, and exact-match rate of the next 5 lines.
## Secondary measures
- Per-token log-likelihood of the gold patch given the pre-patch file (lower NLL = more familiar), normalized by an equal-length shuffled-lines baseline.
- Task resolve rate (pass@1) on A vs B with the same harness and budget.

## Models
Gemma 4 E2B and E4B (Kaggle free GPU only); 31B only if a free path exists. Same prompt, same decoding for every set.

## Analysis plan
- Compare A vs B per measure with a permutation test (10,000 shuffles), report effect size and 95% bootstrap CI.
- Primary test: one-sided, A > B on the completion score, alpha 0.05. Everything else is exploratory and labelled as such.
- A null result is reported as null. No measure is added or dropped after seeing data without saying so in the paper.

## Threats noted up front
- Set B is small and skewed to 4 repos; difficulty differs from A (smaller diffs). Report diff-size-matched subsets.
- Popular-repo code style may be familiar even post-cutoff; set C exists to separate repo familiarity from task memorization.
