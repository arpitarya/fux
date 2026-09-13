"""The bind that makes `CLAUDE.md`'s law block legal.

[SR-LAW-0](../records/0002_LAW-0-authority.md) decision 1 says every rule is
stated in exactly one SR and every other artifact links to it. Decision 5 makes
one exception: **a generated view is permitted, and only while a test asserts
equality.** This file is that test.

🔴 **Delete this file and `CLAUDE.md`'s block becomes an illegal restatement** —
a second normative-looking copy of eleven laws that can drift from the records while
both still look correct, which is the exact failure L0 exists to end. The
permission is the test, not the generation. SR-LAW-0's veto condition 2 names
this file's absence as a reopen trigger.

**What is checked, and why each one:**

1. the block in `CLAUDE.md` equals what the records render — the drift itself
2. every handle `L0`–`L10` has exactly one record, and no record has two — a law
   with no home, or two homes, is the same defect as drift one step earlier
3. no *other* live document carries a law's block verbatim — the residue check,
   so a third copy cannot appear somewhere nobody greps. ⚠ It catches a COPY,
   never a paraphrase; the test says why, and SR-LAW-0 says paraphrase is
   ungated
4. `SR-LAWS` routes every handle — a law that exists but is unreachable from
   the router is a law nobody will find
5. `CLAUDE.md`'s section says it is generated — the one thing a reader has to
   see before they edit the wrong file
"""

from __future__ import annotations

import importlib.util
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
CLAUDE_MD = ROOT / "CLAUDE.md"
SR_DIR = ROOT / "records"
GENERATOR = ROOT / "scripts" / "gen-laws.py"

#: Directories that are not live documents. `archive/` above all: an archived
#: doc may carry a law's old wording, and rewriting history to satisfy a
#: freshness rule is what the archive exists to prevent.
_SKIP_PARTS = frozenset({"archive", ".venv", "node_modules", ".git", "site-packages"})


def _gen():
    """`scripts/gen-laws.py` as a module. Imported by path because `scripts/` is
    not a package and must not become one for one test."""
    spec = importlib.util.spec_from_file_location("fux_gen_laws", GENERATOR)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def gen():
    return _gen()


def _live_markdown() -> list[Path]:
    out = []
    for path in ROOT.rglob("*.md"):
        rel = path.relative_to(ROOT)
        if _SKIP_PARTS & set(rel.parts):
            continue
        out.append(path)
    return sorted(out)


def _flat(text: str) -> str:
    """Whitespace-collapsed, so a phrase that is line-wrapped differently in two
    files still compares equal. Wrapping is not a difference anyone means."""
    return re.sub(r"\s+", " ", text)


# -- 1. the block and the records agree --------------------------------------


def test_the_claude_md_law_block_matches_the_records(gen):
    """The whole point. A failure here means someone edited the wrong file."""
    expected = gen.render()
    actual = gen.committed_block()
    assert actual == expected, (
        "CLAUDE.md's law block has drifted from records/*_LAW-*.md. The records "
        "are the source (SR-LAW-0 decision 1) — fix the record, then run "
        "`python scripts/gen-laws.py --write`."
    )


def test_the_generator_is_idempotent(gen, tmp_path):
    """Rendering twice gives the same bytes, so `--write` cannot oscillate."""
    assert gen.render() == gen.render()


# -- 2. one home per law, and every law has one ------------------------------


def test_every_handle_has_exactly_one_record(gen):
    records = gen.law_records()
    assert sorted(records) == sorted(gen.LAW_ORDER), (
        f"law records declare {sorted(records)}, expected {sorted(gen.LAW_ORDER)}"
    )


def test_no_record_carries_two_law_blocks():
    """`law_records()` raises on a second block; this asserts the shape directly
    so the failure names the file rather than the loader."""
    for path in sorted(SR_DIR.glob("*_LAW-*.md")):
        text = path.read_text(encoding="utf-8")
        assert text.count("<!-- LAW-TEXT:BEGIN ") == 1, path.name
        assert text.count("<!-- LAW-TEXT:END ") == 1, path.name


