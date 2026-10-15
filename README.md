# IndicArt: consent-first sequential matching policy

CRSU x Romeo & Juliet Hackathon 2026, Round 2. Team **IndicArt** (Aaryan Verma, solo).
Everything here is evaluated on the organisers' **synthetic** simulator; results say nothing about real people.

**Documents:** [`REPORT.md`](REPORT.md) (full report) · [`LICENSE_INDICART.md`](LICENSE_INDICART.md) (licence for my own code) · the organisers' original README is kept unchanged [further down](#crsu-x-romeo--juliet-hackathon).

## What the policy does
`indicart.py` is a standard-library-only JSON policy (`python indicart.py`, one request on stdin, one response on stdout). It is decision support: it proposes clarification requests and introductions; people approve.

1. **Feasibility gate.** Only pairs that `kit.eligibility` marks `feasible` are ever introduced. Missing is never treated as a pass; declined answers are never re-asked or imputed.
2. **Clarification.** Each day, up to 6 budget units go to `relationship_goal` (1 unit) for members who already have a feasible partner; the rest buys `constraints` bundles (3 units) for the members whose answers would unlock the most potential partners.
3. **Pair scoring and allocation.** Feasible pairs are scored by soft-field agreement (goal weighted highest, weights chosen from the public *training* pools only) and taken greedily without overlap.
4. **Safety.** Every pair and ask is re-validated before output; any internal error returns an empty (valid) action. Memory is unused. There is no randomness, so the inference random seed is not applicable.

The starter baselines stay in `policy.py` unchanged. `indicart.py` accepts and ignores `--baseline` so the official runner can launch it.

## Headline results (synthetic simulator)
* Clarification is the dominant lever: about 4x the primary score of `no_asks`.
* Held-out, 30 seeds (301-330) x 6 scenarios: IndicArt 0.467 vs greedy 0.450 MSMI per 100 arrived members (paired difference +0.017, 95% CI -0.056 to +0.089, **not established**); mutual acceptances per 100 5.58 vs 5.36 (+0.219, CI +0.039 to +0.400).
* Official evaluator, seeds 101-103: IndicArt 0.306, greedy 0.389, random 0.278, no_asks 0.139 (18 episodes each; differences are within noise). All runs eligible, 0 invalid episodes.
* The baseline runs reproduce the organisers' reference results on seed 101 exactly (identical action hashes).

See `REPORT.md` for scenario-level results, waiting times, ask costs, ablations, limitations and the product-integration note.

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
Larger in-process experiments (identical simulator and metrics, resumable, about 7 s per episode):
```bash
python fast_eval.py run --policies greedy,random,no_asks,mod:indicart --seeds 301-330 --variants all --out results/final_heldout.jsonl --workers 4
python fast_eval.py summary --out results/final_heldout.jsonl --funnel
python compare.py results/final_heldout.jsonl greedy mod:indicart
python check_results.py
```

## Seeds and data splits
* Exploration/debugging: 101-108. Tuning and ablations: 201-230. **Held-out confirmation: 301-330** (the final policy was fixed before these seeds were run).
* Public pools: train `public_01`-`06` (used only for the weight tabulation), validation `07`-`08` and development-test `09`-`10` untouched.

## Results files (all in `results/`)
* `baselines.jsonl`: tuning seeds, all ablation variants.
* `heldout.jsonl`, `final_heldout.jsonl`: held-out runs (seeds 301-330).
* `final.json`: official evaluator, IndicArt, seeds 101-103.
* `official_greedy.json`, `official_random.json`, `official_no_asks.json`: official evaluator, baselines, same seeds and scenarios.
* `container_check_py312.json`, `container_check_py310.json`: offline container checks (seed 101) produced by the organisers' CI workflow on Python 3.12 and 3.10. The `--output results/container_check.json` command above reproduces the same check locally.

## Files
* `indicart.py`: submission policy.
* `fast_eval.py`, `compare.py`, `check_results.py`: experiment, comparison and integrity-check tools.
* `policy_v1.py`, `policy_v2.py`, `policy_v2a.py`, `policy_v2u12.py`, `policy_v3.py`, `policy_v4.py`: ablation variants, kept for reproducibility.
* `Dockerfile`: the organisers' file with two lines changed (it copies `indicart.py` and uses it as the entry point).
* `policy.py`, `kit.py`, `evaluate.py`, `organise.py`, `build_public_data.py`, the tests, `verify_data.py` and `data/` are the organisers' starter, unchanged.

## Provenance and AI use
Starter kit and data: CRSU x Romeo & Juliet organisers (see `LICENSE`, `DATA_LICENSE.md`; my own code is MIT-licensed in `LICENSE_INDICART.md`). The policy and experiment tools were written with assistance from Claude (Anthropic); I ran, checked and take responsibility for them. No external datasets, models or network access. See the report for the full account.

---

# CRSU x Romeo & Juliet Hackathon

*The text below is the organisers' original README, kept unchanged.*

**Participant release 1.0.0 | 5 October 2026 | Vouchsafe-focused synthetic challenge**

Design a consent-first decision-support policy for sequential introductions. The policy must respect each person's stated constraints, work with incomplete preferences and delayed feedback, and leave final decisions to people. Every person, profile, conversation and outcome in this kit is synthetic.

## Start here

1. Read [the problem statement](PROBLEM_STATEMENT.md) or [download its PDF](docs/PROBLEM_STATEMENT.pdf), [data contract](docs/DATA_CONTRACT.md), [policy interface](docs/POLICY_INTERFACE.md) and [submission instructions](docs/SUBMISSION.md).
2. Download this repository with **Code → Download ZIP**, or clone it. The complete synthetic dataset is in `data/`; no Supabase account, API key or separate download is needed.
3. Install Python 3.10 or later. Run:

