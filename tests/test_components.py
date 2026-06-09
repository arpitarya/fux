"""`fux components` — the design-system registry + data-binding catalog ($0, §18.3)."""
from __future__ import annotations

from fux import build, components

_BUTTON = (
    "export interface ButtonProps {\n"
    "  label: string;\n"
    "  variant?: 'primary' | 'ghost';\n"
    "  onClick?: () => void;\n"
    "  // a comment line, not a prop\n"
    "  meta: { nested: string };\n"   # nested object — its inner field is depth-2, excluded
    "}\n\n"
    "export function Button(p: ButtonProps) { return null; }\n"
)
_HOOKS = (
    "export function useHoldings() { return []; }\n"
    "export function used() { return 1; }\n"          # not a hook (lowercase 4th char)
)
_DTOS = "export interface HoldingDTO { symbol: string; }\n"


def _setup(project):
    ui = project / "src" / "ui"
    ui.mkdir(parents=True)
    (ui / "Button.tsx").write_text(_BUTTON)
    (project / "src" / "holdings.query.ts").write_text(_HOOKS)
    (project / "src" / "portfolio.types.ts").write_text(_DTOS)
    build.run(project)


def test_registry_collects_components_props_hooks_dtos(project):
    _setup(project)
    reg = components.registry(project)
    button = next(c for c in reg["components"] if c["name"] == "Button")
    prop_names = {p["name"] for p in button["props"]}
    assert {"label", "variant", "onClick", "meta"} <= prop_names      # depth-1 fields
    assert "nested" not in prop_names                                 # depth-2 excluded
    assert next(p for p in button["props"] if p["name"] == "variant")["optional"]
    assert {h["name"] for h in reg["hooks"]} == {"useHoldings"}       # `used` excluded
    assert {d["name"] for d in reg["dtos"]} == {"HoldingDTO"}


def test_scope_filters_by_path_prefix(project):
    _setup(project)
    reg = components.registry(project, scope="src/ui")
    assert [c["name"] for c in reg["components"]] == ["Button"]
    assert reg["hooks"] == []                                         # outside src/ui


def test_render_json_is_valid_and_human_render_lists_props(project):
    import json
    _setup(project)
    reg = components.registry(project)
    assert json.loads(components.render_json(reg))["components"]      # round-trips
    text = components.render(reg)
    assert "Button" in text and "label" in text
