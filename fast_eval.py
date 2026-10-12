"""Fast, resumable in-process experiment runner (development only; final numbers use evaluate.py).
Usage:
  python fast_eval.py run --policies greedy,no_asks,random,mod:policy_v1 --seeds 201-230 --variants all --out results/exp.jsonl --workers 2
  python fast_eval.py summary --out results/exp.jsonl
Policies: greedy | no_asks | random (starter baselines) | mod:<module> (module exposing decide(request)).
Every finished episode is appended to the JSONL file; reruns skip episodes already present."""
import argparse, importlib, json, os, statistics as st, sys, time
from multiprocessing import Pool
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kit import Simulator, generate

ALL = ['development', 'sparse', 'cold_start', 'delayed', 'shift', 'drift']

def seeds_arg(s):
    out = []
    for part in s.split(','):
        if '-' in part:
            a, b = part.split('-'); out += list(range(int(a), int(b) + 1))
        else: out.append(int(part))
    return out

def get_decider(name):
    if name.startswith('mod:'):
        return importlib.import_module(name[4:]).decide
    import policy
    return lambda req: policy.decide(req, name)

def episode(job):
    name, variant, seed = job
    t0 = time.time(); decide = get_decider(name); mem = None
    sim = Simulator(generate(seed, 200, 'evaluation', variant)); valid = True; err = None; calls = []
    try:
        for _ in range(60):
            for phase in ('ask', 'match'):
                req = json.loads(json.dumps({'phase': phase, 'state': sim.observe(), 'memory': mem}))
                c = time.time(); r = json.loads(json.dumps(decide(req), allow_nan=False)); calls.append(time.time() - c)
                mem = r.get('memory')
                if phase == 'ask': sim.resolve_asks(r['asks'])
                else: sim.advance(r['pairs'])
        for _ in range(40): sim.advance([])
    except Exception as e:
        valid = False; err = repr(e)
    arrived = {i for i, m in sim.members.items() if m['arrived_day'] <= 59}
    n = max(1, len(arrived)); m = sim.metrics()
    first = {}
    for it in sim.introductions:
        for u in (it['user_a'], it['user_b']):
            first.setdefault(u, it['assigned_day'])
    covered = [u for u in arrived if u in first]
    waits = [max(0, first[u] - sim.members[u]['arrived_day']) for u in covered]
    return {'policy': name, 'variant': variant, 'seed': seed, 'valid': valid, 'error': err,
            'msmi_per_100': 100 * m['mutual_second_meeting_intention'] / n,
            'mutual_per_100': 100 * m['mutual_acceptances'] / n, 'coverage': len(covered) / n,
            'ask_cost': m['ask_cost'], 'intros': m['assignments'], 'mean_wait_days': st.mean(waits) if waits else None,
            'max_call_seconds': max(calls) if calls else 0, 'episode_seconds': time.time() - t0}

def done_keys(path):
    keys = set()
    if os.path.exists(path):
        for line in open(path):
            try: r = json.loads(line); keys.add((r['policy'], r['variant'], r['seed']))
            except Exception: pass
    return keys

def run(a):
    variants = ALL if a.variants == 'all' else a.variants.split(',')
    jobs = [(p, v, s) for s in seeds_arg(a.seeds) for v in variants for p in a.policies.split(',')]
    have = done_keys(a.out); jobs = [j for j in jobs if j not in have]
    os.makedirs(os.path.dirname(a.out) or '.', exist_ok=True)
    print(f'{len(jobs)} episodes to run ({len(have)} already done)', file=sys.stderr)
    t = time.time()
    with open(a.out, 'a') as f, Pool(a.workers) as pool:
        for i, r in enumerate(pool.imap_unordered(episode, jobs), 1):
            f.write(json.dumps(r) + '\n'); f.flush()
            if i % 10 == 0 or i == len(jobs): print(f'  {i}/{len(jobs)}  {time.time()-t:.0f}s', file=sys.stderr)

def summary(a):
    rows = [json.loads(l) for l in open(a.out)]
    print('policy | PRIMARY msmi/100 | mutual/100 | coverage | ask_cost | wait_d | invalid | episodes')
    for p in sorted({r['policy'] for r in rows}):
        per = {}
        for v in ALL:
            rs = [r for r in rows if r['policy'] == p and r['variant'] == v]
            if rs: per[v] = rs
        mean = lambda k: st.mean(st.mean(x[k] for x in rs) for rs in per.values())
        waits = [x['mean_wait_days'] for rs in per.values() for x in rs if x['mean_wait_days'] is not None]
        inv = sum(not x['valid'] for rs in per.values() for x in rs)
        print(f"{p} | {mean('msmi_per_100'):.3f} | {mean('mutual_per_100'):.2f} | {mean('coverage'):.2f} | {mean('ask_cost'):.0f} | {st.mean(waits) if waits else float('nan'):.1f} | {inv} | {sum(len(r) for r in per.values())}")
        for v, rs in per.items():
            print(f"   {v:12s} msmi {st.mean(x['msmi_per_100'] for x in rs):.3f} mutual {st.mean(x['mutual_per_100'] for x in rs):.2f} cov {st.mean(x['coverage'] for x in rs):.2f} n={len(rs)}")

if __name__ == '__main__':
    ap = argparse.ArgumentParser(); sub = ap.add_subparsers(dest='cmd', required=True)
    r = sub.add_parser('run'); r.add_argument('--policies', default='greedy'); r.add_argument('--seeds', default='201-210')
    r.add_argument('--variants', default='all'); r.add_argument('--out', default='results/exp.jsonl'); r.add_argument('--workers', type=int, default=1)
    s = sub.add_parser('summary'); s.add_argument('--out', default='results/exp.jsonl')
    a = ap.parse_args(); run(a) if a.cmd == 'run' else summary(a)
