"""Every frozen rung still carries the seed corpus this repo actually has.

**Two strikes, so a gate** — [SR-WORK-SESSION](../records/0060_WORK-session.md)
decision 13. The failure class is *the golden ladder drifts and nothing
detects it*:

1. **2026-09-15, W-186** — a format bump and two retired config keys had made
   all eight rungs unreadable for nine days. *"Nothing detected it. No test,
   hook or CI arm reads a rung."*
2. **2026-09-15, W-136 prompt 4** — seven of the twenty documents in
   `work/golden/seed/` grew by 131 lines, and all eight rungs went on holding
   the OLD text. `ladder_check.py` passed, `rungs.verify()` passed, every
   manifest matched its corpus byte for byte. They only ever compare the ladder
   against itself.

🔴 **A stale rung does not fail loudly.** It answers questions written against
words it does not contain, and returns a number shaped exactly like a real one
— the same hazard [L11](../records/0012_LAW-11-sealed-answer-key.md) names for
the key. So the check is mechanical and runs in the fast suite.

**It reads `work/golden/seed/` and `work/golden/ladder/` only** — the two
directories L11 leaves open — and needs no corpus, so it runs on a clean clone.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools" / "differential"))

import rungs  # noqa: E402


def test_the_ladder_declares_rungs_at_all():
    """A ladder that vanished would make every check below vacuously green."""
    assert rungs.rung_names(), f"no rung manifests in {rungs.LADDER}"


def test_the_seed_corpus_is_where_the_rungs_copy_it_from():
    live = rungs.seed_documents()
    assert live, f"no seed documents under {rungs.SEED}"
    assert all(rel.startswith("seed/") for rel in live)


@pytest.mark.parametrize("name", rungs.rung_names())
def test_no_rung_carries_a_stale_seed_document(name):
    problems = rungs.seed_drift(name)
    assert not problems, (
        f"{name} was frozen against a different work/golden/seed/ than this repo "
        f"now has. Rebuild it — work/golden/prompts/4-claude-corpus.md:\n  "
        + "\n  ".join(problems)
    )
