"""The cited-decision contest set, and the circularity SCREEN that gates it.

**W-183's recommendation, built.** See
[`work/proposals/quality-endpoint-for-reranking.md`](../../work/proposals/quality-endpoint-for-reranking.md),
committed alone at the freeze so the band below cannot have been chosen to fit
a number.

## What a contest is

This corpus cites *into* documents, not merely at them::

    [SR-RS](0133_predictions.md) decision 19

The citing author names a target document **and a decision inside it**. Records
number their decisions `**N.` by a convention a test already enforces, so the
line range of decision 19 in that file is mechanically resolvable. One contest
is therefore:

    (query, target document, true line range)

where the query is the citing **sentence** — the author's own wording for the
thing they were pointing at — and the truth is **where the author put that
decision**, fixed long before any query existed.

## The screen, and why it comes first

🔴 **"Non-circular" had only ever been judged by argument**, three times, and
C2's number is still quoted as if it meant something. So the endpoint is gated
on a test it can FAIL, computed from the corpus alone with no arm run and no
engine configured:

> For each contest, score every passage with the reranker's **own** objective
> (`passage_boost`). Is the TRUE passage also the one that objective picks?

`agreement` is the share where it is.

- `≈ 1.00` -> **circular**: the truth IS the objective. That is C2, caught
  mechanically instead of debated.
- `≈ chance` -> **independent**: the objective carries no information here, and
  a null from this endpoint would say nothing about the feature.
- **in between** -> usable, and the only shape in which a proximity reranker can
  be shown to earn its latency.

**The band is `0.25 <= agreement <= 0.85`** and it is the proposal's, frozen
before this file existed. ⚠ **It may not move** (SR-RS decision 10b). If the
measured value lands outside it, the output of W-183 is the fork to Arpit, not
a wider band.

⚠ **The screen is necessary, not sufficient.** It catches truth-equals-objective
and it cannot catch circularity through a third variable — an author who
paraphrases the decision they cite writes a query dense in that decision's own
words. Two pre-registered mitigations, both implemented here: `agreement` is
reported **per record** so one dense document cannot carry the result, and a
contest whose citing sentence shares more than `QUOTE_SHARE` of its analyzed
terms with the true passage is **excluded as a quotation rather than a
reference**.

## What this file does NOT do

It configures no arm, reads no answer key, and rules on nothing. It emits
contests and one number. Offline and deterministic: the corpus is walked in
sorted order and every tie breaks on a name.

Usage::

    python tools/quality-controls/cited_decision.py --root . --json-out screen.json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from fux.query.analyzer import analyze  # noqa: E402
from fux.query.rerank import passage_boost  # noqa: E402
from fux.refer._chunk import chunk  # noqa: E402

#: `](<something>.md) decision 19` / `decisions 3-5`. The link target is kept
#: raw and resolved against the CITING file's directory, because the same
#: record is cited as `0133_predictions.md` from `records/` and as
#: `../records/0133_predictions.md` from `work/`.
CITATION = re.compile(
    r"\]\((?P<target>[^)\s]+\.md)\)\s*(?:§\d+\s*)?decisions?\s+(?P<number>\d+)(?P<suffix>[a-z]?)"
)

#: A record's decision heading: `**19.` or `**19b.` at the start of a line.
DECISION = re.compile(r"^\*\*(?P<number>\d+)(?P<suffix>[a-z]?)\.")

#: Any line that ends a decision even though it is not the next one.
SECTION = re.compile(r"^#{2,6}\s")

#: Above this share of the citing sentence's analyzed terms appearing in the
#: true passage, the citation is a QUOTATION and the contest is dropped. The
#: mitigation is the proposal's; the value is the proposal's `80 %`.
QUOTE_SHARE = 0.80

#: The pre-registered band. 🔴 Frozen — see the module docstring.
BAND = (0.25, 0.85)


@dataclass(frozen=True)
class Contest:
    """One `(query, document, true span)` triple, plus where it came from."""

    query: str
    source: str
    target: str
    number: str
    line_start: int
    line_end: int
    #: Ordinals of the passages that overlap the true line range.
    true_ordinals: tuple[int, ...]
    passages: int


def _sentence_around(text: str, index: int) -> str:
    """The sentence containing `index`, as an author would read it.

    Markdown decoration is stripped because the query is what somebody would
    TYPE, not what the file holds: a query containing `**` or `](path.md)`
    exercises the tokenizer's handling of punctuation, which is not the
    question this endpoint asks.
    """
    start = max(text.rfind(". ", 0, index), text.rfind("\n\n", 0, index)) + 1
    dot = text.find(". ", index)
    para = text.find("\n\n", index)
    candidates = [p for p in (dot, para) if p != -1]
    end = min(candidates) if candidates else len(text)
    raw = text[start:end]
    raw = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", raw)      # links -> their text
    raw = re.sub(r"[`*_#>|]", " ", raw)                      # markdown decoration
    raw = re.sub(r"\s+", " ", raw)
    return raw.strip()


def decision_spans(lines: list[str]) -> dict[str, tuple[int, int]]:
    """`{"19": (start, end)}`, 1-based inclusive, for one record's decisions.

    A decision runs to the next decision or the next `##`-or-deeper heading,
    whichever comes first. **Never to the end of the file**: a trailing span
    that swallowed half a record would make the truth trivially easy to hit and
    the screen would read as independent when it was simply coarse.
    """
    marks: list[tuple[str, int]] = []
    stops: list[int] = []
    for i, line in enumerate(lines, start=1):
        match = DECISION.match(line)
        if match:
            marks.append((match.group("number") + match.group("suffix"), i))
        elif SECTION.match(line):
            stops.append(i)
    spans: dict[str, tuple[int, int]] = {}
    for position, (key, start) in enumerate(marks):
        after_next = marks[position + 1][1] - 1 if position + 1 < len(marks) else len(lines)
        after_stop = next((s - 1 for s in stops if s > start), len(lines))
        spans[key] = (start, min(after_next, after_stop))
    return spans


def _walk(root: Path, folders: tuple[str, ...]) -> list[Path]:
    out: list[Path] = []
    for folder in folders:
        base = root / folder
        if not base.is_dir():
            continue
        out.extend(p for p in base.rglob("*.md") if "golden" not in p.parts)
    return sorted(out)


def contests(root: Path, folders: tuple[str, ...] = ("records", "work", "docs")) -> list[Contest]:
    """Every resolvable cited-decision contest in the tree, in sorted order.

    ⚠ **`work/golden/` is excluded by path, unconditionally.** The walk is
    recursive over `work/`, which is the one route
    [L11](../../records/0012_LAW-11-sealed-answer-key.md) names as unguarded.
    """
    cache: dict[Path, tuple[list[str], dict[str, tuple[int, int]], list]] = {}
    found: list[Contest] = []
    for source in _walk(root, folders):
        text = source.read_text(encoding="utf-8", errors="replace")
        for match in CITATION.finditer(text):
            target = (source.parent / match.group("target")).resolve()
            if not target.is_file() or "golden" in target.parts:
                continue
            if target not in cache:
                body = target.read_text(encoding="utf-8", errors="replace")
                cache[target] = (
                    body.splitlines(),
                    decision_spans(body.splitlines()),
                    chunk(body),
                )
            lines, spans, passages = cache[target]
            key = match.group("number") + match.group("suffix")
            if key not in spans:
                continue
            start, end = spans[key]
            true = tuple(
                p.ordinal
                for p in passages
                if p.line_start and p.line_end and p.line_start <= end and p.line_end >= start
            )
            if not true or len(true) == len(passages):
                # No passage carries the decision, or every passage does. Either
                # way there is no contest — dropped rather than counted as a hit.
                continue
            query = _sentence_around(text, match.start())
            if len(analyze(query)) < 3:
                continue
            found.append(
                Contest(
                    query=query,
                    source=source.relative_to(root).as_posix(),
                    target=target.relative_to(root).as_posix(),
                    number=key,
                    line_start=start,
                    line_end=end,
                    true_ordinals=true,
                    passages=len(passages),
                )
            )
    return found


def _quotation(query_terms: list[str], true_text: str) -> bool:
    """Is the citing sentence mostly lifted from the passage it points at?"""
    if not query_terms:
        return True
    inside = set(analyze(true_text))
    return sum(1 for t in query_terms if t in inside) / len(query_terms) > QUOTE_SHARE


def screen(root: Path, rows: list[Contest]) -> dict:
    """`agreement`, the chance rate, and the per-record breakdown.

    **The objective is the reranker's, called directly.** Nothing here
    reimplements proximity: a second copy of `passage_boost` that drifted from
    the first would screen a different feature than the one being measured.
    """
    cache: dict[str, list] = {}
    agree = 0
    chance = 0.0
    counted = 0
    quotations = 0
    per_record: dict[str, list[int]] = {}

    for row in rows:
        if row.target not in cache:
            cache[row.target] = chunk((root / row.target).read_text(encoding="utf-8"))
        passages = cache[row.target]
        query_terms = analyze(row.query)
        true_text = " ".join(p.text for p in passages if p.ordinal in row.true_ordinals)
        if _quotation(query_terms, true_text):
            quotations += 1
            continue
        scores = [(passage_boost(query_terms, analyze(p.text)), -p.ordinal) for p in passages]
        best = max(range(len(scores)), key=lambda i: scores[i])
        hit = passages[best].ordinal in row.true_ordinals
        counted += 1
        agree += int(hit)
        chance += len(row.true_ordinals) / len(passages)
        bucket = per_record.setdefault(row.target, [0, 0])
        bucket[0] += int(hit)
        bucket[1] += 1

    agreement = agree / counted if counted else 0.0
    return {
        "contests_found": len(rows),
        "contests_excluded_as_quotations": quotations,
        "contests_screened": counted,
        "agreement": round(agreement, 4),
        "chance": round(chance / counted, 4) if counted else 0.0,
        "band": list(BAND),
        "inside_band": BAND[0] <= agreement <= BAND[1] if counted else False,
        "per_record": {
            k: {"agree": v[0], "n": v[1], "rate": round(v[0] / v[1], 4)}
            for k, v in sorted(per_record.items())
            if v[1] >= 5
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--json-out", type=Path)
    parser.add_argument("--contests-out", type=Path, help="write the contest set itself")
    args = parser.parse_args(argv)

    root = args.root.resolve()
    rows = contests(root)
    result = screen(root, rows)

    print(f"contests found:      {result['contests_found']}")
    print(f"  excluded as quotations: {result['contests_excluded_as_quotations']}")
    print(f"  screened:               {result['contests_screened']}")
    print(f"agreement:           {result['agreement']:.4f}")
    print(f"chance:              {result['chance']:.4f}")
    print(f"band:                {BAND[0]} - {BAND[1]}")
    print()
    if not result["contests_screened"]:
        print("NO CONTESTS — the generator found nothing, which is a defect in it, not a result")
        return 2
    if result["inside_band"]:
        print("SCREEN PASSED — the endpoint is usable; write W-154's Part B against it")
    elif result["agreement"] > BAND[1]:
        print(
            "SCREEN FAILED (circular) — the truth IS the reranker's objective here. "
            "This is C2's shape, caught before an arm ran. W-183's output is the fork."
        )
    else:
        print(
            "SCREEN FAILED (independent) — the objective carries no information about the "
            "truth, so a null from this endpoint would say nothing. W-183's output is the fork."
        )

    if args.json_out:
        args.json_out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    if args.contests_out:
        args.contests_out.write_text(
            "\n".join(json.dumps(asdict(r)) for r in rows), encoding="utf-8"
        )
    return 0 if result["inside_band"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
