"""The bind that makes every record's **Components** block legal.

[SR-LAW-0](../records/0002_LAW-0-authority.md) decision 1 says every rule is
stated in exactly one SR and every other artifact links to it. Decision 5 makes
one exception: **a generated view is permitted, and only while a test asserts
equality.** This file is that test, for the block
[`scripts/gen-components.py`](../scripts/gen-components.py) renders into every
record from the register's `OWNERSHIP` and `DESCRIBES` tables.

🔴 **Delete this file and every block becomes an illegal restatement** — a
second, authoritative-looking copy of who owns what, in eighty places, able to
drift from the register while each copy still looks correct. That is the exact
failure `owns`/`describes` exists to end, one level up.
[SR-WORK-OWNERSHIP](../records/0054_WORK-ownership.md) decision 14 names this
file's absence as a reopen trigger.

**What is checked, and why each one:**

1. every block equals what the tables render — the drift itself
2. the generator is idempotent, so `--write` cannot oscillate
3. the block sits directly under the frontmatter and above the `# ` heading —
   a block further down is one a reader scrolls past, which is how the register's
   own prose rule went unread for a year
4. every record that owns or is described HAS one, and a law with neither has
   none — a silently skipped record is a record that still names no files
5. every link inside a block resolves — `test_doc_links.py` covers it too, and
   both are cheap; this one names the generator when it fails
"""

from __future__ import annotations

import importlib.util
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SR_DIR = ROOT / "records"
GENERATOR = ROOT / "scripts" / "gen-components.py"

_LINK = re.compile(r"\]\(([^)\s]+)\)")


def _gen():
    """`scripts/gen-components.py` as a module. Imported by path because
    `scripts/` is not a package and must not become one for one test."""
    spec = importlib.util.spec_from_file_location("fux_gen_components", GENERATOR)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def gen():
    return _gen()


# -- 1. the blocks and the tables agree --------------------------------------


def test_every_block_matches_the_register(gen) -> None:
    """The whole point. A failure here means someone edited the wrong file."""
    stale = [
        path.name
        for path, body in gen.blocks().items()
        if gen.current(path) != body
    ]
    assert not stale, (
        f"{len(stale)} record(s) carry a stale Components block: {stale[:8]}"
        f"{' …' if len(stale) > 8 else ''}\n"
        "The register's tables are the source (SR-WORK-OWNERSHIP decision 2) — fix "
        "the table, then run `python scripts/gen-components.py --write && "
        "python scripts/sr-hash.py --write`."
    )


def test_there_are_blocks_to_check(gen) -> None:
    """A collector that silently matches nothing is a test that always passes."""
    rendered = [b for b in gen.blocks().values() if b is not None]
    assert len(rendered) > 50, f"only {len(rendered)} records render a block — the walk is wrong"


# -- 2. the generator is stable ----------------------------------------------


def test_the_generator_is_idempotent(gen) -> None:
    assert gen.blocks() == gen.blocks()


def test_applying_a_block_twice_changes_nothing(gen) -> None:
    """`apply` is what `--write` runs; a second pass must be a no-op."""
    for path, body in gen.blocks().items():
        text = path.read_text(encoding="utf-8")
        assert gen.apply(gen.apply(text, body), body) == gen.apply(text, body), path.name


# -- 3. the block is where a reader will see it ------------------------------


def test_the_block_sits_between_the_frontmatter_and_the_heading(gen) -> None:
    """Directly under the metadata, above `# SR-NAME`. Nowhere else."""
    misplaced = []
    for path, body in gen.blocks().items():
        text = path.read_text(encoding="utf-8")
        if body is None:
            assert gen.BEGIN not in text, f"{path.name} carries a block it should not have"
            continue
        start = text.index(gen.BEGIN)
        end = text.index(gen.END)
        heading = text.index("\n# ")
        fm_end = gen._frontmatter_end(text)
        if not (fm_end <= start < end < heading):
            misplaced.append(path.name)
    assert not misplaced, (
        f"the Components block is not between the frontmatter and the `# ` heading "
        f"in: {misplaced}"
    )


def test_the_marker_names_the_generator(gen) -> None:
    for path, body in gen.blocks().items():
        if body is None:
            continue
        assert gen.BEGIN_LINE in path.read_text(encoding="utf-8"), path.name


# -- 4. nothing is silently skipped ------------------------------------------


def test_every_record_that_owns_or_is_described_has_a_block(gen) -> None:
    owns, describes = gen.owns_by_record(), gen.describes_by_record()
    missing = [
        path.name
        for path, body in gen.blocks().items()
        if body is None and (owns.get(_name(path)) or describes.get(_name(path)))
    ]
    assert not missing, f"these records name components but render no block: {missing}"


def test_only_a_law_may_have_no_block(gen) -> None:
    """A law governs conduct, not components — every other record says something,
    even if what it says is that it owns nothing."""
    wrong = [
        path.name
        for path, body in gen.blocks().items()
        if body is None and gen._kind_of(path) != "law"
    ]
    assert not wrong, f"these non-law records render no block: {wrong}"


def _name(path: Path) -> str:
    m = re.search(r"^name:\s*(SR-[A-Z0-9-]+)\s*$", path.read_text(encoding="utf-8"), re.M)
    assert m, f"{path.name} has no `name:` in its frontmatter"
    return m.group(1)


# -- 5. the links resolve ----------------------------------------------------


def test_every_link_in_a_block_resolves(gen) -> None:
    broken = []
    for path, body in gen.blocks().items():
        if not body:
            continue
        for target in _LINK.findall(body):
            if not (path.parent / target.split("#")[0]).exists():
                broken.append(f"{path.name} -> {target}")
    assert not broken, (
        "these Components links point at nothing:\n  " + "\n  ".join(broken)
        + "\n\nA path that moved must move in records/README.md's table first."
    )
