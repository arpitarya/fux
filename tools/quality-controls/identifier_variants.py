#!/usr/bin/env python3
"""W-233 — generate the variant-spelling id-query set for one rung, by rule.

**What a row is.** `{id, family, variant, query, primary}`: an identifier a
rung document contains, one way a person might type it, and the ONE document
that contains it. 🔴 **Not a golden question, no answer, never under
`work/golden/`** — the primary is whichever document holds the string, found by
reading the rung's own text, exactly as W-205's id-queries were
([`identifier_probe.py`](identifier_probe.py)).

**The rule, frozen with the pre-registration** (it decides which queries exist,
so it cannot move after an arm has run):

1. Scan `seed/` and `ext/` of the rung, **skipping any path with an `archive`
   segment** (archived documents rank by a different rule).
2. Every raw analyzer token with a digit, a separator and a **literal letter
   prefix** is grouped by `prefix | shape` — the same grouping the fixture
   used ([`identifier_fixture.py`](identifier_fixture.py) `shape`).
3. A family qualifies at **≥ 3 distinct values in ≥ 2 documents**.
4. Within a family, only values found in **exactly one** document are
   eligible, so the primary is unambiguous; the first `--per-family` of them,
   sorted, are taken.
5. Each id yields these variants, each only when it differs from `exact`:
   `exact` · `space` (every `-`/`_` → a space) · `nosep` (a separator between
   a letter and a digit removed) · `endash` (`-` → U+2013) · `unpadded`
   (leading zeros dropped from every digit run).

    .venv/bin/python tools/quality-controls/identifier_variants.py \\
        --rung rung-01000 --out work/regression/<run>/evidence/variants-rung-01000.jsonl
"""

from __future__ import annotations

import argparse
import collections
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from identifier_fixture import LAB_RUNGS, _raw, shape  # noqa: E402

_DIGIT = re.compile(r"\d")
_SEP = re.compile(r"[-_]")
_PREFIX = re.compile(r"[A-Za-z]+")


def variants(ident: str) -> dict[str, str]:
    out = {"exact": ident}
    out["space"] = re.sub(r"[-_]", " ", ident)
    out["nosep"] = re.sub(r"(?<=[A-Za-z])[-_](?=\d)|(?<=\d)[-_](?=[A-Za-z])", "", ident)
    out["endash"] = ident.replace("-", "–")
    out["unpadded"] = re.sub(r"\d+", lambda m: m.group(0).lstrip("0") or "0", ident)
    return {k: v for k, v in out.items() if k == "exact" or v != ident}


def build(rung: Path, per_family: int) -> list[dict]:
    docs_of: dict[str, set[str]] = collections.defaultdict(set)
    family_of: dict[str, str] = {}
    files = sorted(p for d in ("seed", "ext") for p in (rung / d).rglob("*") if p.is_file())
    for path in files:
        rel = path.relative_to(rung).as_posix()
        if "archive" in rel.split("/"):
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for raw in _raw(text):
            if not (_DIGIT.search(raw) and _SEP.search(raw)):
                continue
            m = _PREFIX.match(raw)
            if not m or "/" in raw or "." in raw:
                continue
            prefix = m.group(0)
            docs_of[raw].add(rel)
            family_of[raw] = f"{prefix}|{shape(raw[len(prefix):])}"
    members: dict[str, list[str]] = collections.defaultdict(list)
    for ident, fam in family_of.items():
        members[fam].append(ident)
    rows = []
    for fam in sorted(members):
        values = members[fam]
        fam_docs = set().union(*(docs_of[v] for v in values))
        if len(values) < 3 or len(fam_docs) < 2:
            continue
        eligible = sorted(v for v in values if len(docs_of[v]) == 1)[:per_family]
        for ident in eligible:
            (primary,) = docs_of[ident]
            for name, query in variants(ident).items():
                rows.append({"id": ident, "family": fam, "variant": name,
                             "query": query, "primary": primary})
    return rows


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--rung", required=True)
    ap.add_argument("--per-family", type=int, default=3)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args(argv)
    rows = build(LAB_RUNGS / args.rung, args.per_family)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n")
    by = collections.Counter(r["variant"] for r in rows)
    print(f"{args.rung}: {len({r['id'] for r in rows})} ids, "
          f"{len({r['family'] for r in rows})} families, {len(rows)} queries — {dict(sorted(by.items()))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
