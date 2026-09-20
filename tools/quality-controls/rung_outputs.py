#!/usr/bin/env python3
"""W-204 phase A — one human-readable document per rung, from the hand-offs.

🔴 **There is no column for *correct*, and there never will be in this file.**
A per-rung document is an **output** record: it carries what fux ranked,
answered, cited and declined, and never what it should have done. *Correct*
is born in W-204 phase D, after Arpit opens the key, and nowhere earlier
([L11](../../records/0012_LAW-11-sealed-answer-key.md)). **A document that
guessed would train the next reader to trust a guess.**

**It is generated, never written by hand**, and that is the point. The `.md` and
the `handoff-set-N.jsonl` rows phase D will score come from the same bytes, so
the eight documents cannot disagree with the rows — the failure mode where a
readable summary and the machine evidence drift apart, and the summary is what
everybody actually reads.

**Set 1 in full, then set 2, never interleaved.** The two sets have different
authors and the gap between them is the measurement; a document that alternates
invites a reader to average them by eye. The generator **refuses** a pair whose
ids collide, because one ambiguous id scores the wrong set and nothing
downstream can see it.

**Stdlib only**, and no network: it reads two JSONL files and writes one
Markdown file.

    python3 tools/quality-controls/rung_outputs.py \
        --rung rung-00100 \
        --evidence work/regression/2026-09-20-golden-ladder-outputs/evidence/rung-00100
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CORPORA = Path.home() / "my_programs" / "fux-lab" / "corpora" / "golden"

#: Who authored each set. Stated here because every heading repeats it and a
#: reader who meets one set without the other has to be told which this is.
AUTHOR = {1: "Codex", 2: "Claude — `informed` permanently"}


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def index_version(rung: str, corpora: Path = CORPORA) -> str:
    """The `_format` stamp of the rung's own shards, read rather than assumed.

    ⚠ **Not a default and not an argument with a plausible value.** The whole
    reason this run exists at a frozen engine is that the rungs' format moved
    (v3 -> v4); a header that *said* v4 while the shards held v3 is precisely
    the disagreement this generator is built to make impossible. When the corpus
    is not on this machine the header says so, in those words, rather than
    naming a version nobody checked.
    """
    index = corpora / rung / ".fux" / "index"
    if not index.is_dir():
        return "unknown — the corpus is not on this machine"
    for shard in sorted(index.glob("*.jsonl")):
        first = shard.read_text(encoding="utf-8").split("\n", 1)[0]
        try:
            return json.loads(first).get("_format") or "unknown — no `_format` in the shard header"
        except json.JSONDecodeError:
            continue
    return "unknown — no readable shard"


def document_name(rung: str) -> str:
    """`rung-00100` -> `RUNG-00100.md`; `rung-seed` -> `RUNG-SEED.md`."""
    return f"RUNG-{rung.removeprefix('rung-').upper()}.md"


def _locators(row: dict) -> list[str]:
    return [str(loc) for loc in (row.get("ranked") or [])]


def _citations(row: dict) -> list[str]:
    """`{"doc","lines"}` -> `doc:Lx-Ly`, de-duplicated, order preserved.

    ⚠ **De-duplicated, because `answer` cites one document once per passage.**
    Printing the same locator four times reads as four pieces of evidence.
    """
    out: list[str] = []
    for cite in row.get("citations") or []:
        doc, lines = cite.get("doc", ""), cite.get("lines", "")
        text = f"{doc}:{lines}" if lines else doc
        if text and text not in out:
            out.append(text)
    return out


def question_section(row: dict) -> list[str]:
    """One question's section. It reports; it never judges."""
    lines = [f"### `{row.get('id')}`", "", f"> {row.get('question', '').strip()}", ""]

    band = row.get("band")
    answerable = row.get("answerable")
    lines.append(
        f"**band** `{band}` · **answerable** `{json.dumps(answerable)}`"
    )
    lines.append("")

    ranked = _locators(row)
    if ranked:
        lines.append("**`fux ask` — top 10, in rank order**")
        lines.append("")
        lines.extend(f"{i}. `{loc}`" for i, loc in enumerate(ranked, 1))
    else:
        # Not folded in with the populated case: an empty ranked list is one of
        # the four surface claims this run is allowed to make, and it has to be
        # greppable rather than inferred from a missing block.
        lines.append("**`fux ask` — 🔴 EMPTY ranked list**, no result returned.")
    lines.append("")

    answer_text = (row.get("answer_text") or "").strip()
    if answer_text:
        lines.append("**`fux answer`**")
        lines.append("")
        lines.append("```text")
        lines.extend(answer_text.splitlines() or [""])
        lines.append("```")
        lines.append("")
        cites = _citations(row)
        if cites:
            lines.append("**cited**")
            lines.append("")
            lines.extend(f"- `{c}`" for c in cites)
        else:
            lines.append("**cited** — 🔴 nothing. An answer with no citation.")
        lines.append("")
        lines.append(f"**freshness** `{row.get('freshness') or 'not recorded'}`"
                     f" · **source** `{row.get('source') or 'not recorded'}`")
    else:
        lines.append("**`fux answer` — DECLINED.** No answer and no citation.")
    lines.append("")
    return lines


