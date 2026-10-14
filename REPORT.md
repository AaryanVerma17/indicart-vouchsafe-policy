# IndicArt: goal-aware clarification for consent-first sequential matching

Team **IndicArt** (Aaryan Verma, solo) · CRSU x Romeo & Juliet Hackathon 2026, Round 2 · Synthetic simulator only.

## 1. Summary
- **Hypothesis.** In this simulator most value comes from *getting the information needed to make an introduction feasible and well-matched*, not from clever pairing. I test whether spending spare clarification budget on `relationship_goal` (1 unit, the only soft field that clearly predicts acceptance in the public training pools) improves outcomes over the starter's clarification and scoring.
- **Policy.** `indicart.py`: reciprocal feasibility gate (`kit.eligibility`), targeted constraint clarification, cheap goal clarification, goal-weighted greedy allocation, final validity guard. Standard library only; no learned model.
- **Result.** Clarification is decisive: every policy that asks scores about 4x the no-clarification baseline. On 30 untouched held-out seeds, IndicArt's MSMI is *not* significantly above greedy (+0.017 per 100, 95% CI -0.056 to +0.089); its mutual-acceptance rate is slightly but reliably higher (+0.219 per 100, CI +0.039 to +0.400). An earlier, larger-looking MSMI gain on the tuning seeds (+0.092, CI +0.014 to +0.167) did not replicate at the same size, so I treat it as partly chance.
- **Safety.** 0 invalid episodes in every run reported here, including the official evaluator and the offline container check.

## 2. Problem interpretation and decision objective
The policy is decision support: it proposes clarification requests and feasible introductions; people approve. Each day it chooses (a) asks within 12 budget units (`constraints` bundle = 3, one soft field = 1) and (b) a set of non-overlapping, never-repeated, mutually feasible pairs. The objective is MSMI per 100 arrived members (mutual second-meeting intention within the official windows), averaged equally over the six scenario families; ties go to coverage, mutual acceptances, ask cost and runtime. Hard constraints are never traded off: missing is not a pass, a known failure always wins over missing data, declined answers are never re-asked or imputed.

## 3. Observations, missingness and leakage
At each decision the policy sees only the JSON request: arrived members, observed/declined/not-asked fields, past introductions, visible feedback (response, date, second-meeting events with their observation days) and `ask_budget_remaining`. It receives no seed, future arrivals, truth fields, biases or response rates, and does not read the simulator source at run time. The simulator code was read only to design experiments; no constant from it is hard-coded in the policy. Feedback is delayed and selective (about 39 missing responses per episode); the final policy does not train on feedback online (a variant that did, v4, is reported as a negative result). Declined hard fields permanently exclude a member from introductions, which caps coverage.

## 4. Method (`indicart.py`)
1. **Gate.** Candidate pairs = available, not previously introduced, `eligibility == feasible`.
2. **Clarification.** Up to 6 units/day ask `relationship_goal` for members who already have at least one feasible partner (most candidates first). Remaining budget buys `constraints` for the members whose answers unlock the most potential partners (partners who are already complete count fully, partners also missing data count half; members who declined any hard field are skipped).
3. **Allocation.** Score = weighted agreement over observed soft fields (goal 1.0, pace 0.6, lifestyle 0.3, conversations 0.3, others 0.1; disagreement costs 0.3x weight); non-overlapping pairs taken greedily by score.
4. **Guard.** Every pair/ask is re-validated; any exception returns an empty (valid) action. No memory and no randomness.

Weights come from tabulating acceptance by field agreement in the six *training* pools (`public_01`-`06`): goal agreement 0.65 vs 0.44 acceptance, other fields little or no effect. Validation and development-test pools were not used. No training compute is required; assets: none.

