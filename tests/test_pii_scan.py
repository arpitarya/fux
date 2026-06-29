"""PII content probe — dante's BLOCK regexes, ported stdlib, wired into the gate
(constitution-enforcement / remaining-backlog item 5).

NOTE: the literal example identifiers below carry an inline `pii-allow` marker so the
`fux pii-scan` gate step does not flag this test file itself — which also exercises the
marker. Everything else references these constants, never a bare literal.
"""
from __future__ import annotations

from types import SimpleNamespace

from fux import clicmds, piiscan

PAN = "ABCDE1234F"            # pii-allow — vetted example PAN
AADHAAR = "1234 5678 9012"    # pii-allow — vetted example Aadhaar
ACCT = "account: 1234567"     # pii-allow — vetted example account id


def test_detects_each_hard_identifier():
    assert [k for _, k, _ in piiscan.scan_text(f"my pan {PAN}")] == ["pan"]
    assert [k for _, k, _ in piiscan.scan_text(f"id {AADHAAR}")] == ["aadhaar"]
    assert [k for _, k, _ in piiscan.scan_text(ACCT)] == ["account-id"]


def test_clean_text_has_no_hits():
    assert piiscan.scan_text("nothing sensitive here, just 42 and a date 2026-06-29") == []


def test_inline_allow_marker_skips_a_line():
    assert piiscan.scan_text(f"my pan {PAN} here  # {piiscan.ALLOW}") == []


def test_plan_and_decision_docs_are_exempt():
    assert piiscan.is_exempt("docs/handoff/batch-ingest-handoff.md")
    assert piiscan.is_exempt("docs/decisions/0001-fux-elgar-relationship.md")
    assert piiscan.is_exempt("docs/fux-plan.md")
    assert not piiscan.is_exempt("fux/check.py")
    assert not piiscan.is_exempt("README.md")


def test_scan_file_and_cli_exit_code(tmp_path, capsys):
    leak = tmp_path / "note.md"
    leak.write_text(f"contact {AADHAAR}\n", encoding="utf-8")
    clean = tmp_path / "ok.md"
    clean.write_text("all good here\n", encoding="utf-8")
    assert piiscan.scan_file(leak) and not piiscan.scan_file(clean)

    rc = clicmds.cmd_pii_scan(SimpleNamespace(paths=[str(leak)]))
    assert rc == 2 and "aadhaar" in capsys.readouterr().out
    assert clicmds.cmd_pii_scan(SimpleNamespace(paths=[str(clean)])) == 0


def test_exempt_file_is_skipped_even_with_a_hit(tmp_path):
    plan = tmp_path / "feature-plan.md"
    plan.write_text(f"example PAN {PAN}\n", encoding="utf-8")
    assert piiscan.scan_file(plan) == []        # exempt by the `-plan`/`plan.md` path rule
