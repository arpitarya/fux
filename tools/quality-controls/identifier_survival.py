#!/usr/bin/env python3
"""W-168 step 2 — do identifiers survive the analyzer, and can the corpus test it?

**A precondition check, not an arm.** [The proposal](../../work/proposals/search-improvements-v3.md)
§0 is explicit: *"Build the golden question before the feature, or the verdict is
theatre."* So this asks two questions before anything is built:

1. **Does the analyzer actually mangle identifiers?** Idea #3 asserts *"the
   stemmer mangles ids"*. An assertion is not a measurement, and a feature built
   on a premise nobody checked is the W-83 class.
2. **Can this corpus test the fix?** [SR-RS](../../records/0133_predictions.md)
   decision 23: test data must contain the input the feature acts on, and
   **missing input is a data defect, not a null** — the lesson
   [W-191](../../work/open/W-191-the-ladder-carries-no-links.md) cost a whole
   measurement to learn.

It reads `work/golden/seed/` and the **ids and question text** of
`work/golden/questions/` — both of which
[SR-WORK-GOLDEN](../../records/0066_WORK-golden.md) decision 2 permits — and
nothing else under `work/golden/`.

    python3 tools/quality-controls/identifier_survival.py --json-out out.json
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

#: Identifier SHAPES, as the proposal names them: `W-146`, `SR-GRAPH`,
#: `ERR_2031`, versions. Deliberately conservative — it is looking for the
#: population the feature would serve, not every token with a digit in it.
ID_RE = re.compile(
    r"\b(?:[A-Z]{2,}[-_][A-Z0-9]+(?:[-_][A-Z0-9]+)*|[A-Z]{2,}\d+|v?\d+\.\d+\.\d+)\b"
)


def survives(token: str) -> tuple[bool, list[str]]:
    """Does `token` come out of the analyzer whole? Returns `(whole, tokens)`."""
    from fux.query.tokenize import tokenize

    out = tokenize(token)
    return (out == [token.lower()], out)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--seed", type=Path, default=ROOT / "work" / "golden" / "seed")
    ap.add_argument("--questions", type=Path, default=ROOT / "work" / "golden" / "questions")
    ap.add_argument("--json-out", type=Path)
    args = ap.parse_args(argv)

    # ---- 1 · the corpus's identifier inventory ------------------------------
    counts: collections.Counter[str] = collections.Counter()
    docs = 0
    for path in sorted(args.seed.rglob("*")):
        if path.is_file():
            docs += 1
            counts.update(ID_RE.findall(path.read_text(encoding="utf-8", errors="replace")))

    # ---- 2 · what the analyzer does to each ---------------------------------
    whole, split, mangled = [], [], []
    for token in sorted(counts):
        ok, out = survives(token)
        if ok:
            whole.append(token)
        else:
            split.append((token, out))
            # 🔴 **MANGLED is stronger than SPLIT**, and the difference decides
            # how bad this is. Split means the parts survive and a query can
            # still match them; mangled means a part came out as a string the
            # document does not contain — the stemmer ate a letter — so no query
            # spelled the way a person spells it can reach that piece.
            #
            # ⚠ **Compared against the token's PARTS, not against the whole
            # lowercased string.** A substring test looks right and silently
            # passes the worst cases: `kf` IS a substring of `kfs-2014`, so
            # `KFS-2014 -> ['kf', '2014']` would read as a clean split when the
            # `S` is gone. Splitting on the separators first is what makes the
            # check see it.
            parts = {p for p in re.split(r"[-_.]", token.lower()) if p}
            if any(p.isalpha() and p not in parts for p in out):
                mangled.append((token, out))

    # ---- 3 · can the questions exercise it? ---------------------------------
    per_set = {}
    for path in sorted(args.questions.glob("set-*.jsonl")):
        rows = [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]
        hits = [(r["id"], ID_RE.findall(r["question"])) for r in rows]
        with_id = [(qid, t) for qid, t in hits if t]
        per_set[path.stem] = {"questions": len(rows), "with_identifier": len(with_id),
                              "ids": [q for q, _ in with_id]}

    print(f"{docs} seed documents: {sum(counts.values())} identifier tokens, "
          f"{len(counts)} distinct\n")
    print(f"{'analyzer outcome':>22}  count")
    print(f"{'survives whole':>22}  {len(whole)}")
    print(f"{'split into parts':>22}  {len(split)}")
    print(f"{'MANGLED (a letter lost)':>22}  {len(mangled)}\n")

    for token, out in split[:12]:
        flag = "   🔴 MANGLED" if (token, out) in mangled else ""
        print(f"  {token:<14} -> {out}{flag}")
    if len(split) > 12:
        print(f"  … {len(split) - 12} more")

    print(f"\n{'question set':>14}  {'questions':>9}  {'with an identifier':>18}")
    total_q = total_id = 0
    for name, d in per_set.items():
        print(f"{name:>14}  {d['questions']:>9}  {d['with_identifier']:>18}")
        total_q += d["questions"]
        total_id += d["with_identifier"]
    print(f"{'TOTAL':>14}  {total_q:>9}  {total_id:>18}")

    if total_id < 6:
        print(f"\n🔴 {total_id} id-bearing questions is BELOW SR-RS decision 19's floor of all")
        print("   floors (a net of 6). No arm on this set can clear alpha at any split,")
        print("   so the feature cannot be given a verdict here — a DATA DEFECT (d23b),")
        print("   fixed in the data, never filed as a null.")

    if args.json_out:
        args.json_out.write_text(json.dumps({
            "seed_documents": docs,
            "identifier_tokens": sum(counts.values()),
            "distinct": len(counts),
            "survives_whole": whole,
            "split": [{"token": t, "tokens": o} for t, o in split],
            "mangled": [{"token": t, "tokens": o} for t, o in mangled],
            "questions": per_set,
        }, indent=2, sort_keys=True), encoding="utf-8")
    # Non-zero when the questions cannot power a verdict, so this gates.
    return 0 if total_id >= 6 else 2


if __name__ == "__main__":
    raise SystemExit(main())
