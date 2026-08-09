"""Example fuzzing (§17.20a) + rule mining (§17.23) — both $0, deterministic."""
from __future__ import annotations

from fux import mine, verify
from tests.conftest import write_rule


def test_fuzz_flags_div_by_zero_guard(project):
    # check divides by a numeric input; the 0 boundary must surface as a fuzz fail.
    write_rule(project, "pct", "---\nid: pct\ntype: formula\nstatus: active\n"
               "check: \"profit / base > 0\"\n"
               "examples:\n  - given: \"profit=10, base=5\"\n    expect: \"true\"\n"
               "---\n**Rule:** ratio. **Why:** x.\n")
    clean = [v for v in verify.run(project, fuzz=False) if v.status == "fail"]
    fuzzed = [v for v in verify.run(project, fuzz=True)
              if v.status == "fail" and "zero" in v.detail]
    assert not clean                      # the supplied example passes
    assert fuzzed                         # base=0 boundary divides by zero


def test_fuzz_is_quiet_when_guarded(project):
    write_rule(project, "safe", "---\nid: safe\ntype: formula\nstatus: active\n"
               "check: \"(profit / base if base else 0) >= 0\"\n"
               "examples:\n  - given: \"profit=10, base=5\"\n    expect: \"true\"\n"
               "---\n**Rule:** guarded. **Why:** x.\n")
    assert not [v for v in verify.run(project, fuzz=True) if v.status == "fail"]


def test_mine_finds_repeated_magic_number(project):
    (project / "src").mkdir(exist_ok=True)
    (project / "src" / "a.py").write_text(
        "def f():\n    return 86400 * 7\n\ndef g():\n    return 86400 + 1\n"
        "\ndef h():\n    x = 86400\n    return x\n", encoding="utf-8")
    cands = mine.mine(project, min_sites=3)
    keys = [c.key for c in cands]
    assert "86400" in keys
    assert "1" not in keys                # trivial numbers filtered out
    top = next(c for c in cands if c.key == "86400")
    assert len(top.sites) == 3


def test_mine_render_empty(project):
    assert "nothing to mine" in mine.render(mine.mine(project, min_sites=3))
