#!/usr/bin/env python3
"""G4 — no document's section contribution exceeds its best section scored as a document. Read-only.

W-278 DoD 3's construction check, **no key**. Frozen by hash in
`PRE-REGISTRATION.md` §Freeze before the generation-6 ladder exists and before
any arm. Run with the PINNED engine's interpreter, so the engine it imports is
the one the arms ran:

    <pinned venv>/bin/python g4.py --tree <sw-1.0 copy> \\
        --questions work/golden/questions/set-7-claude.jsonl > evidence/g4/g4.json

For every question and every candidate document the engine scores, the
engine's own `(section, contribution)` (the `--why` seam, `stats_out`) is held
against an **independent re-derivation from the committed shards**: the
parent's and every section's whole line `json.loads`-ed — not the scan's byte
patterns — and each own-matching section built as SR-SECTIONS decision 5 says
(its body and heading slots, the parent's title, path and ctx slots and their
lengths), scored on the document `df`, `n` and `avg_wlen`. Four conditions:

1. **bound** — `contribution <= S_sec*` of the named section;
2. **max form** — at `λ = 1`, `S_doc' + contribution` equals the best
   `S_sec*` (relative 1e-9) whenever a section is named;
3. **nothing missed** — when no section is named, no own-matching section's
   `S_sec*` exceeds `S_doc'`;
4. **the right section** — the named one is the best, ties to the lowest `k`.

It reads `id` and `question` from the released question file and nothing else
under `work/golden/` (SR-WORK-GOLDEN decision 2). It prints no question text.
It opens no key and runs no scorer. JSON to stdout only.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from fux import store, tune as tune_mod
from fux.query import identifiers as ids_mod
from fux.query import scan
from fux.query.bm25f import score_record

REL = 1e-9


def sections_by_parent(root: Path) -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = {}
    for path in store.iter_section_paths(root):
        for line in path.read_bytes().split(b"\n")[1:]:
            if line:
                rec = json.loads(line)
                out.setdefault(store.section_parent(rec["id"]), []).append(rec)
    return out


def close(a: float, b: float) -> bool:
    return abs(a - b) <= REL * max(1.0, abs(a), abs(b))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("--tree", type=Path, required=True)
    ap.add_argument("--questions", type=Path, required=True)
    args = ap.parse_args()

    root = args.tree.resolve()
    tune = tune_mod.load(root, enabled=True)
    scoring = tune.scoring
    lam = scoring.section
    if not 0 < lam <= 1:
        raise SystemExit(f"refusing: section_weight is {lam}; G4 runs on an arm with the term on")
    ids = ids_mod.for_root(root)
    secs_of = sections_by_parent(root)
    slots = store.SECTION_SLOTS
    rows = [json.loads(l) for l in args.questions.read_text(encoding="utf-8").splitlines() if l.strip()]

    checked = named = 0
    failures: list[dict] = []
    for row in rows:
        hashes = scan.query_term_hashes(row["question"], ids)
        if not hashes:
            continue
        candidates, df, corpus = scan.scan_candidates(root, hashes, scoring=scoring)
        stats: dict = {}
        scan.ask(root, row["question"], len(candidates) + 1, scoring=scoring, stats_out=stats)
        engine = stats.get("sections", {})
        for parent in candidates:
            if not parent.get("nsec"):
                continue
            checked += 1
            pid = parent["id"]
            terms, flen = parent.get("terms", {}), list(parent.get("flen", []))
            s_doc = score_record(terms, flen, hashes, df, corpus.n, corpus.avg_wlen, scoring)
            best_k, best = None, 0.0
            by_k: dict[int, float] = {}
            for sec in sorted(secs_of.get(pid, []), key=lambda r: store.reader.section_ordinal(r["id"])):
                if not any(h in sec["terms"] for h in hashes):
                    continue  # own-match only (Arpit, 2026-10-13)
                unit = {}
                for h in hashes:
                    own = sec["terms"].get(h)
                    tail = list(terms.get(h, []))[slots:]
                    if own is None and not any(tail):
                        continue
                    unit[h] = (list(own or []) + [0] * slots)[:slots] + tail
                uflen = (list(sec["flen"]) + [0] * slots)[:slots] + flen[slots:]
                k = store.reader.section_ordinal(sec["id"])
                by_k[k] = score_record(unit, uflen, hashes, df, corpus.n, corpus.avg_wlen, scoring)
                if by_k[k] > best:
                    best_k, best = k, by_k[k]
            sec_id, contribution = engine.get(pid, (None, 0.0))
            qid = row["id"]
            if sec_id is None:
                if best_k is not None and best > s_doc and not close(best, s_doc):
                    failures.append({"id": qid, "doc": pid, "why": "a section beats the document but none is named"})
                continue
            named += 1
            k = store.reader.section_ordinal(sec_id)
            if k not in by_k:
                failures.append({"id": qid, "doc": pid, "why": "the named section does not match on its own words"})
                continue
            if contribution > by_k[k] and not close(contribution, by_k[k]):
                failures.append({"id": qid, "doc": pid, "why": "contribution exceeds the section's S_sec*"})
            if k != best_k:
                failures.append({"id": qid, "doc": pid, "why": f"named #s{k}, the best is #s{best_k}"})
            if not close(contribution, lam * (best - s_doc)):
                failures.append({"id": qid, "doc": pid, "why": "contribution is not lambda * (best S_sec* - S_doc')"})
            if lam == 1.0 and not close(s_doc + contribution, best):
                failures.append({"id": qid, "doc": pid, "why": "at lambda 1 the document does not score its best section"})

    report = {
        "gate": "G4 - no section contribution exceeds its section scored as a document (construction, no key)",
        "section_weight": lam,
        "questions": len(rows),
        "sectioned_candidates_checked": checked,
        "sections_named": named,
        "failures": len(failures),
        "first_failures": failures[:20],
        "verdict": "PASS" if checked > 0 and named > 0 and not failures else "FAIL",
    }
    print(json.dumps(report, indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
