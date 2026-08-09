"""Eval harness wired into the suite — lexical baseline + the v2 ship gate."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent / "eval"))

from run_eval import EVAL_DIR, evaluate, load_pairs  # noqa: E402


def _model_bundled() -> bool:
    from fux.embed.model import DATA_PATH

    return DATA_PATH.is_file()


def test_lexical_baseline_floor(ingested):
    """The harness works and lexical v1 clears a sane floor on the fixture pairs."""
    pairs = load_pairs(EVAL_DIR / "pairs.jsonl")
    assert len(pairs) >= 15
    metrics = evaluate(ingested, pairs, top=10, lexical_only=True)
    print("\n" + metrics.row("lexical-v1"))
    assert metrics.hit5 >= 0.6  # deliberate paraphrase pairs are allowed to miss
    assert metrics.mrr >= 0.4


@pytest.mark.skipif(not _model_bundled(), reason="model bundle not built")
def test_hybrid_gate_beats_lexical(ingested):
    """The v2 ship gate (handoff 0003 DoD 5): hybrid ≥ lexical on hit@5 and MRR."""
    pairs = load_pairs(EVAL_DIR / "pairs.jsonl")
    lexical = evaluate(ingested, pairs, top=10, lexical_only=True)
    hybrid = evaluate(ingested, pairs, top=10, lexical_only=False)
    print("\n" + lexical.row("lexical") + "\n" + hybrid.row("hybrid"))
    assert hybrid.hit5 >= lexical.hit5
    assert hybrid.mrr >= lexical.mrr