def test_only_law_records_declare_law_text():
    """A LAW-TEXT marker anywhere else is a fourth source of truth in disguise."""
    offenders = [
        p.relative_to(ROOT)
        for p in _live_markdown()
        if "<!-- LAW-TEXT:BEGIN " in p.read_text(encoding="utf-8")
        and not re.match(r"\d{4}_LAW-\d+-", p.name)
    ]
    assert not offenders, f"LAW-TEXT markers outside the law records: {offenders}"


# -- 3. the residue check ----------------------------------------------------


def _record_form(path: Path, handle: str) -> str:
    """One law's block exactly as its record carries it — links unrewritten."""
    text = path.read_text(encoding="utf-8")
    body = text.split(f"<!-- LAW-TEXT:BEGIN {handle} -->", 1)[1]
    return body.split(f"<!-- LAW-TEXT:END {handle} -->", 1)[0].strip("\n")


def test_no_verbatim_third_copy_of_a_law_exists(gen):
    """A law's block, whole, appears in exactly two places and no more: its
    record (record-relative links) and `CLAUDE.md` (root-relative links).

    ⚠ **This catches a VERBATIM copy and nothing weaker, and the limit is the
    point rather than an oversight.** The realistic failure is a section pasted
    into a second document and then amended on one side only — which is what
    happened to the laws for the whole of their life before L0. A *paraphrase* is
    not caught here and is not caught anywhere: SR-LAW-0 §"What is gated, and
    what is not" says so plainly, and writing a fuzzy matcher to close it would
    be choosing a similarity threshold nobody ratified — the moving-threshold
    failure in another costume.

    **Why not a shorter, more sensitive phrase.** A law's opening bolded
    statement *is* its handle for the short laws (L5's is five words), and
    SR-LAWS' table is required to carry the handle. A check on that phrase fires
    on the router doing its job, and the only way to keep it green is to stop
    routing.
    """
    flat = {p: _flat(p.read_text(encoding="utf-8")) for p in _live_markdown()}
    records = gen.law_records()
    for handle in gen.LAW_ORDER:
        owner = records[handle]
        # ⚠ **The two forms are the same bytes for a law that carries no link**
        # (L2, L4–L7), so the expectation is a SUBSET rather than one file — and
        # the two `assert … in` lines below are what stop that subset being
        # satisfied vacuously by a law that appears in neither.
        record_form = _record_form(owner, handle)
        claude_form = gen.law_text(owner, handle)
        assert _flat(record_form) in flat[owner], f"{handle} is not in {owner.name}"
        assert _flat(claude_form) in flat[CLAUDE_MD], f"{handle} is not in CLAUDE.md"
        for form in (record_form, claude_form):
            phrase = _flat(form)
            holders = {p for p, t in flat.items() if phrase in t}
            extra = sorted(p.relative_to(ROOT) for p in holders - {owner, CLAUDE_MD})
            assert not extra, (
                f"{handle}'s block appears verbatim in {extra} — only its own "
                f"record and CLAUDE.md's generated block may carry it "
                f"(SR-LAW-0 decision 1)"
            )


# -- 4. the router routes ----------------------------------------------------


def test_sr_laws_routes_every_handle(gen):
    """`SR-LAWS` is the index. A law missing from its table is unreachable."""
    text = (SR_DIR / "0001_LAWS.md").read_text(encoding="utf-8")
    records = gen.law_records()
    for handle in gen.LAW_ORDER:
        row = f"| **{handle}** |"
        assert row in text, f"SR-LAWS has no table row for {handle}"
        assert records[handle].name in text, (
            f"SR-LAWS' {handle} row does not link {records[handle].name}"
        )


# -- 5. the reader is told, before they edit the wrong file -------------------


def test_the_claude_md_section_declares_itself_generated(gen):
    text = CLAUDE_MD.read_text(encoding="utf-8")
    heading = next(
        line for line in text.split("\n") if line.startswith("## Non-negotiable constraints")
    )
    assert "generated" in heading.lower() and "not the source" in heading.lower(), (
        f"the section heading must say it is generated and not the source: {heading!r}"
    )
    assert "scripts/gen-laws.py" in text
    assert gen.BEGIN_LINE in text, "the opening marker must name the generator"
