"""IndicArt v2: v1 targeted constraint asks + cheap relationship_goal asks + goal-weighted scoring.
Weights justified by training pools (analysis: goal agreement 0.65 vs 0.44 acceptance). Stdlib only."""
import itertools, json, sys
from kit import HARD, eligibility
from policy_v1 import _past, _hard_declined, pair_score

SOFT_UNITS = 6   # units/day reserved for goal asks (tunable)

def _feasible_degree(avail, past):
    deg = {m['member_id']: 0 for m in avail}
    for a, b in itertools.combinations(avail, 2):
        if tuple(sorted((a['member_id'], b['member_id']))) in past: continue
        if eligibility(a, b)['status'] == 'feasible':
            deg[a['member_id']] += 1; deg[b['member_id']] += 1
    return deg

def choose_asks(state):
    avail = [m for m in state['members'] if m['available']]
    past = _past(state); budget = state['ask_budget_remaining']
    asks = []
    deg = _feasible_degree(avail, past)
    cand = [m for m in avail if m['fields']['relationship_goal'] is None
            and m['field_status']['relationship_goal'] != 'declined' and deg[m['member_id']] > 0]
    cand.sort(key=lambda m: (-deg[m['member_id']], m['member_id']))
    soft = min(SOFT_UNITS, budget, len(cand))
    for m in cand[:soft]:
        asks.append({'member_id': m['member_id'], 'field': 'relationship_goal'})
    left = budget - soft
    import policy_v1
    st2 = dict(state); st2['ask_budget_remaining'] = left
    asks += policy_v1.choose_asks(st2)
    return asks

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
