"""Recall evaluation set — paraphrase queries vs expected rule (plan §10.11/§17.4).

A LoCoMo/LongMemEval-style labelled set: a corpus of rules and paraphrased queries
whose answer shares no verbatim id token. Validates the default `$0` lexical path
and the opt-in RRF hybrid path with recall@k + MRR. No API, no network.
"""
from __future__ import annotations

from fux import bench, embed, recall
from fux.hybrid import fuse
from conftest import write_rule

# id -> (frontmatter extra, body)
CORPUS = {
    "day-pnl": ("domain: portfolio\nkeywords: [pnl, profit, loss, today, gain]\n",
                "Today's profit or loss is computed on current market value, not invested cost."),
    "inr-normalization": ("domain: portfolio\nkeywords: [currency, forex, rupee, dollar]\n",
                          "Foreign-currency holdings convert to Indian rupees before they are summed."),
    "xirr": ("domain: portfolio\nkeywords: [return, annualized, irr, performance]\n",
             "Annualised internal rate of return across dated cashflows."),
    "api-key-hashing": ("domain: security\nkeywords: [secret, hash, credential, token]\n",
                        "Secrets are hashed before they are written to storage."),
    "avg-cost-basis": ("domain: portfolio\nkeywords: [cost, basis, average, buy]\n",
                       "Cost basis uses the average purchase price across all buy lots."),
    "market-hours": ("domain: markets\nkeywords: [session, nse, timing, open, close]\n",
                     "Indian equity sessions run 9:15 to 15:30 IST on trading days."),
    "stcg-ltcg": ("domain: tax\nkeywords: [capital, gains, holding, period, tax]\n",
                  "Short-term vs long-term capital gains split at a one-year holding period."),
    "broker-zero-holdings": ("domain: brokers\nkeywords: [broker, empty, dump, silent]\n",
                             "A broker source may silently return zero holdings on a failed sync."),
}

# (paraphrased query, expected id) — none share the id verbatim.
EVAL = [
    ("how much did my holdings earn or lose today", "day-pnl"),
    ("what was my gain or loss for the day", "day-pnl"),
    ("converting dollars to rupees before adding them up", "inr-normalization"),
    ("normalise foreign currency to INR first", "inr-normalization"),
    ("annualised rate of return on my investments", "xirr"),
    ("where do we hash credentials before saving", "api-key-hashing"),
    ("how is the average buy price used for cost", "avg-cost-basis"),
    ("when does the NSE trading session open and close", "market-hours"),
    ("difference between short and long term capital gains", "stcg-ltcg"),
    ("a broker returning empty holdings after a sync failure", "broker-zero-holdings"),
]


def _seed(project):
    for rid, (fm, body) in CORPUS.items():
        write_rule(project, rid, f"---\nid: {rid}\ntype: rule\nstatus: active\n"
                   f"created: 2026-06-01\nupdated: 2026-06-01\n{fm}---\n**Rule:** {body}\n")


def _results(project, ranker):
    return [([r.id for r in ranker(q)], expected) for q, expected in EVAL]


def test_lexical_recall_meets_thresholds(project):
    _seed(project)
    res = _results(project, lambda q: [r for r, _ in recall.run(project, q, top=5)])
    rep = bench.report(res)
    assert rep["recall@1"] >= 0.8 and rep["recall@3"] >= 0.9 and rep["mrr"] >= 0.85


def test_hybrid_does_not_regress_recall(project):
    _seed(project)
    rules = lambda q: [r for r, _ in recall.run(project, q, top=5)]
    rules_h = lambda q: [r for r, _ in recall.run(project, q, top=5, hybrid=True)]
    base = bench.recall_at_k(_results(project, rules), 3)
    hyb = bench.recall_at_k(_results(project, rules_h), 3)
    assert hyb >= base


def test_metrics_are_well_formed():
    res = [(["a", "b", "c"], "b"), (["x", "y"], "x")]
    assert bench.recall_at_k(res, 1) == 0.5
    assert bench.recall_at_k(res, 3) == 1.0
    assert abs(bench.mrr(res) - ((0.5) + 1.0) / 2) < 1e-9
