import itertools, json, sys
import policy_v2
from kit import eligibility
from policy_v1 import _past, pair_score
def choose_pairs(state):
    avail = [m for m in state['members'] if m['available']]
    past = _past(state); edges = []
    for a, b in itertools.combinations(avail, 2):
        key = tuple(sorted((a['member_id'], b['member_id'])))
        if key in past or eligibility(a, b)['status'] != 'feasible': continue
        ga, gb = a['fields']['relationship_goal'], b['fields']['relationship_goal']
        if ga is not None and gb is not None and ga != gb: continue
        edges.append((-pair_score(a, b), key))
    used, out = set(), []
    for _, p in sorted(edges):
        if not used.intersection(p): out.append(list(p)); used.update(p)
    return out
def decide(request):
    state, memory = request['state'], request.get('memory') or {}
    if request['phase'] == 'ask': return {'asks': policy_v2.choose_asks(state), 'memory': memory}
    return {'pairs': choose_pairs(state), 'memory': memory}
if __name__ == '__main__': print(json.dumps(decide(json.load(sys.stdin)), allow_nan=False))