## 5. Experimental design
Same simulator, same metrics as `evaluate.py`, run in-process by `fast_eval.py` (resumable, identical episode loop; 60 decision days then 40 follow-up days). Seeds 101-108 debugging; **201-230 tuning and ablations**; **301-330 held-out confirmation** (no decision used them). All six scenarios, 30 seeds each. Differences are *paired* (same world per seed and scenario) with a 4,000-draw bootstrap 95% interval (`compare.py`), scenarios weighted equally. MSMI events are rare (about 0.9 per episode of roughly 190 arrived members), so single-seed numbers are noisy; mutual acceptances (about 11 per episode) are used as a denser diagnostic and are reported next to MSMI, never instead of it.

## 6. Results on held-out seeds 301-330 (6 scenarios x 30 seeds = 180 episodes per method)
| Method | MSMI/100 (primary) | Mutual acc./100 | Coverage | Ask cost | Mean wait (days)* | Invalid |
|---|---|---|---|---|---|---|
| no_asks | 0.103 | 1.48 | 0.12 | 0 | 3.7 | 0 |
| random-feasible | 0.411 | 5.39 | 0.35 | 199 | 6.8 | 0 |
| greedy | 0.450 | 5.36 | 0.35 | 199 | 6.7 | 0 |
| **IndicArt** | **0.467** | **5.58** | 0.35 | 217 | 6.2 | 0 |

*Wait = days from arrival to first introduction, among members who were introduced. Unserved members (never introduced by day 59): no_asks 0.88, greedy/random/IndicArt 0.65.

Per scenario (MSMI/100): 
| Scenario | no_asks | random | greedy | IndicArt |
|---|---|---|---|---|
| development | 0.150 | 0.450 | 0.583 | 0.617 |
| sparse | 0.017 | 0.150 | 0.133 | 0.167 |
| cold_start | 0.067 | 0.533 | 0.400 | 0.383 |
| delayed | 0.133 | 0.467 | 0.467 | 0.533 |
| shift | 0.100 | 0.433 | 0.533 | 0.533 |
| drift | 0.150 | 0.433 | 0.583 | 0.567 |

Outcome funnel per episode (mean over 180): 
| Method | Introductions | Mutual acceptances | Dates | MSMI events | Missing responses |
|---|---|---|---|---|---|
| no_asks | 21.3 | 3.0 | 2.3 | 0.21 | 11.1 |
| random | 75.8 | 10.8 | 8.5 | 0.82 | 40.3 |
| greedy | 75.1 | 10.7 | 8.6 | 0.90 | 40.3 |
| IndicArt | 74.7 | 11.2 | 8.5 | 0.93 | 39.1 |

Paired differences, IndicArt minus greedy: MSMI +0.017 (CI -0.056, +0.089); mutual acceptances +0.219 (CI +0.039, +0.400); coverage +0.001 (CI 0.000, +0.002). IndicArt minus random: MSMI +0.056 (CI -0.025, +0.136); mutual +0.189 (CI -0.003, +0.369). **Honest reading:** asking is what matters; IndicArt's edge over greedy on the official score is small and not established, and greedy and random are statistically indistinguishable. Per-scenario differences are within noise (about 0.5 MSMI events per scenario-seed). Runtime: slowest single call under 1.6 s with four episodes running concurrently (limit 10 s).

**Official evaluator (`evaluate.py`, seeds 101, 102, 103; all six scenarios; 18 episodes per method; every run `eligible: true`, 0 invalid).**
| Method | Primary score (MSMI/100) | MSMI events (of 18 episodes) | Coverage | Mutual acc./100 | Ask cost | Inference s/episode* |
|---|---|---|---|---|---|---|
| no_asks | 0.1389 | 5 | 0.143 | 1.75 | 0 | 23.5 |
| random-feasible | 0.2778 | 10 | 0.377 | 5.33 | 206.7 | 22.1 |
| greedy | 0.3889 | 14 | 0.372 | 5.50 | 206.7 | 18.2 |
| IndicArt | 0.3056 | 11 | 0.373 | 6.72 | 227.3 | 24.6 |

