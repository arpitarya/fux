"""The controls ADR-RS decision 15 is owed — the two built, and the seal.

`tools/quality-controls/` is owned by ADR-RS: a control belongs to the
measurement discipline, not to the feature it tests.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools" / "quality-controls"))

from placebo import POOL, placebo_body  # noqa: E402
from seal import SEALED_COUNT, split  # noqa: E402

IDS = [f"q{n:03d}" for n in range(1, 51)]


# --- the seal ---------------------------------------------------------------

def test_the_split_is_deterministic_and_order_independent():
    """L3. No seed to record, no `random`, and re-sorting the goldens file
    cannot silently change which queries are sealed."""
    a, _ = split(IDS)
    b, _ = split(list(reversed(IDS)))
    assert a == b
    assert split(IDS) == split(IDS)


def test_the_split_is_exhaustive_and_disjoint():
    sealed, visible = split(IDS)
    assert len(sealed) == SEALED_COUNT
    assert not set(sealed) & set(visible)
    assert set(sealed) | set(visible) == set(IDS)


def test_growing_the_set_is_a_RESEAL_not_an_append():
    """Membership changes when the corpus does, and that is deliberate.

    A seal is named by the corpus it was cut from. Pretending it is permanent
    across a growing set is how a "sealed" query quietly becomes one that was
    visible when somebody authored against it.
    """
    before, _ = split(IDS)
    after, _ = split(IDS + ["q051", "q052", "q053"])
    assert before != after, "a grown corpus must produce a new cut, not the old one"


# --- the placebo ------------------------------------------------------------

def test_the_placebo_is_deterministic():
    assert placebo_body("abc123", 100) == placebo_body("abc123", 100)


def test_the_placebo_matches_length_without_a_systematic_bias():
    """An early version always overshot the target and gave the arm a +8 %
    length bias — confounding length with content, the one confound it exists
    to remove. It now stops on whichever side of the target is closer.
    """
    deltas = [len(placebo_body(f"sha{i}", 100).split()) - 100 for i in range(40)]
    assert max(abs(d) for d in deltas) <= 12, deltas
    mean = sum(deltas) / len(deltas)
    assert abs(mean) <= 3, f"systematic length bias of {mean:+.1f} words"


def test_every_placebo_shares_one_vocabulary():
    """⚠ **The load-bearing property.** A placebo written *about an unrelated
    topic* would still be discriminative — its terms would match some documents
    better than others — and would measure something else entirely. Identical
    vocabulary across the corpus is what makes any remaining lift attributable
    to the PRESENCE of fluent text and nothing else.
    """
    pool_words = {w.lower().strip(".,") for s in POOL for w in s.split()}
    for sha in ("aaa", "bbb", "ccc", "ddd"):
        words = {w.lower().strip(".,") for w in placebo_body(sha, 110).split()}
        assert words <= pool_words, words - pool_words


def test_the_placebo_carries_no_document_specific_term():
    """It must not accidentally name anything: no digits, no capitalised nouns
    beyond a sentence opener. A placebo that says `Calder` is not a placebo."""
    body = placebo_body("deadbeef", 110)
    assert not any(ch.isdigit() for ch in body)
    for sentence in body.split(". "):
        for word in sentence.split()[1:]:
            assert not word[0].isupper(), f"proper-noun-shaped token: {word!r}"


# --- the decoys -------------------------------------------------------------

def test_the_decoys_are_well_formed_and_have_no_expected_answer():
    """A decoy with a `doc` would be a golden. The whole reason an agent may
    author these is that there is no correct answer to fit to."""
    path = ROOT / "tools" / "quality-controls" / "decoys.jsonl"
    rows = [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]

    assert len(rows) >= 15
    assert len({r["id"] for r in rows}) == len(rows), "duplicate decoy id"
    for r in rows:
        assert set(r) == {"id", "q"}, f"{r['id']} carries more than a question: {set(r)}"
        assert r["q"].strip() and not r["q"].endswith("?")


def test_the_controls_are_runnable_as_scripts():
    """They are tools, not library code — a control nobody can run is not one."""
    for script in ("placebo.py", "seal.py"):
        p = subprocess.run(
            [sys.executable, str(ROOT / "tools" / "quality-controls" / script)],
            capture_output=True, text=True,
        )
        assert p.returncode == 2, f"{script} should exit 2 with usage, got {p.returncode}"
