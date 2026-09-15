"""The bind that makes `CLAUDE.md`'s golden-key block legal.

[SR-LAW-0](../records/0002_LAW-0-authority.md) decision 1 says every rule is
stated in exactly one SR and every other artifact links to it. Decision 5 makes
one exception: **a generated view is permitted, and only while a test asserts
equality.** This file is that test, for
[SR-WORK-GOLDEN](../records/0066_WORK-golden.md) decision 1.

🔴 **Delete this file and `CLAUDE.md`'s block becomes an illegal restatement** —
a second normative-looking copy of the sealed-key prohibition that can drift from
the record while both still look correct. **The permission is the test, not the
generation**, and SR-WORK-GOLDEN's veto condition names this file's absence as a
reopen trigger.

**Why this rule gets a view at all, when most do not.** SR-WORK-GOLDEN decision 3:
Claude Code is restrained by `permissions.deny` and by the hook, but **Cowork
reads `CLAUDE.md` and does not read `records/`**. A link in `CLAUDE.md` would
cover nothing Cowork reaches, which is why row 17 of W-146 sat in the inbox for
three days rather than being resolved by an agent's own reading of a law.

**What is checked, and why each one:**

1. the block in `CLAUDE.md` equals what the record renders — the drift itself
2. the record carries exactly one `GOLDEN-TEXT` pair, and no other live document
   carries the marker — a second source in disguise
3. no *other* live document carries the block verbatim — the residue check, so a
   third copy cannot appear somewhere nobody greps. ⚠ It catches a COPY, never a
   paraphrase, for the reason `test_claude_md_laws.py` states at length
4. `work/golden/README.md` links to the record and does not restate the rule —
   decision 4, and the copy that existed before this record did
5. `CLAUDE.md`'s section says it is generated — the one thing a reader has to see
   before they edit the wrong file
"""

from __future__ import annotations

import importlib.util
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
CLAUDE_MD = ROOT / "CLAUDE.md"
RECORD = ROOT / "records" / "0066_WORK-golden.md"
GOLDEN_README = ROOT / "work" / "golden" / "README.md"
GENERATOR = ROOT / "scripts" / "gen-golden.py"

#: Directories that are not live documents. `archive/` above all: an archived
#: doc may carry the rule's old wording, and rewriting history to satisfy a
#: freshness rule is what the archive exists to prevent.
_SKIP_PARTS = frozenset({"archive", ".venv", "node_modules", ".git", "site-packages"})


def _gen():
    """`scripts/gen-golden.py` as a module. Imported by path because `scripts/`
    is not a package and must not become one for one test."""
    spec = importlib.util.spec_from_file_location("fux_gen_golden", GENERATOR)
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


# -- 1. the block and the record agree ---------------------------------------


def test_the_claude_md_golden_block_matches_the_record(gen):
    """The whole point. A failure here means someone edited the wrong file."""
    expected = gen.render()
    actual = gen.committed_block()
    assert actual == expected, (
        "CLAUDE.md's §Golden answer key block has drifted from "
        "records/0066_WORK-golden.md. The record is the source (SR-LAW-0 "
        "decision 1) — fix the record, then run "
        "`python scripts/gen-golden.py --write`."
    )


def test_the_generator_is_idempotent(gen):
    """Rendering twice gives the same bytes, so `--write` cannot oscillate."""
    assert gen.render() == gen.render()


# -- 2. one home, and nothing else declaring one -----------------------------


def test_the_record_carries_exactly_one_golden_text_block():
    text = RECORD.read_text(encoding="utf-8")
    assert text.count("<!-- GOLDEN-TEXT:BEGIN -->") == 1, RECORD.name
    assert text.count("<!-- GOLDEN-TEXT:END -->") == 1, RECORD.name