*Mean inference time per episode as reported by the official evaluator (`inference_seconds`), measured on my development machine; the per-call limit is 10 s and the slowest call I observed was under 1.6 s.

Official scenario means, MSMI/100 (IndicArt / greedy / random / no_asks): development 0.333 / 0.500 / 0.333 / 0.167; sparse 0.000 / 0.167 / 0.167 / 0.000; cold_start 0.167 / 0.167 / 0.167 / 0.000; delayed 0.667 / 0.500 / 0.167 / 0.333; shift 0.333 / 0.500 / 0.500 / 0.167; drift 0.333 / 0.500 / 0.333 / 0.167. Each scenario mean is only three episodes, so a single event changes it by 0.167.

On these three seeds IndicArt scored 11 successful second-meeting outcomes against greedy's 14: below greedy, the opposite sign to the 30-seed held-out run. A difference of three events across 18 episodes is well within chance, and I report it unadjusted rather than choosing the more favourable run. IndicArt again has the highest mutual-acceptance rate (6.72 vs 5.50 greedy, 5.33 random). Taken together: asking matters a great deal (no_asks is the clear loser in every run); goal-aware asking gives a small, consistent gain in mutual acceptance; any gain in MSMI over greedy is unproven.

**Offline container check.** The submission image built from the committed `Dockerfile` (entry point `indicart.py`) was run by the organisers' container runner (`evaluate.py --image`, no network, no host mounts) in GitHub Actions on Python 3.12 and 3.10 runners: seed 101, development scenario, `valid: true`, MSMI 0.5, coverage 0.465, mutual acceptances 12.0 per 100, ask cost 221. These match the local (non-container) run on the same seed exactly, which is evidence that the container reproduces the local behaviour. Container inference time for the episode was 48 s (3.12 runner) and 52 s (3.10 runner); it is higher than locally because each call starts a fresh container process on a shared CI runner. Artifacts: `container.json` for each runner.

## 7. Ablations (tuning seeds 201-230, 180 paired episodes each unless noted)
| Change tested | Hypothesis | MSMI/100 diff (95% CI) | Mutual diff | Verdict |
|---|---|---|---|---|
| v1 vs greedy: order who is asked by unlock value, goal-weighted scoring | Asking the most useful members first speeds up clarification | 0.317 vs 0.311 (no CI run) | none | no effect: both ask the same members eventually (coverage 0.32 each) |
| **v2 vs greedy: add goal asks (<=6 units/day)** | Knowing `relationship_goal` lets scoring pick better pairs | **+0.092 (+0.014, +0.167)** | +0.100 (-0.131, +0.317) | helped on tuning seeds; held-out gain smaller (Section 6) |
| v2 vs v2a: custom weights vs starter scoring (both with goal asks) | Weights matter | -0.003 (-0.056, +0.053) | -0.039 | no difference: the gain comes from asking, not from the weights |
| v3 vs v2: hold back pairs whose known goals disagree (waiting) | Waiting for better pairs improves quality | **-0.067 (-0.122, -0.011)** | -0.961 (-1.150, -0.781) | hurts: coverage falls 0.044 and fewer introductions outweigh quality |
| v2u12 vs v2: allow 12 goal-ask units/day | More information is better | -0.011 (-0.028, +0.003) | +0.025 | no benefit: spare budget is not the limit |
| v4 vs v2: learn member acceptance/response propensity from feedback | Reliable members convert better | **-0.092 (-0.139, -0.044)** | 0.000 | hurts: little history per member and acceptance history does not predict second-meeting intention here (unverified explanation) |

Takeaway for the causal claim: the improvement over the starter is attributable to *information* (goal clarification feeding the pair score), not to the allocation rule or to waiting. Global matching was not built: on identical states, greedy produced 57/87/116 pairs vs a maximum of 60/88/125 (development, three seeds) and identical counts in sparse, so at most about 8% more introductions were available.

