"""Phase-2 recall rerank — $0 char-trigram fallback (no sentence-transformers)."""
from __future__ import annotations

from fux import embed
from fux.model import Rule


def _rule(rid: str, body: str) -> Rule:
    from pathlib import Path
    return Rule(id=rid, type="rule", fm={"id": rid}, body=body, path=Path("x.md"), layer="project")


def test_rerank_disabled_is_identity():
    cands = [(_rule("a", "alpha"), 2.0), (_rule("b", "beta"), 1.0)]
    assert embed.rerank("anything", cands, {"recall_rerank": False}) == cands


def test_rerank_promotes_semantically_closer_candidate():
    # Two candidates tied-ish lexically; the trigram-closer one should win.
    cands = [
        (_rule("greeting", "a cheerful unrelated note about weather"), 1.0),
        (_rule("portfolio-valuation", "portfolio valuation total value"), 1.0),
    ]
    ranked = embed.rerank("portfolio valuation", cands, {"recall_rerank": True})
    assert ranked[0][0].id == "portfolio-valuation"


def test_ngram_cosine_self_is_one():
    g = embed._ngrams("valuation")
    assert abs(embed._cosine(g, g) - 1.0) < 1e-9
