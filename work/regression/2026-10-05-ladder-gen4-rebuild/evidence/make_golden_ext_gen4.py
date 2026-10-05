#!/usr/bin/env python3
"""fux-lab's UNMODIFIED `make_golden_ext.py`, with the authored documents pair-ordered.

The generator emits its 20 hand-authored documents first, in filename order.
Two of them (a05, a06) declare `supersedes:` on two others (a19, a20) that sort
LAST. Until generation 4 every rung above the seed held all 20, so the pairs
were never split. With 94 seed documents `rung-00100` holds 6 ext documents —
a01…a06 — and the builder refuses the rung: *supersedes: targets not in the
rung*. The generator's own rule for its generated stream is that the retired
half sits immediately before its successor, *"so that a rung boundary can never
admit a `supersedes:` line whose target is not in the rung"*. This wrapper
applies that rule to the authored list and changes nothing else:

    a01 a02 a03 a04 a19 a05 a20 a06 a07 … a18

No document's bytes change. The generated stream is untouched, because the
authored count is still 20. Every rung of 200 or more holds all 20 either way,
so only `rung-00100`'s membership depends on this order.

    python3 make_golden_ext_gen4.py --out <rung-dir> --count N   # as the original
    python3 make_golden_ext_gen4.py --check-closure               # every prefix 1..10000 closed
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path.home() / "my_programs/fux-lab/shared/generate"))
import make_golden_ext as g  # noqa: E402

_authored = g.authored
_SUP = re.compile(r"^supersedes:\s*(\S+)\s*$", re.M)


def authored() -> list[dict]:
    docs = _authored()
    by_path = {d["path"]: d for d in docs}
    targets = {m.group(1) for d in docs for m in _SUP.finditer(d["text"])
               if m.group(1) in by_path}
    out: list[dict] = []
    for d in docs:
        if d["path"] in targets:
            continue  # emitted just before its successor
        for m in _SUP.finditer(d["text"]):
            if m.group(1) in by_path:
                out.append(by_path[m.group(1)])
        out.append(d)
    assert sorted(x["path"] for x in out) == sorted(by_path), "authored set changed"
    return out


g.authored = authored

if __name__ == "__main__":
    if sys.argv[1:] == ["--check-closure"]:
        docs = g.stream(10000)
        have: set[str] = set()
        open_targets = 0
        for n, d in enumerate(docs, 1):
            have.add(d["path"])
            for m in _SUP.finditer(d["text"]):
                if m.group(1) not in have:
                    raise SystemExit(f"FAIL at n={n}: {d['path']} supersedes {m.group(1)}")
        print("OK: every prefix 1..10000 is supersedes-closed")
        print("authored order:", " ".join(Path(d["path"]).name[:3] for d in authored()))
        raise SystemExit(0)
    raise SystemExit(g.main())
