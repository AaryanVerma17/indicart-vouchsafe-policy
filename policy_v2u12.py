"""Sensitivity: reserve up to 12 units/day for goal asks."""
import json, sys
import policy_v2
policy_v2.SOFT_UNITS = 12
decide = policy_v2.decide
if __name__ == '__main__': print(json.dumps(decide(json.load(sys.stdin)), allow_nan=False))
