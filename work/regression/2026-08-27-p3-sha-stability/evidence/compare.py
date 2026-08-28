"""Fraction of fetched URLs whose SANITIZED sha was unchanged between two runs.

`.fux/runtime/url-shas.json` is url -> sanitized sha, written by every `fux
update`. Copy it after each run; this compares two copies. No fux call.
"""
import json, sys
a = json.load(open(sys.argv[1])); b = json.load(open(sys.argv[2]))
keys = sorted(set(a) & set(b))
same = [k for k in keys if a[k] == b[k]]
diff = [k for k in keys if a[k] != b[k]]
print(f"n = {len(keys)} fetched URLs present in both runs")
print(f"sanitized sha UNCHANGED: {len(same)}/{len(keys)} = {len(same)/len(keys):.1%}")
print("changed:" if diff else "changed: none")
for k in diff:
    print("  ", k)
