"""W-247: dump `fux.api` results for a fixed call list, as JSON on stdout.

Run it twice with different `PYTHONPATH` (the tree before the split, the tree
after) from inside a snapshot ROOT and diff the two outputs byte for byte:

    PYTHONPATH=OLD/src python library_dump.py --set repo > old.json
    PYTHONPATH=NEW/src python library_dump.py --set repo > new.json
"""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import sys

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from capture import QUERIES  # noqa: E402


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--set", choices=sorted(QUERIES), required=True)
    name = p.parse_args().set
    from fux import open as fux_open

    import pathlib

    pathlib.Path(".fux/runtime/last-cited.json").unlink(missing_ok=True)
    ix = fux_open(".")
    q = QUERIES[name]
    out = []
    err = io.StringIO()
    with contextlib.redirect_stderr(err):
        for text in q["single"]:
            out.append(["find", text, [r.as_dict() for r in ix.find(text)]])
            out.append(["find-top2", text, [r.as_dict() for r in ix.find(text, top=2)]])
            out.append(["ask", text, ix.ask(text).as_dict()])
            out.append(["ask-noband", text, ix.ask(text, band=False, sections=False).as_dict()])
            for refer in (False, True):
                a = ix.answer(text, audit=True, receipt=True, no_refer=not refer)
                out.append(["answer", text, refer, a.as_dict()])
                out.append(["answer-bare", text, refer,
                            ix.answer(text, audit=False, receipt=False, no_refer=not refer, band=True).as_dict()])
        for text, more in q["fused"]:
            out.append(["ask-fused", text, ix.ask(text, queries=more).as_dict()])
        for flags in q["find_flags"]:
            if flags[0] == "--under":
                out.append(["find-under", flags[1], [r.as_dict() for r in ix.find(q["find_query"], under=flags[1])]])
    json.dump({"calls": out, "stderr": err.getvalue()}, sys.stdout, indent=1, sort_keys=False)
    return 0


if __name__ == "__main__":
    sys.exit(main())
