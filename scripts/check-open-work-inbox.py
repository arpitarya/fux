#!/usr/bin/env python3
"""fux — validates the "Blocked on Arpit" section of work/OPEN-WORK.md against
SR-WORK-OPEN-QUEUE rule 45a: when the inbox table carries no rows, the line
directly beneath it is exactly one `*Empty since YYYY-MM-DD ...*` declaration
(one logical sentence — it may soft-wrap across physical lines) and nothing
else: no recap prose, no restated rulings.

Read-only. Exits 0 (silent) if the section is well-formed or absent. Exits 1
with a one-line reason on stdout if it is not — the caller decides what to do
with that (block, or just print it).

records/0051_WORK-open-queue.md rule 45a is the rule; this is one of its
enforcing checks (see also tests/test_open_work_is_not_stale.py and
tests/test_open_work_rows_are_short.py, which this mirrors for the hook
surfaces). This script states no rule of its own.
"""
import re
import sys
from pathlib import Path

EMPTY_RE = re.compile(r"^\*Empty since \d{4}-\d{2}-\d{2}\b.*\*$")


def find_repo_root(start: Path):
    p = start.resolve()
    for candidate in [p, *p.parents]:
        if (candidate / "work" / "OPEN-WORK.md").is_file():
            return candidate
    return None


def paragraphs(lines):
    """Split a list of lines into paragraphs (runs separated by blank lines)."""
    out, cur = [], []
    for l in lines:
        if l.strip():
            cur.append(l)
        elif cur:
            out.append(cur)
            cur = []
    if cur:
        out.append(cur)
    return out


def check(open_work: Path):
    """Return an error message, or None if the section is fine."""
    lines = open_work.read_text().splitlines()
    try:
        start = next(i for i, l in enumerate(lines) if l.strip() == "## Blocked on Arpit")
    except StopIteration:
        return None  # section not found — not this check's problem
    try:
        end = start + 1 + next(
            i for i, l in enumerate(lines[start + 1:]) if l.strip() == "---"
        )
    except StopIteration:
        return "rule 45a: '## Blocked on Arpit' has no closing '---' — section is unterminated"

    paras = paragraphs(lines[start + 1:end])
    if not paras or not paras[0][0].startswith("|") or len(paras[0]) < 2 or not paras[0][1].startswith("|"):
        return "rule 45a: 'Blocked on Arpit' is missing its table header/separator row"

    table_para = paras[0]
    extra_table_rows = table_para[2:]  # rows appended directly under the separator, no blank line
    rest_paras = paras[1:]

    if extra_table_rows and all(l.startswith("|") for l in extra_table_rows) and not rest_paras:
        return None  # real rows, nothing further — fine

    if not extra_table_rows and not rest_paras:
        return (
            "rule 45a: the inbox table is empty but has no "
            "'*Empty since YYYY-MM-DD ...*' declaration beneath it"
        )

    if not extra_table_rows and len(rest_paras) == 1:
        sentence = " ".join(l.strip() for l in rest_paras[0])
        if EMPTY_RE.match(sentence):
            return None  # correctly declared empty (may soft-wrap)

    found = " / ".join(" ".join(p) for p in ([extra_table_rows] if extra_table_rows else []) + rest_paras)
    return (
        "rule 45a: 'Blocked on Arpit' carries content beyond the table and its "
        "one '*Empty since YYYY-MM-DD ...*' line — found: " + repr(found)
    )


def main():
    root = find_repo_root(Path.cwd())
    if root is None:
        return 0  # not in this repo — nothing to check
    open_work = root / "work" / "OPEN-WORK.md"
    if not open_work.is_file():
        return 0
    error = check(open_work)
    if error is None:
        return 0
    print(f"work/OPEN-WORK.md — {error} (see records/0051_WORK-open-queue.md rule 45a)")
    return 1


if __name__ == "__main__":
    sys.exit(main())
