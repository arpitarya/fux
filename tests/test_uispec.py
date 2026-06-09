"""`fux validate-spec` — the mount-time guardrail for generated UISpecs ($0, §18.3.3)."""
from __future__ import annotations

from fux import uispec

_REG = {
    "components": [
        {"name": "Card", "props": [{"name": "children", "optional": False, "type": "any"},
                                   {"name": "variant", "optional": True, "type": "string"}]},
        {"name": "CountUp", "props": [{"name": "value", "optional": False, "type": "number"},
                                      {"name": "suffix", "optional": True, "type": "string"}]},
    ],
    "hooks": [{"name": "useHoldings", "file": "x.ts"}],
    "dtos": [],
}


def test_valid_spec_passes():
    spec = {"component": "Card", "props": {"variant": "glow"}, "children": [
        {"component": "CountUp", "props": {"value": 42}, "data": "useHoldings"},
        {"text": "Net worth"},
    ]}
    assert uispec.validate(_REG, spec) == []


def test_unknown_component_is_rejected():
    errs = uispec.validate(_REG, {"component": "EvilWidget"})
    assert any("unknown component 'EvilWidget'" in e for e in errs)


def test_undeclared_prop_is_rejected():
    errs = uispec.validate(_REG, {"component": "CountUp",
                                  "props": {"value": 1, "onClick": "alert"}})
    assert any("prop 'onClick' not on CountUp" in e for e in errs)


def test_missing_required_prop_is_reported():
    errs = uispec.validate(_REG, {"component": "CountUp", "props": {"suffix": "%"}})
    assert any("missing required prop 'value'" in e for e in errs)


def test_unknown_data_hook_is_rejected():
    errs = uispec.validate(_REG, {"component": "Card", "props": {"children": []},
                                  "data": "useSecretBackdoor"})
    assert any("data hook 'useSecretBackdoor'" in e for e in errs)


def test_children_on_childless_component_is_rejected():
    errs = uispec.validate(_REG, {"component": "CountUp", "props": {"value": 1},
                                  "children": [{"text": "x"}]})
    assert any("takes no children" in e for e in errs)
