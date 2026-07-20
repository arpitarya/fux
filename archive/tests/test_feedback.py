"""`fux feedback` — the §18.4 generation-outcome learning loop ($0)."""
from __future__ import annotations

from fux import feedback


def test_record_then_summarise_acceptance_and_reasons(project):
    feedback.record(project, {"prompt": "net worth card", "valid": True, "attempts": 1})
    feedback.record(project, {"prompt": "risk panel", "valid": True, "attempts": 2})
    feedback.record(project, {"prompt": "evil", "valid": False, "attempts": 2,
                              "errors": ["$: unknown component 'Hacker'"]})
    rows = feedback.load(project)
    assert len(rows) == 3
    text = feedback.render(rows)
    assert "3 compose(s): 2 valid (66%), 1 on first try" in text
    assert "unknown component" in text                      # rejection reason rolled up


def test_render_empty_is_friendly(project):
    assert "no generation outcomes" in feedback.render(feedback.load(project))


def test_prompt_is_truncated_and_ts_added(project):
    rec = feedback.record(project, {"prompt": "x" * 500, "valid": True})
    assert len(rec["prompt"]) == 200 and rec["ts"]
