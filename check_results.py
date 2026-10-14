"""Integrity check for fast_eval JSONL files: duplicates, missing episodes, invalid runs, identical seed sets.
Usage: python check_results.py results/baselines.jsonl results/final_heldout.jsonl"""
import json, sys, collections
ok = True
for path in sys.argv[1:]:
    rows = [json.loads(l) for l in open(path) if l.strip()]
    keys = collections.Counter((r['policy'], r['variant'], r['seed']) for r in rows)
    dups = [k for k, c in keys.items() if c > 1]
    pols = sorted({r['policy'] for r in rows}); vars_ = sorted({r['variant'] for r in rows})
    seeds = {p: {s for (pp, v, s) in keys if pp == p} for p in pols}
    ref = set.intersection(*seeds.values()) if seeds else set()
    print(f'{path}: {len(rows)} rows, {len(pols)} policies, {len(vars_)} scenarios')
    print('  duplicates:', len(dups), '| invalid episodes:', sum(not r['valid'] for r in rows))
    for p in pols:
        n = sum(1 for k in keys if k[0] == p)
        per = collections.Counter(v for (pp, v, s) in keys if pp == p)
        miss = [(v, c) for v, c in per.items() if c != len(seeds[p]) ] 
        print(f'  {p:18s} episodes {n:4d} seeds {min(seeds[p])}-{max(seeds[p])} ({len(seeds[p])})', '' if not miss else f'UNEVEN {miss}')
        ok &= (n == len(seeds[p]) * len(vars_))
    ok &= not dups
print('ALL CHECKS PASSED' if ok else 'PROBLEM FOUND')
