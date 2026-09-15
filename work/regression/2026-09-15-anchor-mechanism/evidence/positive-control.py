import sys, pathlib
sys.path.insert(0, "/Users/arpitarya/my_programs/fux/tools/quality-controls")
from anchor_probe import rank, anchor_inventory
corp = pathlib.Path("/private/tmp/claude-501/-Users-arpitarya-my-programs-fux/eceb0af1-b664-464e-82c9-c609eab870a6/scratchpad/anchor-control")
print("inventory:", anchor_inventory(corp))
q = "zarvox throughput ceiling"
print(f"\nquery: {q!r}  (these words appear ONLY in a-linker's link text)")
for w in (0.0, 0.5, 1.0, 2.0, 3.0):
    print(f"  anchor={w:<4} -> {[(loc, round(s,3)) for loc,s in rank(corp, q, w, 5)]}")
