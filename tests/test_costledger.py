"""Cumulative cost ledger — per-lookup savings accumulate into cost.json (§12)."""
from __future__ import annotations

import datetime as _dt

from fux import costledger, recall
from tests.conftest import write_rule


def _seed(project):
    (project / "src").mkdir(exist_ok=True)
    # a big governed file → reading it (without Fux) is expensive
    (project / "src" / "agg.py").write_text("x = 1\n" * 400, encoding="utf-8")
    write_rule(project, "day-pnl", "---\nid: day-pnl\ntype: formula\nstatus: active\n"
               "keywords: [pnl, profit]\ncode_refs:\n  - src/agg.py\n"
               "---\n**Rule:** profit today. **Why:** current value.\n")


def test_record_accumulates(project):
    _seed(project)
    from fux import loader, config, paths
    rules = loader.resolve(project, config.load(paths.Footprint(project).config)).active()
    costledger.record(project, "pnl", rules, today=_dt.date(2026, 6, 5))
    costledger.record(project, "profit", rules, today=_dt.date(2026, 6, 5))
    led = costledger.load(project)
    assert led["lookups"] == 2
    assert led["tokens_without"] > led["tokens_with"]      # big file vs small rule
    assert led["tokens_saved"] == led["tokens_without"] - led["tokens_with"]
    assert led["first"] == "2026-06-05" and len(led["recent"]) == 2


def test_recall_records_when_enabled(project):
    _seed(project)
    cfg = project / ".fux" / "config.toml"
    cfg.write_text(cfg.read_text().replace("cost_tracking = false", "cost_tracking = true")
                   if "cost_tracking" in cfg.read_text()
                   else cfg.read_text() + "\ncost_tracking = true\n")
    recall.run(project, "profit", top=3)
    led = costledger.load(project)
    assert led["lookups"] == 1 and led["tokens_saved"] > 0


def test_reset_and_summary(project):
    _seed(project)
    from fux import loader, config, paths
    rules = loader.resolve(project, config.load(paths.Footprint(project).config)).active()
    costledger.record(project, "q", rules)
    assert "Cumulative" in costledger.render_summary(costledger.load(project))
    costledger.reset(project)
    assert costledger.load(project)["lookups"] == 0
    assert costledger.render_summary(costledger.load(project)) == ""


def test_rates_amortise_over_span(project):
    _seed(project)
    from fux import loader, config, paths
    rules = loader.resolve(project, config.load(paths.Footprint(project).config)).active()
    # span 2026-06-05 → 2026-06-13 is 8 days
    costledger.record(project, "a", rules, today=_dt.date(2026, 6, 5))
    costledger.record(project, "b", rules, today=_dt.date(2026, 6, 13))
    led = costledger.load(project)
    assert costledger.span_days(led) == 8
    r = costledger.rates(led)
    assert r["day"] == led["tokens_saved"] / 8
    assert r["week"] == r["day"] * 7
    assert r["month"] > r["week"] > r["day"] > 0     # ascending, all positive
    out = costledger.render_summary(led)
    for label in ("saved per day", "saved per week", "saved per month", "avg over 8 day(s)"):
        assert label in out


def test_span_floored_to_one_day(project):
    """A same-day ledger (first == last) yields span 1, not a divide-by-zero."""
    _seed(project)
    from fux import loader, config, paths
    rules = loader.resolve(project, config.load(paths.Footprint(project).config)).active()
    costledger.record(project, "a", rules, today=_dt.date(2026, 6, 5))
    led = costledger.load(project)
    assert costledger.span_days(led) == 1
    r = costledger.rates(led)
    assert r["day"] == led["tokens_saved"] and r["week"] == led["tokens_saved"] * 7
