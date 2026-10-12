"""IndicArt v1: targeted clarification + soft-agreement scoring. Stdlib only; no hidden state."""
import argparse, itertools, json, sys
from kit import HARD, SOFT, eligibility

def _past(state):
    return {tuple(sorted((i['user_a'], i['user_b']))) for i in state['introductions']}

def _hard_declined(m):
    return any(m['field_status'][k] == 'declined' for k in HARD)

def choose_asks(state):
    """Spend constraint bundles where they unlock the most potential partners per unit cost."""
    budget = state['ask_budget_remaining'] // 3
    if budget <= 0: return []
    avail = [m for m in state['members'] if m['available'] and not _hard_declined(m)]
    past = _past(state)
    askable = [m for m in avail if any(m['fields'][k] is None for k in HARD)]
    gain = {}
    for m in askable:
        g = 0
        for o in avail:
            if o is m or tuple(sorted((m['member_id'], o['member_id']))) in past: continue
            e = eligibility(m, o)
            if e['status'] == 'infeasible': continue  # known failure beats missing
            # unlock only if m's missing fields are the sole blocker or o is complete
            blockers = {x.split(':')[0] for x in e['missing']}
            if blockers <= {m['member_id']} or not blockers:
                g += 1 if o not in askable else 0.5
            else:
                g += 0.25
        gain[m['member_id']] = g
    order = sorted(askable, key=lambda m: (-gain[m['member_id']], m['member_id']))
    return [{'member_id': m['member_id'], 'field': 'constraints'}
            for m in order[:budget] if gain[m['member_id']] > 0]

def pair_score(a, b):
    s = 0.0
    w = {'relationship_goal': 1.0, 'relationship_pace': 0.6, 'lifestyle': 0.3, 'conversations': 0.3,
         'emotional_availability': 0.1, 'space_for_relationship': 0.1, 'relocate': 0.1}
    for k, wk in w.items():
        x, y = a['fields'].get(k), b['fields'].get(k)
        if x is not None and y is not None:
            s += wk if x == y else -0.3 * wk
    return s

def choose_pairs(state):
    avail = [m for m in state['members'] if m['available']]
    past = _past(state); edges = []
    for a, b in itertools.combinations(avail, 2):
        key = tuple(sorted((a['member_id'], b['member_id'])))
        if key in past or eligibility(a, b)['status'] != 'feasible': continue
        edges.append((-pair_score(a, b), key))
    used, out = set(), []
    for _, p in sorted(edges):
        if not used.intersection(p):
            out.append(list(p)); used.update(p)
    return out

def decide(request):
    state, memory = request['state'], request.get('memory') or {}
    if request['phase'] == 'ask':
        return {'asks': choose_asks(state), 'memory': memory}
    return {'pairs': choose_pairs(state), 'memory': memory}

if __name__ == '__main__':
    print(json.dumps(decide(json.load(sys.stdin)), allow_nan=False))
