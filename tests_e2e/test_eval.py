"""Eval harness wired into the suite — baseline sanity + (from M6) the v2 gate."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "eval"))

from run_eval import EVAL_DIR, evaluate, load_pairs  # noqa: E402


def test_lexical_baseline_floor(ingested):
    """The harness works and lexical v1 clears a sane floor on the fixture pairs."""
    pairs = load_pairs(EVAL_DIR / "pairs.jsonl")
    assert len(pairs) >= 15
    metrics = evaluate(ingested, pairs, top=10, lexical_only=False)
    print("\n" + metrics.row("lexical-v1"))
    assert metrics.hit5 >= 0.6  # deliberate paraphrase pairs are allowed to miss
    assert metrics.mrr >= 0.4
