#!/usr/bin/env python3
"""Compute a golden question's difficulty from the key and the corpus it is asked against.

**What this is for.** `difficulty` is a field in the golden answer key, and a
free-text one — ``"difficulty": "medium"`` — is unfalsifiable: nobody can check
it, nobody can re-derive it, and a stratified claim built on it ("fux is weaker
on hard questions") means whatever the labeller felt that day. This script
replaces the judgement with a **count of the independent discriminations a
question forces**, every one of them computed from bytes that are already
committed or already in the key.

🔴 **Difficulty is NEVER derived from fux's own results.** *Hard = fux got it
wrong* turns every stratified claim into a tautology and destroys the only thing
the field is for. Nothing in this file reads a prediction, a score or an index.

🔴 **This script never runs against a key inside the repository**, and it refuses
rather than trusting the caller — `work/golden/golden-answer/` is not a location
and no key file exists under this tree
([SR-LAW-11](../../records/0012_LAW-11-sealed-answer-key.md)). The key is Arpit's;
he or Codex points this at it from wherever he keeps it.

## The two numbers

**`difficulty_static`** — intrinsic to the question, frozen when the key is
written, comparable across every rung. It is `d`, the discrimination count:

====================== ====================================================
flag                   +1 when
====================== ====================================================
``multi_doc``          ``len(relevant) >= 2`` (and +1 again at ``>= 3``)
``no_lexical_overlap`` no high-IDF question term appears in the evidence
``retired_competitor`` an archived or superseded doc matches and is not
                       in ``relevant`` — needs discrimination, not recall
``buried_value``       the primary doc is large or low-structure
``negation``           the question turns on a negation or an exception
``unanswerable``       ``answerable`` is false
====================== ====================================================

Bands: ``d <= 1`` easy · ``d == 2`` medium · ``d >= 3`` hard, and an
**unanswerable question is floored at hard** whatever its count — abstention is
the discrimination the engine is worst at and the band should never hide one.

**`distractors_at_rung`** — corpus-dependent, recomputed per rung: how many
documents that are *not* in ``relevant`` carry the question's top-IDF terms. This
is why a lookup that is trivial at 20 documents is genuinely hard at 10 000, and
it is the number the ladder exists to expose.

## Determinism (L3)

Fixed stopword list, fixed tokenizer, BM25 IDF over a corpus enumerated in sorted
path order, integer comparisons only. Same key + same corpus in, byte-identical
output. No clock, no randomness, no set-iteration order.

Usage::

    python3 tools/golden-difficulty/difficulty.py \\
        --key /path/to/answers.jsonl --corpus ~/my_programs/fux-lab/corpora/golden/rung-01000 \\
        --rung rung-01000 --out difficulty-rung-01000.jsonl

    python3 tools/golden-difficulty/difficulty.py --selftest   # synthetic fixtures, no key
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path

#: Word characters only, lowercased. Deliberately dumb: a smarter tokenizer is a
#: second analyzer to keep in step with the engine's, and this measures the
#: question, not the engine.
_TOKEN = re.compile(r"[a-z0-9]+")

#: A closed stopword list. **Closed is the point** — a frequency-derived list
#: would move when the corpus moves and silently re-label every question.
STOPWORDS = frozenset("""
a an and are as at be been by do does did for from had has have how i if in into
is it its may must no not of on or should so than that the their then there these
they this to was were what when where which who whom why will with would you your
""".split())

#: Negation and exception cues. Closed, for the same reason as STOPWORDS.
NEGATION_CUES = frozenset(
    "not never except unless exempt exempted without excluding besides "
    "neither nor cannot".split()
)

#: Extensions whose bytes carry little structure to locate an answer inside.
LOW_STRUCTURE = frozenset({".eml", ".txt", ".html", ".htm", ".yaml", ".yml", ".log"})

#: A primary document at or above this many bytes buries a specific value.
BURIED_BYTES = 8000
#: ...or this many, when the format gives the reader no headings to aim at.
BURIED_BYTES_LOW_STRUCTURE = 3000

#: How many of the question's highest-IDF terms define "about this question".
TOP_TERMS = 3

#: Frontmatter key that retires another document.
_SUPERSEDES = re.compile(r"^supersedes:\s*(.+)$", re.M)


def tokens(text: str) -> list[str]:
    """Lowercase word tokens, stopwords and one-character tokens dropped."""
    return [t for t in _TOKEN.findall(text.lower()) if len(t) > 1 and t not in STOPWORDS]


def load_corpus(root: Path) -> dict[str, str]:
    """Every indexable document under ``root``, keyed by its path relative to it.

    Sorted, so the walk order cannot reach the output. Decoding is
    ``errors="replace"``: a byte this cannot read is still a document that
    competes for the query, and skipping it would undercount distractors —
    the direction that flatters the engine.
    """
    docs: dict[str, str] = {}
    for p in sorted(root.rglob("*")):
        if not p.is_file() or p.name.startswith("."):
            continue
        rel = p.relative_to(root).as_posix()
        if rel.startswith(".fux/") or "/.git/" in f"/{rel}":
            continue
        docs[rel] = p.read_text(encoding="utf-8", errors="replace")
    return docs


def retired_paths(docs: dict[str, str]) -> set[str]:
    """Documents that are archived or that another document declares it supersedes.

    ⚠ **The retired half of a supersession pair is what makes a question hard**,
    not the current half: the current one is the answer. So a ``supersedes:``
    line contributes the *target* it names, never the document carrying it.
    """
    out = {rel for rel in docs if "/archive/" in f"/{rel}" or rel.startswith("archive/")}
    for rel, text in docs.items():
        for m in _SUPERSEDES.finditer(text[:2000]):
            target = m.group(1).strip().strip("\"'")
            for cand in docs:
                if cand == target or cand.endswith("/" + target) or Path(cand).name == Path(target).name:
                    out.add(cand)
    return out


def idf_table(docs: dict[str, str]) -> dict[str, float]:
    """BM25 IDF per term over the corpus. Deterministic and corpus-relative."""
    n = len(docs)
    df: dict[str, int] = {}
    for text in docs.values():
        for term in set(tokens(text)):
            df[term] = df.get(term, 0) + 1
    return {t: math.log(1 + (n - c + 0.5) / (c + 0.5)) for t, c in df.items()}


def top_terms(question: str, idf: dict[str, float], k: int = TOP_TERMS) -> list[str]:
    """The k highest-IDF question terms, ties broken alphabetically.

    A term the corpus has never seen gets the IDF of a term seen once, not
    infinity: an unseen term is a vocabulary gap, which ``no_lexical_overlap``
    already scores, and letting it dominate here would make every such question
    look like it has no competitors.
    """
    n = max(len(idf), 1)
    unseen = math.log(1 + (n - 1 + 0.5) / 1.5)
    uniq = sorted(set(tokens(question)))
    return sorted(uniq, key=lambda t: (-min(idf.get(t, unseen), unseen), t))[:k]


def score_row(row: dict, docs: dict[str, str], idf: dict[str, float], retired: set[str]) -> dict:
    """One key row in, one difficulty object out. Reads no prediction and no index."""
    question = row.get("question", "")
    relevant = list(row.get("relevant") or [])
    answerable = bool(row.get("answerable", True))
    flags: list[str] = []
    d = 0

    if len(relevant) >= 2:
        flags.append("multi_doc")
        d += 1
        if len(relevant) >= 3:
            d += 1

    q_terms = set(tokens(question))
    evidence = " ".join(
        str(e.get("quote", "")) for e in (row.get("evidence") or []) if isinstance(e, dict)
    )
    if answerable and evidence and not (q_terms & set(tokens(evidence))):
        flags.append("no_lexical_overlap")
        d += 1

    keys = top_terms(question, idf)
    need = max(1, (len(keys) + 1) // 2)
    competitors = [
        rel
        for rel, text in docs.items()
        if rel not in relevant and len(set(tokens(text)) & set(keys)) >= need
    ]
    if any(rel in retired for rel in competitors):
        flags.append("retired_competitor")
        d += 1

    primary = row.get("primary") or (relevant[0] if relevant else None)
    if primary and primary in docs:
        size = len(docs[primary].encode("utf-8"))
        limit = (
            BURIED_BYTES_LOW_STRUCTURE
            if Path(primary).suffix.lower() in LOW_STRUCTURE
            else BURIED_BYTES
        )
        if size >= limit:
            flags.append("buried_value")
            d += 1

    # ⚠ Negation is checked on RAW tokens, before stopwords. "not" and "nor" are
    # stopwords for ranking and are the whole question here — reusing `q_terms`
    # silently scored every "when does X not apply" as if it said "when does X
    # apply", which is the one class this flag exists for.
    raw = set(_TOKEN.findall(question.lower()))
    if raw & NEGATION_CUES or "n't" in question.lower():
        flags.append("negation")
        d += 1

    if not answerable:
        flags.append("unanswerable")
        d += 1

    band = "easy" if d <= 1 else ("medium" if d == 2 else "hard")
    if not answerable:
        band = "hard"

    return {
        "band": band,
        "d": d,
        "flags": flags,
        "key_terms": keys,
        "distractors": len(competitors),
    }


def run(key_path: Path, corpus: Path, rung: str) -> list[dict]:
    """Score every row of a key against one rung. Returns rows, writes nothing."""
    docs = load_corpus(corpus)
    if not docs:
        raise SystemExit(f"difficulty: no documents under {corpus}")
    idf = idf_table(docs)
    retired = retired_paths(docs)
    out = []
    for line in key_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        row = json.loads(line)
        diff = score_row(row, docs, idf, retired)
        out.append(
            {
                "id": row.get("id"),
                "rung": rung,
                "difficulty_static": {k: diff[k] for k in ("band", "d", "flags")},
                "key_terms": diff["key_terms"],
                "distractors_at_rung": diff["distractors"],
            }
        )
    return out


def _guard_key_path(key_path: Path) -> None:
    """Refuse a key inside this repository. **No key file exists here** (L11).

    This is the one place the tool could be turned into the thing the law
    forbids — *"just point it at the repo copy"* — so it fails closed rather
    than trusting the caller's intent.
    """
    repo = Path(__file__).resolve().parents[2]
    try:
        key_path.resolve().relative_to(repo)
    except ValueError:
        return
    raise SystemExit(
        f"difficulty: refusing a key inside the repository ({key_path}). "
        "No answer key lives under this tree — SR-LAW-11. Point this at Arpit's copy."
    )


# --------------------------------------------------------------------------- #
# Self-test — synthetic fixtures, invented here, never a real question.
# --------------------------------------------------------------------------- #

_FIXTURE_DOCS = {
    "seed/01-rate-card.md": "Rate card. The reefer surcharge for Nagpur is 14 percent.\n",
    "seed/02-runbook.md": "Runbook. On a temperature excursion, quarantine the pallet.\n",
    "seed/03-notes.md": "Quarantine pallets are logged by the night shift lead.\n",
    "seed/archive/a01-rate-card-old.md": "Rate card 2019. The reefer surcharge for Nagpur is 9 percent.\n",
    "ext/filler/x1.md": "Unrelated writing about bicycles and weather.\n",
}


def _selftest() -> int:
    docs = dict(_FIXTURE_DOCS)
    idf = idf_table(docs)
    retired = retired_paths(docs)
    assert "seed/archive/a01-rate-card-old.md" in retired, retired

    easy = score_row(
        {"question": "What is the reefer surcharge percentage?", "answerable": True,
         "relevant": ["seed/01-rate-card.md"], "primary": "seed/01-rate-card.md",
         "evidence": [{"quote": "The reefer surcharge for Nagpur is 14 percent."}]},
        docs, idf, retired)
    assert easy["band"] == "easy", easy

    # Two discriminations -> medium. Asserted at the value the rubric gives, not
    # at the one the question "feels" like: a fixture written to a felt band is
    # the judgement call this tool exists to remove.
    medium = score_row(
        {"question": "What is the current reefer surcharge, and when does it not apply?",
         "answerable": True,
         "relevant": ["seed/01-rate-card.md", "seed/02-runbook.md"],
         "primary": "seed/01-rate-card.md",
         "evidence": [{"quote": "The reefer surcharge for Nagpur is 14 percent."}]},
        docs, idf, retired)
    assert medium["flags"] == ["multi_doc", "negation"], medium
    assert medium["band"] == "medium" and medium["d"] == 2, medium

    # Three relevant documents (+2) and a negation (+1) -> hard.
    hard = score_row(
        {"question": "Which quarantine steps do not apply to the reefer surcharge?",
         "answerable": True,
         "relevant": ["seed/01-rate-card.md", "seed/02-runbook.md", "seed/03-notes.md"],
         "primary": "seed/02-runbook.md",
         "evidence": [{"quote": "quarantine the pallet"}]},
        docs, idf, retired)
    assert hard["band"] == "hard" and hard["d"] >= 3, hard

    absent = score_row(
        {"question": "Which insurer covers the Guwahati fleet?", "answerable": False,
         "relevant": [], "evidence": []},
        docs, idf, retired)
    assert absent["band"] == "hard" and "unanswerable" in absent["flags"], absent

    gap = score_row(
        {"question": "How much extra for chilled haulage?", "answerable": True,
         "relevant": ["seed/01-rate-card.md"], "primary": "seed/01-rate-card.md",
         "evidence": [{"quote": "The reefer surcharge for Nagpur is 14 percent."}]},
        docs, idf, retired)
    assert "no_lexical_overlap" in gap["flags"], gap

    a = score_row({"question": "reefer surcharge Nagpur", "answerable": True,
                   "relevant": ["seed/01-rate-card.md"], "primary": "seed/01-rate-card.md",
                   "evidence": [{"quote": "reefer surcharge Nagpur"}]}, docs, idf, retired)
    b = score_row({"question": "reefer surcharge Nagpur", "answerable": True,
                   "relevant": ["seed/01-rate-card.md"], "primary": "seed/01-rate-card.md",
                   "evidence": [{"quote": "reefer surcharge Nagpur"}]}, docs, idf, retired)
    assert a == b, "not deterministic"

    print("difficulty: selftest OK (6 checks)")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--key", type=Path, help="answer-key .jsonl — Arpit's copy, outside this repo")
    ap.add_argument("--corpus", type=Path, help="the rung directory to score against")
    ap.add_argument("--rung", default="", help="rung label written into each row")
    ap.add_argument("--out", type=Path, help="write jsonl here instead of stdout")
    ap.add_argument("--selftest", action="store_true", help="run the synthetic fixtures and exit")
    args = ap.parse_args(argv)

    if args.selftest:
        return _selftest()
    if not args.key or not args.corpus:
        ap.error("--key and --corpus are required (or use --selftest)")

    _guard_key_path(args.key)
    rows = run(args.key, args.corpus, args.rung or args.corpus.name)
    text = "".join(json.dumps(r, sort_keys=True) + "\n" for r in rows)
    if args.out:
        args.out.write_text(text, encoding="utf-8")
        print(f"difficulty: {len(rows)} rows -> {args.out}")
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
