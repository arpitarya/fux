"""`fux savings` — measured token-cost estimate ($0, plan §12)."""
from __future__ import annotations

from fux import savings
from conftest import write_rule

RULE = """---
id: day-pnl
domain: portfolio
type: formula
status: active
created: 2026-06-01
updated: 2026-06-01
code_refs:
  - src/agg.py#L1-L2
---
**Rule:** Today's P&L uses current INR value, not invested cost.
"""


def _seed(project, big_lines: int = 400):
    # A governed file much larger than the rule that documents it.
    (project / "src" / "agg.py").write_text(
        "def day_pnl(h):\n" + "    x = 0\n" * big_lines, encoding="utf-8")
    write_rule(project, "day-pnl", RULE)


def test_aggregate_reports_measured_corpus(project):
    _seed(project)
    rep = savings.build(project)
    assert rep.n_rules == 1
    assert rep.index_tok > 0
    assert rep.topics == 1
    assert rep.governed_files == 1
    # The governed file is far larger than the rule → a real saving multiplier.
    assert rep.avg_without > rep.avg_rule
    assert rep.avg_ratio() > 1.0


def test_query_lookup_compares_with_vs_without(project):
    _seed(project)
    rep = savings.build(project, query="how is day pnl computed", top=3)
    lk = rep.lookup
    assert lk is not None and any(r.id == "day-pnl" for r in lk.rules)
    assert lk.without > lk.with_first > lk.with_later
    assert lk.ratio_later() > lk.ratio_first() > 1.0


def test_missing_code_ref_excluded_not_counted(project):
    write_rule(project, "ghost", RULE.replace("src/agg.py#L1-L2", "src/gone.py"))
    rep = savings.build(project)
    assert rep.topics == 0          # no existing governed file
    assert rep.governed_files == 0
    assert any("baseline" in n for n in rep.notes)


def test_render_is_stringable(project):
    _seed(project)
    text = savings.render(savings.build(project, query="day pnl"))
    assert "fux savings" in text and "cheaper" in text


def test_usd_conversion_math():
    assert savings.usd(1_000_000, 5.0) == 5.0
    assert savings.usd(500_000, 10.0) == 5.0
    assert savings.fmt_usd(12.5) == "$12.50"        # cents once past a dollar
    assert savings.fmt_usd(0.003) == "$0.0030"      # 4 dp below a cent


def test_render_shows_dollars(project):
    _seed(project)
    rep = savings.build(project, query="day pnl")
    assert rep.usd_per_mtok == savings.DEFAULT_USD_PER_MTOK
    text = savings.render(rep)
    assert "$" in text and "/M input tok" in text and "you save" in text


def test_usd_per_mtok_config_override(project):
    _seed(project)
    cfg = project / ".fux" / "config.toml"
    cfg.write_text(cfg.read_text().replace("usd_per_mtok = 5.0", "usd_per_mtok = 10.0"),
                   encoding="utf-8")
    rep = savings.build(project)
    assert rep.usd_per_mtok == 10.0
    # Same tokens, double the price → double the dollars on the aggregate baseline.
    assert savings.usd(rep.avg_without, 10.0) == 2 * savings.usd(rep.avg_without, 5.0)
