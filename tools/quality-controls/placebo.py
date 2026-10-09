#!/usr/bin/env python3
"""The CONTENT-FREE PLACEBO arm — [SR-RS](../../records/0133_predictions.md)
decision 15's second control.

**What it is for.** *Neural Retrievers are Biased Towards LLM-Generated Content*
(KDD 2024) establishes **source bias**: retrievers rank LLM-written text higher
independently of whether it informs, and the effect reaches re-rankers. Every
fux enrichment arm added ~115 words of fluent LLM prose to nine of ten documents
**with no matched control**, so *text presence* and *text content* have never
been separable in any number this project has filed.

**The control.** Enrichment of MATCHED LENGTH that carries no information about
the document it is attached to.

⚠ **The load-bearing property is that every placebo draws from ONE pool, so all
of them share a vocabulary.** A placebo written *about an unrelated topic* would
still be discriminative — its terms would match some documents better than
others — and would measure a different thing. Identical vocabulary across the
whole corpus is what makes any remaining lift attributable to *presence of
fluent text* and nothing else.

**Deterministic (L4).** Sentence selection is driven by the source sha, never by
`random` and never by the wall clock: same corpus in, byte-identical placebos
out. No model is called — this is the control *for* model-written text, and
generating it with a model would be circular.

**`--per-line`** (W-257, 2026-10-10) matches **line count** too: one placebo
line per question line, each word-matched to its line. Without it the body is
one paragraph, byte for byte what every earlier run used.

**It is NOT installed anywhere.** It writes to an output directory you name, and
a measurement swaps it in. Installing a control into `.fux/enrich/` would
silently replace the corpus everything else is graded against.

    python3 tools/quality-controls/placebo.py [--per-line] <enrich-dir> <out-dir>
"""

from __future__ import annotations

import hashlib
import re
import sys
from pathlib import Path

#: Fluent, domain-plausible, and deliberately CONTENT-FREE: every sentence could
#: be attached to any document in any corpus without becoming false. That is the
#: point — no sentence here can help a ranker tell two documents apart.
#:
#: ⚠ Written by hand, not generated. A model asked for "generic text" reaches for
#: the subject matter it was shown, which is the leak this control exists to close.
POOL = (
    "This document sets out the approach taken and the reasoning behind it.",
    "It covers the considerations that apply and the order in which they matter.",
    "The material here is intended for readers who need the detail rather than the summary.",
    "Several points are worth drawing out before going further.",
    "The steps involved are described in the sequence they are normally carried out.",
    "Where a choice exists, the tradeoffs are stated rather than assumed.",
    "Context that a reader is likely to need is provided alongside each part.",
    "Some of what follows will be familiar and is included for completeness.",
    "The scope is stated explicitly so that its edges are visible.",
    "Related material is referenced where it bears on what is described here.",
    "Points that are commonly misunderstood are called out directly.",
    "The reasoning is given so that it can be checked rather than taken on trust.",
    "Conditions that change the answer are named where they apply.",
    "What is out of scope is said plainly instead of left to inference.",
    "The account ends with the considerations that most often come up in practice.",
)


def placebo_body(sha: str, words: int) -> str:
    """Sentences from POOL, chosen by `sha`, to approximately `words` words.

    Deterministic and seedless: the sha IS the seed. Length is matched to the
    real enrichment because an unmatched control confounds length with content —
    the exact confound it is here to remove.
    """
    digest = hashlib.sha256(sha.encode("utf-8")).digest()
    out: list[str] = []
    count = 0
    for i in range(500):  # a bound rather than a `while True`
        pick = POOL[digest[i % len(digest)] % len(POOL)]
        n = len(pick.split())
        if count + n > words:
            # ⚠ **Stop at whichever side of the target is CLOSER**, rather than
            # always appending past it. Always overshooting gave the placebo a
            # systematic +8 % length bias over the real arm — which would
            # confound length with content, the one confound this control
            # exists to remove.
            if abs(count + n - words) < abs(count - words):
                out.append(pick)
            break
        out.append(pick)
        count += n
    return " ".join(out)


#: The frontmatter's `skill:` stamp, whatever skill version wrote it.
SKILL_LINE = re.compile(r"^skill:.*$", re.M)

#: A line's list marker, kept so a placebo line is shaped like the line it
#: replaces. `is_question` strips the same characters.
BULLET = re.compile(r"^\s*[-*]\s+")


def placebo_lines(sha: str, body: str) -> str:
    """One placebo line per non-empty `body` line, each matched to that line's
    word count — W-257's amendment (2026-10-10).

    ⚠ **Why per line.** Question-shaped enrichment is one question per line, and
    the pre-registration matches the control on **line count** as well as
    length. `placebo_body` writes one paragraph, so it matches length and not
    lines. Each line is seeded by `sha` and its index, so the output stays
    deterministic and seedless, and each line holds **at least one sentence**:
    the closest-side stop would otherwise return nothing for a line shorter
    than half a sentence, and an empty line is a line the real arm does not have.
    """
    out: list[str] = []
    for i, line in enumerate(l for l in body.splitlines() if l.strip()):
        marker = BULLET.match(line)
        prefix = marker.group(0).strip() + " " if marker else ""
        words = len(BULLET.sub("", line).split())
        made = placebo_body(f"{sha}:{i}", words) or POOL[hashlib.sha256(f"{sha}:{i}".encode()).digest()[0] % len(POOL)]
        out.append(prefix + made)
    return "\n".join(out)


def main(src: Path, dst: Path, per_line: bool = False) -> int:
    files = sorted(src.glob("*.md"))
    if not files:
        print(f"no enrichment files in {src}", file=sys.stderr)
        return 2
    dst.mkdir(parents=True, exist_ok=True)
    for f in files:
        text = f.read_text(encoding="utf-8")
        head, _, body = text.partition("\n---\n") if text.startswith("---") else ("", "", text)
        head = (head + "\n---") if head else ""
        sha = f.stem
        target = len(body.split())
        made = placebo_lines(sha, body) if per_line else placebo_body(sha, target)
        # The marker is in the frontmatter, never in the body: a body marker
        # would be a term the real arm does not have, and the arms must differ
        # in content alone. ⚠ Any `skill:` stamp, not only `fux-enrich@1` — the
        # W-257 rung is stamped `skill: fux-enrich` and kept the real label.
        head = SKILL_LINE.sub("skill: placebo (SR-RS decision 15)", head)
        (dst / f.name).write_text(f"{head}\n{made}\n" if head else f"{made}\n", encoding="utf-8")
        print(f"{f.name}  real {target}w -> placebo {len(made.split())}w")
    print(f"\n{len(files)} placebo file(s) -> {dst}")
    print("NOT installed. Swap it in for a measurement arm, then restore.")
    return 0


if __name__ == "__main__":
    argv = sys.argv[1:]
    per_line = "--per-line" in argv
    argv = [a for a in argv if a != "--per-line"]
    if len(argv) != 2:
        print(__doc__.strip().splitlines()[-1], file=sys.stderr)
        raise SystemExit(2)
    raise SystemExit(main(Path(argv[0]), Path(argv[1]), per_line=per_line))
