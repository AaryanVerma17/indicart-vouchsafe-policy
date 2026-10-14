"""IndicArt policy v2 (submission entry point). Standard library only; reads only the JSON request.

Ask phase : (1) spend up to SOFT_UNITS/day on `relationship_goal` for members who already have a feasible
            partner (1 unit each); (2) spend the rest on `constraints` bundles for members who would unlock
            the most potential partners.
Match phase: score feasible pairs (goal agreement weighted highest, weights taken from the public training
            pools), take non-overlapping pairs greedily, then re-validate every pair before returning it.
Safety    : any internal error returns an empty (valid) action. The --baseline flag is accepted and ignored
            so the official local runner can launch this file; baselines live in policy.py.
"""
import argparse, itertools, json, sys
from kit import HARD, eligibility

SOFT_UNITS = 6
WEIGHTS = {'relationship_goal': 1.0, 'relationship_pace': 0.6, 'lifestyle': 0.3, 'conversations': 0.3,
           'emotional_availability': 0.1, 'space_for_relationship': 0.1, 'relocate': 0.1}


def _key(a, b):
    return tuple(sorted((a, b)))


def _past(state):
    return {_key(i['user_a'], i['user_b']) for i in state['introductions']}


def _hard_declined(m):
    return any(m['field_status'][k] == 'declined' for k in HARD)


def _feasible_degree(avail, past):
    deg = {m['member_id']: 0 for m in avail}
    for a, b in itertools.combinations(avail, 2):
        if _key(a['member_id'], b['member_id']) in past:
            continue
        if eligibility(a, b)['status'] == 'feasible':
            deg[a['member_id']] += 1
            deg[b['member_id']] += 1
    return deg


def _constraint_asks(avail, past, bundles):
    avail = [m for m in avail if not _hard_declined(m)]  # a declined member can never be unlocked
    askable = [m for m in avail if any(m['fields'][k] is None for k in HARD)]
    ids = {m['member_id'] for m in askable}
    gain = {}
    for m in askable:
        g = 0.0
        for o in avail:
            if o is m or _key(m['member_id'], o['member_id']) in past:
                continue
            e = eligibility(m, o)
            if e['status'] == 'infeasible':
                continue  # a known failure beats missing information
            blockers = {x.split(':')[0] for x in e['missing']}
            if blockers <= {m['member_id']}:
                g += 0.5 if o['member_id'] in ids else 1.0
            else:
                g += 0.25
        gain[m['member_id']] = g
    order = sorted(askable, key=lambda m: (-gain[m['member_id']], m['member_id']))
    return [{'member_id': m['member_id'], 'field': 'constraints'}
            for m in order[:bundles] if gain[m['member_id']] > 0]


def choose_asks(state):
    budget = state['ask_budget_remaining']
    avail = [m for m in state['members'] if m['available']]
    past = _past(state)
    deg = _feasible_degree(avail, past)
    cand = [m for m in avail if m['fields']['relationship_goal'] is None
            and m['field_status']['relationship_goal'] != 'declined' and deg[m['member_id']] > 0]
    cand.sort(key=lambda m: (-deg[m['member_id']], m['member_id']))
    soft = min(SOFT_UNITS, budget, len(cand))
    asks = [{'member_id': m['member_id'], 'field': 'relationship_goal'} for m in cand[:soft]]
    asks += _constraint_asks(avail, past, (budget - soft) // 3)
    return asks


def pair_score(a, b):
    s = 0.0
    for k, w in WEIGHTS.items():
        x, y = a['fields'].get(k), b['fields'].get(k)
        if x is not None and y is not None:
            s += w if x == y else -0.3 * w
    return s


def choose_pairs(state):
    members = {m['member_id']: m for m in state['members']}
    avail = [m for m in state['members'] if m['available']]
    past = _past(state)
    edges = []
    for a, b in itertools.combinations(avail, 2):
        k = _key(a['member_id'], b['member_id'])
        if k not in past and eligibility(a, b)['status'] == 'feasible':
            edges.append((-pair_score(a, b), k))
    used, out = set(), []
    for _, (x, y) in sorted(edges):
        if x in used or y in used:
            continue
        # final guard: re-check everything before committing the pair
        if members[x]['available'] and members[y]['available'] and eligibility(members[x], members[y])['status'] == 'feasible':
            out.append([x, y])
            used.update((x, y))
    return out


def valid_asks(state, asks):
    avail = {m['member_id'] for m in state['members'] if m['available']}
    seen, cost, out = set(), 0, []
    for a in asks:
        c = 3 if a['field'] == 'constraints' else 1
        if a['member_id'] in avail and (a['member_id'], a['field']) not in seen and cost + c <= state['ask_budget_remaining']:
            seen.add((a['member_id'], a['field'])); cost += c; out.append(a)
    return out


def decide(request):
    state, memory = request['state'], request.get('memory') or {}
    try:
        if request['phase'] == 'ask':
            return {'asks': valid_asks(state, choose_asks(state)), 'memory': memory}
        return {'pairs': choose_pairs(state), 'memory': memory}
    except Exception as exc:  # never crash an episode; waiting is always valid
        print('indicart: fell back to no action: %r' % (exc,), file=sys.stderr)
        return {'asks': [], 'memory': memory} if request.get('phase') == 'ask' else {'pairs': [], 'memory': memory}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--baseline', default='greedy', help='accepted for runner compatibility; ignored')
    parser.parse_args()
    print(json.dumps(decide(json.load(sys.stdin)), allow_nan=False))