## 8. Failure analysis
- **Sparse supply.** With 12 zones, reciprocal zone and schedule overlap leave few feasible pairs: coverage is 0.18 vs 0.40 in development for every policy. Clarification cannot create compatibility; IndicArt's 0.167 vs greedy 0.133 is a difference of a fraction of one event per episode.
- **Withheld answers.** A declined hard field is final, so those members are never introduced and are excluded from the ask list; this, plus infeasible pairs, is why coverage stays near 0.35-0.40 however well asks are targeted. Unserved members are about 65% of arrivals.
- **Delayed feedback.** The `delayed` scenario postpones dates; the policy does not adapt to feedback, so it is unaffected by delay but also learns nothing from it (v4 tried and failed). IndicArt was ahead of greedy there (0.533 vs 0.467) but within noise.
- **Competition and cold start.** Each person is busy for at least 8 days after an introduction, so early days are decisive; with only 20% complete profiles at start (`cold_start`) IndicArt and greedy both fall on MSMI (0.383 vs 0.400, no difference) because asks, not scoring, dominate.
- **Shift and drift.** Scoring weights are fixed from training data. In `shift` (soft-field importance changes) and `drift` (acceptance declines from day 35) IndicArt matched or trailed greedy within noise; no adaptation mechanism was shown to help.
- **Low event counts.** About 0.9 MSMI events per episode means MSMI-based claims need many seeds; I report intervals and use mutual acceptance only as a diagnostic.

## 9. Limitations
Everything is invented: zones, answer behaviour, immediate clarification, acceptance and second-meeting models. The goal-agreement effect is a property of this simulator, learned from its public pools; it says nothing about real people. The MSMI improvement over greedy is not statistically established. The policy was selected among a small set of variants on tuning seeds, then confirmed once on held-out seeds.

## 10. Product integration note
- **Consent checks.** The policy only proposes pairs that pass reciprocal hard constraints on *current* server-side state, re-validated by the adapter before display; a declined answer is stored as declined and never re-asked, imputed or inferred.
- **Human approval.** Output is a suggestion list; nobody is contacted, and no introduction happens without both people choosing to accept.
- **Explanations.** Each suggestion would state the shared basis in plain words (for example "you both said you are looking for something long-term") without revealing the other person's private answers beyond what they agreed to share, and allow correction or rejection.
- **Data minimisation.** Clarification is asked only when it can unlock a feasible partner, and the cheap goal question is preferred to the full constraints bundle where it suffices; policy IDs are opaque and short-lived.
- **Failure monitoring.** Track invalid-action rate (target zero), runtime, acceptance and second-meeting rates by cohort, share of unserved and declined members, and drift in acceptance; alert on shifts and fall back to no action.
- **To validate before any Vouchsafe use.** Whether goal agreement predicts acceptance with real people; real clarification latency and refusal behaviour; fairness of who is left unserved; wording of explanations; legal and consent review. No commercial licence to this code is implied.

## 11. Reproducibility, provenance and AI use
Commands, versions and seeds are in `README.md`. Python 3.12, standard library only; Docker base `python:3.12.7-slim`; no network, GPU or training compute. Data: organisers' synthetic pools (training pools used only for the weight tabulation). Code: organisers' starter (`kit.py`, `evaluate.py`, `policy.py`, tests, unmodified) plus my files. The policy, experiment tools and this report were developed with assistance from Claude (Anthropic) as a coding and writing aid; I ran every experiment, checked the numbers against the saved result files and am responsible for the content. Starter licences: `LICENSE`, `DATA_LICENSE.md`; my additions are released under the MIT licence in `LICENSE_INDICART.md` (the organisers' `LICENSE` covers the starter and states that it does not automatically cover student submissions).
**Evaluator validation:** Our evaluator reproduces the organisers’ reference results for the `greedy`, `random`, and `no_asks` baselines on seed 101 across all six scenarios, with identical `action_sha256` hashes and matching evaluation metrics. All evaluated episodes were valid and eligible.