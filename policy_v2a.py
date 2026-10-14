"""Ablation: goal asks (v2) but the starter's pair scoring."""
import json, sys
import policy_v2
from kit import baseline_match
def decide(request):
    state, memory = request['state'], request.get('memory') or {}
    if request['phase'] == 'ask': return {'asks': policy_v2.choose_asks(state), 'memory': memory}
    return {'pairs': baseline_match(state), 'memory': memory}
if __name__ == '__main__': print(json.dumps(decide(json.load(sys.stdin)), allow_nan=False))