def render(rung: str, sets: dict[int, list[dict]], *, fmt: str) -> str:
    commits = sorted({r.get("engine_commit") for rows in sets.values() for r in rows if r.get("engine_commit")})
    commit = commits[0] if len(commits) == 1 else (", ".join(commits) or "not recorded")

    out = [
        f"# {rung} — what fux ranked, answered and declined",
        "",
        "| | |",
        "|---|---|",
        f"| rung | `{rung}` |",
        f"| engine commit | `{commit}` |",
        f"| index version | `{fmt}` |",
        f"| set 1 | {len(sets.get(1, []))} questions — {AUTHOR[1]} |",
        f"| set 2 | {len(sets.get(2, []))} questions — {AUTHOR[2]} |",
        "",
        "🔴 **There is no correctness column in this document, and no Claude session",
        "can supply one.** It records what fux *did*. *Correct* and *incorrect* are",
        "W-204 phase D's, after Arpit opens the key.",
        "",
        "🔴 **The two sets are never pooled.** Their authors differ and the gap between",
        "them is the measurement; a figure spanning both erases it.",
        "",
        "**Generated by `tools/quality-controls/rung_outputs.py` from",
        "`handoff-set-1.jsonl` and `handoff-set-2.jsonl`. Do not edit by hand** — an",
        "edit here makes this document disagree with the rows phase D scores.",
        "",
    ]
    if len(commits) > 1:
        out[:0] = [
            "🔴 **THE HAND-OFFS DISAGREE ABOUT THE ENGINE.** More than one",
            "`engine_commit` appears in these rows, so this rung was not produced at one",
            "frozen engine and nothing here may be read as a single measurement.",
            "",
        ]

    for n in (1, 2):
        rows = sets.get(n)
        if rows is None:
            continue
        out += ["---", "", f"## Set {n} — {AUTHOR[n]}", "", f"{len(rows)} questions.", ""]
        for row in rows:
            out += question_section(row)
    return "\n".join(out).rstrip() + "\n"


def collide(sets: dict[int, list[dict]]) -> list[str]:
    """Ids present in both sets. Non-empty is fatal — see the module docstring."""
    a = {r.get("id") for r in sets.get(1, [])}
    b = {r.get("id") for r in sets.get(2, [])}
    return sorted(x for x in (a & b) if x is not None)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--rung", required=True, help="e.g. rung-00100")
    ap.add_argument("--evidence", type=Path, required=True,
                    help="the directory holding handoff-set-1.jsonl and handoff-set-2.jsonl")
    ap.add_argument("--out", type=Path, default=None,
                    help="output path; defaults to <evidence>/RUNG-NNNNN.md")
    ap.add_argument("--index-version", default=None,
                    help="override the `_format` read from the rung's shards")
    args = ap.parse_args(argv)

    sets: dict[int, list[dict]] = {}
    for n in (1, 2):
        path = args.evidence / f"handoff-set-{n}.jsonl"
        if not path.is_file():
            print(f"missing {path}", file=sys.stderr)
            return 1
        sets[n] = read_jsonl(path)

    both = collide(sets)
    if both:
        print(
            f"{len(both)} id(s) appear in BOTH sets: {both[:5]} — refusing. "
            "One ambiguous id scores the wrong set and nothing downstream can see it.",
            file=sys.stderr,
        )
        return 1

    fmt = args.index_version or index_version(args.rung)
    out = args.out or (args.evidence / document_name(args.rung))
    out.write_text(render(args.rung, sets, fmt=fmt), encoding="utf-8")
    print(f"{out}  ({len(sets[1])} + {len(sets[2])} questions, index {fmt})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
