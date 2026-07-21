"""Extended example execution: inline key=value bindings + scalar coercion (§10.1)."""
from __future__ import annotations

from pathlib import Path

from fux import vexamples
from fux.model import Rule

_SAFE = {"abs": abs, "round": round}


def _rule(check, examples):
    return Rule(id="r", type="formula",
                fm={"id": "r", "check": check, "examples": examples},
                body="", path=Path("r.md"), layer="project")


def test_inline_pair_given_executes():
    r = _rule("qty * pct / 100 == 2", [{"given": "qty=100, pct=2"}])
    res = vexamples.run_examples(r, _SAFE)
    assert res and res[0][1] == "pass"


def test_expect_scalar_coercion_with_currency():
    r = _rule("qty * pct / 100", [{"given": "qty=100000, pct=2", "expect": "2,000"}])
    res = vexamples.run_examples(r, _SAFE)
    assert res[0][1] == "pass"  # 100000*2/100 == 2000, "2,000" coerces to 2000


def test_boolean_binding_and_truthy_expect():
    r = _rule("enabled and count > 0", [{"given": "enabled=true, count=3"}])
    res = vexamples.run_examples(r, _SAFE)
    assert res[0][1] == "pass"


def test_unparseable_prose_is_skipped_not_failed():
    r = _rule("x > 0", [{"given": "a cheerful note about the weather", "expect": "sunny"}])
    res = vexamples.run_examples(r, _SAFE)
    assert res == []  # skipped — never a false fail


def test_json_object_given_still_works():
    r = _rule("sum(v for v in xs) == total",
              [{"given": '{"xs": [1, 2], "total": 3}'}])
    res = vexamples.run_examples(r, {"sum": sum})
    assert res[0][1] == "pass"


def test_list_value_in_pair_binding_survives_comma_split():
    r = _rule("sum(xs) == total", [{"given": "xs=[1, 2, 3], total=6"}])
    res = vexamples.run_examples(r, {"sum": sum})
    assert res[0][1] == "pass"
