# IndicArt: consent-first sequential matching policy

CRSU x Romeo & Juliet Hackathon 2026, Round 2. Team **IndicArt** (Aaryan Verma, solo).
Everything here is evaluated on the organisers' **synthetic** simulator; results say nothing about real people.

## What the policy does
`indicart.py` is a standard-library-only JSON policy (`python indicart.py`, one request on stdin, one response on stdout).

1. **Feasibility gate.** Only pairs that `kit.eligibility` marks `feasible` are ever introduced. Missing is never treated as a pass; declined answers are never re-asked or imputed.
2. **Clarification.** Each day, up to 6 budget units go to `relationship_goal` (1 unit) for members who already have a feasible partner; the rest buys `constraints` bundles (3 units) for the members whose answers would unlock the most potential partners.
3. **Pair scoring and allocation.** Feasible pairs are scored by soft-field agreement (goal weighted highest, weights chosen from the public *training* pools only) and taken greedily without overlap.
4. **Safety.** Every pair and ask is re-validated before output; any internal error returns an empty (valid) action. Memory is unused. There is no randomness, so the inference random seed is not applicable.

The starter baselines stay in `policy.py` unchanged. `indicart.py` accepts and ignores `--baseline` so the official runner can launch it.

## Environment
Python 3.12 (CI also runs 3.10). No third-party packages (`requirements.txt` is empty). Docker image: `python:3.12.7-slim`.
Training: none. No model is fitted; the soft-field weights come from a one-off tabulation of the six training pools `public_01`-`public_06` (acceptance rate by field agreement). Validation and development-test pools were not used.

## Reproduce
```bash
python -m unittest -v
python verify_data.py
# official evaluator, same seeds and scenarios for all four methods
python evaluate.py --policy policy.py   --baseline greedy   --seeds 101,102,103 --variants all --output results/official_greedy.json
python evaluate.py --policy policy.py   --baseline no_asks  --seeds 101,102,103 --variants all --output results/official_no_asks.json
python evaluate.py --policy policy.py   --baseline random   --seeds 101,102,103 --variants all --output results/official_random.json
python evaluate.py --policy indicart.py                     --seeds 101,102,103 --variants all --output results/final.json
# container check
docker build -t sequential-policy:submission .
python evaluate.py --image sequential-policy:submission --seeds 101 --output results/container_check.json
```
Larger in-process experiments (identical simulator and metrics, resumable, ~7 s per episode):
```bash
python fast_eval.py run --policies greedy,random,no_asks,mod:indicart --seeds 301-330 --variants all --out results/final_heldout.jsonl --workers 4
python fast_eval.py summary --out results/final_heldout.jsonl --funnel
python compare.py results/final_heldout.jsonl greedy mod:indicart
```
## Seeds and data splits
* Exploration/debugging: 101-108. Tuning and ablations: 201-230. **Held-out confirmation: 301-330** (no decision was made using them).
* Public pools: train `public_01`-`06` (used only for the weight tabulation), validation `07`-`08` and development-test `09`-`10` untouched.

## Results files
`results/baselines.jsonl` (tuning seeds, all ablations), `results/heldout.jsonl` and `results/final_heldout.jsonl` (held-out), `results/final.json` and `results/official_*.json` (official evaluator), `results/container_check.json` (offline container; also the CI artifacts `container.json` for Python 3.10 and 3.12).

## Files
`indicart.py` submission policy; `fast_eval.py`, `compare.py` experiment tools; `policy_v1.py`, `policy_v2*.py`, `policy_v3.py`, `policy_v4.py` ablation variants (kept for reproducibility); `policy.py`, `kit.py`, `evaluate.py`, tests and data are the organisers' starter, unmodified.

## Provenance and AI use
Starter kit and data: CRSU x Romeo & Juliet organisers (see `LICENSE`, `DATA_LICENSE.md`; my own code is MIT-licensed in `LICENSE_INDICART.md`). The policy and experiment tools were written with assistance from Claude (Anthropic); I ran, checked and take responsibility for them. No external datasets, models or network access. See the report for the full account.
