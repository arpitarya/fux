"""Recall evaluation set — paraphrase queries vs expected top rule (plan §10.11).

Validates both the default $0 lexical path and the opt-in local rerank against a
small labelled corpus, so the phase-2 re-rank can be promoted with evidence
rather than by assertion. No API, no network.
"""
from __future__ import annotations

from fux import embed, recall
from conftest import write_rule

CORPUS = {
    "day-pnl": (
        "domain: portfolio\nkeywords: [pnl, profit, loss, today, gain]\n",
        "Today's profit or loss is computed on current market value, not invested cost.",
    ),
    "inr-normalization": (
        "domain: portfolio\nkeywords: [currency, forex, rupee, dollar, normalize]\n",
        "Foreign-currency holdings convert to Indian rupees before they are summed.",
    ),
    "xirr": (
        "domain: portfolio\nkeywords: [return, annualized, irr, performance]\n",
        "Annualised internal rate of return across dated cashflows.",
    ),
    "api-key-hashing": (
        "domain: security\nkeywords: [secret, hash, credential, token]\n",
        "Secrets are hashed before they are written to storage.",
    ),
}

# (paraphrased query, expected top rule id) — none share the rule id verbatim.
EVAL = [
    ("how much did my holdings earn or lose today", "day-pnl"),
    ("converting dollars to rupees before adding them up", "inr-normalization"),
    ("annualised rate of return on my investments", "xirr"),
    ("where do we hash credentials before saving", "api-key-hashing"),
]


def _seed(project):
    for rid, (fm, body) in CORPUS.items():
        write_rule(project, rid, f"---\nid: {rid}\ntype: rule\nstatus: active\n"
                   f"created: 2026-06-01\nupdated: 2026-06-01\n{fm}---\n**Rule:** {body}\n")


def _recall_at_1(project, rerank: bool) -> float:
    hits = 0
    for query, expected in EVAL:
        ranked = recall.run(project, query, top=3)
        if rerank:
            ranked = embed.rerank(query, ranked, {"recall_rerank": True})
        if ranked and ranked[0][0].id == expected:
            hits += 1
    return hits / len(EVAL)


def test_lexical_recall_at_1_is_perfect(project):
    _seed(project)
    assert _recall_at_1(project, rerank=False) == 1.0


def test_local_rerank_does_not_regress(project):
    _seed(project)
    assert _recall_at_1(project, rerank=True) >= _recall_at_1(project, rerank=False)
