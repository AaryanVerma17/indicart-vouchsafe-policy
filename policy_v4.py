import itertools, json, sys
import indicart
from kit import eligibility
K = 6.0          # score units per unit of acceptance probability (goal agree vs disagree = 1.3 score for ~0.21 prob)
PRIOR, STRENGTH = 0.48, 2.0

def propensities(state):
    yes, n, resp, nr = {}, {}, {}, {}
    for e in state['feedback']:
        if e['event'] != 'introduction_response' or e.get('member_id') is None: continue
        m = e['member_id']; n[m] = n.get(m, 0) + 1
        if e['value'] is None: continue
        resp[m] = resp.get(m, 0) + 1
        if e['value'] == 'yes': yes[m] = yes.get(m, 0) + 1
    pa, rr = {}, {}
    for m in n:
        pa[m] = (yes.get(m, 0) + PRIOR * STRENGTH) / (resp.get(m, 0) + STRENGTH)
        rr[m] = (resp.get(m, 0) + 0.8 * STRENGTH) / (n[m] + STRENGTH)
    return pa, rr

def choose_pairs(state):
    members = {m['member_id']: m for m in state['members']}
    avail = [m for m in state['members'] if m['available']]
    past = indicart._past(state); pa, rr = propensities(state); edges = []
    for a, b in itertools.combinations(avail, 2):
        k = indicart._key(a['member_id'], b['member_id'])
        if k in past or eligibility(a, b)['status'] != 'feasible': continue
        s = indicart.pair_score(a, b)
        for x in k:
            s += K * (pa.get(x, PRIOR) - PRIOR) + K * 0.5 * (rr.get(x, 0.8) - 0.8)
        edges.append((-s, k))
    used, out = set(), []
    for _, (x, y) in sorted(edges):
        if x in used or y in used: continue
        out.append([x, y]); used.update((x, y))
    return out

def decide(request):
    state, memory = request['state'], request.get('memory') or {}
    if request['phase'] == 'ask':
        return indicart.decide(request)
    try:
        return {'pairs': choose_pairs(state), 'memory': memory}
    except Exception as exc:
        print('v4 fallback', exc, file=sys.stderr); return indicart.decide(request)
if __name__ == '__main__': print(json.dumps(decide(json.load(sys.stdin)), allow_nan=False))