def test_only_the_record_declares_golden_text():
    """A GOLDEN-TEXT marker anywhere else is a second source of truth in
    disguise — the same defect `test_only_law_records_declare_law_text` names."""
    offenders = [
        p.relative_to(ROOT)
        for p in _live_markdown()
        if "<!-- GOLDEN-TEXT:BEGIN" in p.read_text(encoding="utf-8") and p != RECORD
    ]
    assert not offenders, f"GOLDEN-TEXT markers outside the record: {offenders}"


# -- 3. the residue check ----------------------------------------------------


def _record_form() -> str:
    """The block exactly as the record carries it — links unrewritten."""
    text = RECORD.read_text(encoding="utf-8")
    body = text.split("<!-- GOLDEN-TEXT:BEGIN -->", 1)[1]
    return body.split("<!-- GOLDEN-TEXT:END -->", 1)[0].strip("\n")


def test_no_verbatim_third_copy_of_the_prohibition_exists(gen):
    """The block, whole, appears in exactly two places and no more: its record
    (record-relative links) and `CLAUDE.md` (root-relative links).

    ⚠ **This catches a VERBATIM copy and nothing weaker, and the limit is the
    point rather than an oversight.** The realistic failure is the one that
    actually happened here — the paragraph pasted into a second document, then
    amended on one side only. A *paraphrase* is not caught, and writing a fuzzy
    matcher to close that would be choosing a similarity threshold nobody
    ratified. SR-LAW-0 §"What is gated, and what is not" says so plainly.
    """
    flat = {p: _flat(p.read_text(encoding="utf-8")) for p in _live_markdown()}
    record_form = _record_form()
    claude_form = gen.render()
    # The two `assert … in` lines stop the subset check below being satisfied
    # vacuously by a block that appears in neither file.
    assert _flat(record_form) in flat[RECORD], "the block is not in its own record"
    assert _flat(claude_form) in flat[CLAUDE_MD], "the block is not in CLAUDE.md"
    for form in (record_form, claude_form):
        phrase = _flat(form)
        holders = {p for p, t in flat.items() if phrase in t}
        extra = sorted(p.relative_to(ROOT) for p in holders - {RECORD, CLAUDE_MD})
        assert not extra, (
            f"the prohibition appears verbatim in {extra} — only its own record "
            f"and CLAUDE.md's generated block may carry it (SR-LAW-0 decision 1)"
        )


# -- 4. the README links rather than restating -------------------------------


def test_the_golden_readme_links_to_the_record(gen):
    """SR-WORK-GOLDEN decision 4. `work/golden/README.md` is the home of the
    PROCESS; it carried a second copy of the rule until 2026-09-15."""
    text = GOLDEN_README.read_text(encoding="utf-8")
    assert "0066_WORK-golden.md" in text, (
        "work/golden/README.md must link SR-WORK-GOLDEN — it is the record that "
        "states the rule the README used to restate"
    )


def test_the_golden_readme_does_not_restate_who_may_read_the_key():
    """The exact sentence the README carried, in the form it carried it. A
    check on the *idea* would be a paraphrase matcher; this is the copy."""
    flat = _flat(GOLDEN_README.read_text(encoding="utf-8"))
    for phrase in (
        "Arpit, Codex and ChatGPT may read it",
        "Who may read it:",
    ):
        assert phrase not in flat, (
            f"work/golden/README.md restates the readership rule ({phrase!r}) — "
            "SR-WORK-GOLDEN decision 4 says it links instead"
        )


# -- 5. the reader is told, before they edit the wrong file -------------------


def test_the_claude_md_section_declares_itself_generated(gen):
    text = CLAUDE_MD.read_text(encoding="utf-8")
    heading = next(
        line for line in text.split("\n") if line.startswith("## Golden answer key")
    )
    assert "generated" in heading.lower() and "not the source" in heading.lower(), (
        f"the section heading must say it is generated and not the source: {heading!r}"
    )
    assert "scripts/gen-golden.py" in text
    assert gen.BEGIN_LINE in text, "the opening marker must name the generator"
