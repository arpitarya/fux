"""BM25F field weighting + deterministic query expansion (plan §17.18a/b)."""
from __future__ import annotations

from fux import recall
from tests.conftest import write_rule


def _seed_glossary(project):
    write_rule(project, "pnl", "---\nid: pnl\ntype: glossary\nstatus: active\n"
               "keywords: [earnings, gains]\n---\n**Term:** profit and loss.\n")
    write_rule(project, "day-calc", "---\nid: day-calc\ntype: formula\nstatus: active\n"
               "---\n**Rule:** computes earnings for the trading day.\n")


def test_bm25f_weights_id_field_above_body(project):
    # 'widget' as an id should outrank 'widget' buried once in another rule's body.
    write_rule(project, "widget", "---\nid: widget\ntype: rule\nstatus: active\n"
               "---\n**Rule:** a small reusable thing.\n")
    write_rule(project, "other", "---\nid: other\ntype: rule\nstatus: active\n"
               "---\n**Rule:** mentions a widget in passing among many other words here.\n")
    ranked = recall.run(project, "widget", top=2)
    assert ranked[0][0].id == "widget"


def test_expand_terms_pulls_glossary_synonyms(project):
    _seed_glossary(project)
    rules = recall.loader.resolve(project, recall.config.load(
        (project / ".fux" / "config.toml"))).active()
    extra = recall.expand_terms(rules, "pnl")
    assert {"profit", "loss", "earnings", "gains"} <= extra


def test_expansion_surfaces_a_synonym_only_match(project):
    _seed_glossary(project)
    base = [r.id for r, _ in recall.run(project, "pnl", top=5, expand=False)]
    expanded = [r.id for r, _ in recall.run(project, "pnl", top=5, expand=True)]
    assert "day-calc" not in base          # 'pnl' never appears in day-calc
    assert "day-calc" in expanded          # reached via glossary synonym 'earnings'
