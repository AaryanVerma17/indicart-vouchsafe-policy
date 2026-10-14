"""Paired comparison of two policies on identical (variant, seed) worlds, with bootstrap CI.
Usage: python compare.py results/baselines.jsonl greedy mod:policy_v2"""
import json, random, statistics as st, sys
path, A, B = sys.argv[1:4]
rows = [json.loads(l) for l in open(path)]
idx = {(r['policy'], r['variant'], r['seed']): r for r in rows}
keys = sorted({(v, s) for (p, v, s) in idx if p == A and (B, v, s) in idx})
VARS = sorted({v for v, _ in keys})
def stat(metric):
    # scenario-weighted mean of paired differences (equal weight per variant, as the official score)
    per = {v: [idx[(B, v, s)][metric] - idx[(A, v, s)][metric] for (vv, s) in keys if vv == v] for v in VARS}
    return per
for metric in ('msmi_per_100', 'mutual_per_100', 'coverage'):
    per = stat(metric)
    point = st.mean(st.mean(x) for x in per.values())
    rnd = random.Random(1); boots = []
    for _ in range(4000):
        boots.append(st.mean(st.mean(rnd.choices(x, k=len(x))) for x in per.values()))
    boots.sort()
    print(f'{metric:15s} {B} - {A}: {point:+.3f}  95% CI [{boots[100]:+.3f}, {boots[3899]:+.3f}]  pairs={len(keys)}')