```bash
python -m unittest -v
python verify_data.py
python evaluate.py --seeds 101 --output results/first_run.json
```

On Windows, use `py` instead of `python` if needed. On macOS/Linux, use `python3` if that is your Python executable. The starter has no external Python dependencies. Results measure this invented simulator only.

## CRSU participation

- **Teams:** 1–3 participants.
- **Round 1 (research and ideation):** 5–9 October 2026; results by 11 October, 22:00 IST.
- **Final build:** 12–18 October 2026.
- **Registration:** complete registration on both [Unstop](https://unstop.com/) and [events.romeojuliet.love](https://events.romeojuliet.love/crsu-hackathon-2026). Complete the event site's voice chat; it issues a participant code. The team leader must enter each team member's issued code while completing registration on Unstop.
- **Mentorship and workshops:** these are not part of the CRSU track.

Use the forthcoming Google Form for Round 1 research submissions. Use the Final submission and Question issue forms linked below for build submissions and technical questions. Event registration or the participant code is handled through Unstop and the event website, not through GitHub.

## What is included

| File / folder | Purpose |
|---|---|
| [PROBLEM_STATEMENT.md](PROBLEM_STATEMENT.md) | Challenge, rules, scoring, schedule and participation terms |
| [data/](data/) | 2,000 synthetic adults across ten disjoint pools |
| [data_manifest.json](data_manifest.json) | Pool counts, generation seeds and train/validation/development-test split |
| [docs/DATA_CONTRACT.md](docs/DATA_CONTRACT.md) | Fields, constraints and feedback rules |
| [docs/POLICY_INTERFACE.md](docs/POLICY_INTERFACE.md) | Executable JSON request/response protocol |
| [policy.py](policy.py) | Greedy, no-clarification and random-feasible baselines |
| [evaluate.py](evaluate.py) | Episode runner, metrics and scenario-level score |
| [build_public_data.py](build_public_data.py) | Rebuild public synthetic tables in a new folder |
| [kit.py](kit.py) | Reproducible simulator and reciprocal eligibility checks |
| [organise.py](organise.py) and [docs/ORGANISER_RUNBOOK.md](docs/ORGANISER_RUNBOOK.md) | Organiser assessment commands and ranking procedure |
| [Dockerfile](Dockerfile) | Offline container packaging for assessed inference |
| [docs/SUBMISSION.md](docs/SUBMISSION.md) | Research and final submission requirements |
| [docs/INTEGRATION.md](docs/INTEGRATION.md) | Safe adapter boundary for later Vouchsafe evaluation |
| [docs/FAQ.md](docs/FAQ.md) | Common questions and communication guidance |
| [examples/](examples/) | Reference baseline results and report guide |

## Develop and compare

Edit `policy.py`, keeping the JSON interface. Use only the observable input state. The evaluator handles refreshed observations after clarification. Policy memory is passed explicitly between calls and reset between episodes.

```bash
python evaluate.py --baseline greedy --seeds 101,102,103 --variants all --output results/greedy.json
python evaluate.py --baseline no_asks --seeds 101,102,103 --variants all --output results/no_asks.json
python evaluate.py --baseline random --seeds 101,102,103 --variants all --output results/random.json
```

The full commands take longer than the quick start. Public variants are `development`, `sparse`, `cold_start`, `delayed`, `shift` and `drift`. Keep the six training pools, two validation pools and two development-test pools disjoint. Day-30 snapshots are not observations from earlier decisions.

To check container execution after installing Docker:

```bash
docker build -t crsu-policy:1.0 .
python evaluate.py --image crsu-policy:1.0 --seeds 101 --output results/container.json
```

Local subprocess mode is only for trusted development code. Assessed submissions use offline containers with no host evaluation files mounted. Private organiser worlds are not included in this repository.

## Submit and ask questions

| Milestone | Date and time (IST) |
|---|---|
| Round 1 research submission closes | 9 October 2026, 23:59 |
| Round 1 results announced by | 11 October 2026, 22:00 |
| Round 2 build starts | 12 October 2026 |
| Final build submission closes | 18 October 2026, 23:59 |

**Round 1:** submit the research note through a Google Form. The organisers will release the link soon through [Discord](https://discord.gg/ka3uRZza6) and [the submission guide](docs/SUBMISSION.md#research-submission). GitHub Issues are not the research submission route.

**Round 2:** use the [Final submission](https://github.com/RomeoJulietLove/CRSU-x-Romeo-Juliet-Hackathon/issues/new?template=final_submission.yml) issue form by the final deadline. Provide the immutable submitted version and required report/results. Use [Question](https://github.com/RomeoJulietLove/CRSU-x-Romeo-Juliet-Hackathon/issues/new?template=question.yml) for technical questions. Never post personal data, access codes or credentials in public issues.

The repository is the technical source of truth. Questions answered through public Issues are visible to all teams. Event announcements and registration reminders are shared through [the CRSU Discord server](https://discord.gg/ka3uRZza6).

## Data and ownership

The dataset contains invented records only. It contains no real Romeo & Juliet member profiles, conversations, contact details, audio or outcomes. Its structure is designed for a hackathon simulator and does not establish that a model predicts real relationship outcomes.

The [starter-code licence](LICENSE) and [synthetic-data licence](DATA_LICENSE.md) cover the supplied materials. Participants retain ownership of their submissions; participation does not give Vouchsafe a commercial licence to student code. Any later product use requires a separate written agreement.