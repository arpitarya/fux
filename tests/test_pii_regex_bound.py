"""W-255 -- a pathological PII regex is refused at load; its timing is `doctor`'s.

The linter is a predicate on the pattern string (L4: same answer on every
machine). The wall-clock lives in `doctor`'s `pii timing` row and nowhere on the
ingest path, which `test_no_clock_on_the_ingest_path` holds in the shape of the
L5 import fence.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from fux import doctor
from fux.errors import FuxError
from fux.ingest import pii
from l12_fixtures import write_config

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src" / "fux"

CANONICAL = {
    "nested-plus": r"(a+)+$",
    "overlapping-alternation": r"(a|aa)*$",
    "optional-in-star": r"(\w*\s?)*$",
    "backreference-in-repeat": r"(a)(\1)*$",
}

SAFE = [
    r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
    r"(?:[0-9]{1,3}\.){2}[0-9]{1,3}",
    r"(a|b)*c",
    r"(?:\d|[a-f])+",
    r"(a++)+",
    r"(?>a+)+",
    r"(a+)",
]


def _rules(tmp_path: Path, pattern: str, name: str = "r") -> Path:
    path = tmp_path / ".fux" / "pii.toml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"[[rule]]\nname = '{name}'\npattern = '''{pattern}'''\n", encoding="utf-8"
    )
    return path


@pytest.mark.parametrize("shape", sorted(CANONICAL))
def test_the_canonical_redos_shapes_are_refused_at_load(tmp_path, shape):
    _rules(tmp_path, CANONICAL[shape], name="evil")
    with pytest.raises(FuxError) as exc:
        pii.load(tmp_path)
    text = str(exc.value)
    assert "'evil'" in text
    assert "possessive" in text and "atomic" in text
    assert "conservative" in text


@pytest.mark.parametrize("pattern", SAFE)
def test_safe_shapes_pass(pattern):
    assert pii._lint(pattern, 0) is None


def test_the_possessive_fix_the_error_names_is_admitted():
    assert pii._lint(r"(a+)+", 0) is not None
    assert pii._lint(r"(a++)+", 0) is None


def test_the_starter_template_loads_clean(tmp_path):
    path = tmp_path / ".fux" / "pii.toml"
    path.parent.mkdir(parents=True)
    path.write_text(
        (SRC / "templates" / "pii.toml.txt").read_text(encoding="utf-8"), encoding="utf-8"
    )
    assert pii.load(tmp_path)


def test_this_repository_pii_toml_loads_clean():
    assert pii.load(ROOT)


def test_every_commented_starter_pattern_passes_the_linter():
    """The opt-in rules a consumer uncomments must not be refused either."""
    import re

    text = (SRC / "templates" / "pii.toml.txt").read_text(encoding="utf-8")
    patterns = re.findall(r"^#? ?pattern\s*=\s*'''(.*)'''\s*$", text, flags=re.M)
    assert len(patterns) > 10
    for pattern in patterns:
        assert pii._lint(pattern, 0) is None, pattern


def test_a_planted_quadratic_rule_warns_in_doctor(tmp_path):
    write_config(tmp_path)
    # Quadratic, not exponential, so the linter admits it: the run has no `!`.
    _rules(tmp_path, r"[a-z]+!", name="quad")
    (tmp_path / "fux.toml").write_text(
        (tmp_path / "fux.toml").read_text(encoding="utf-8").replace(
            "pii_rule_budget_ms     = 100.0", "pii_rule_budget_ms     = 0.001"
        ),
        encoding="utf-8",
    )
    check = doctor._pii_timing(tmp_path)
    assert check.level == "warn" and check.ok
    assert "quad" in check.detail and "pii_rule_budget_ms" in check.detail


def test_a_generous_budget_does_not_warn(tmp_path):
    write_config(tmp_path)
    _rules(tmp_path, r"[a-z]+!", name="quad")
    (tmp_path / "fux.toml").write_text(
        (tmp_path / "fux.toml").read_text(encoding="utf-8").replace(
            "pii_rule_budget_ms     = 100.0", "pii_rule_budget_ms     = 1000000.0"
        ),
        encoding="utf-8",
    )
    check = doctor._pii_timing(tmp_path)
    assert check.level != "warn"
    assert "quad" in check.detail


_CLOCKS = {"time", "datetime", "perf_counter", "monotonic", "time_ns", "process_time"}


@pytest.mark.parametrize("module", ["pii.py", "run.py"])
def test_no_clock_on_the_ingest_path(module):
    """Redaction writes committed bytes; a clock there would make them CPU-dependent."""
    tree = ast.parse((SRC / "ingest" / module).read_text(encoding="utf-8"))
    found: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found += [a.name for a in node.names if a.name.split(".")[0] in _CLOCKS]
        elif isinstance(node, ast.ImportFrom):
            if (node.module or "").split(".")[0] in _CLOCKS:
                found.append(node.module)
        elif isinstance(node, ast.Attribute) and node.attr in _CLOCKS:
            found.append(node.attr)
    assert not found, f"ingest/{module} reads a clock: {found}"


def test_overlap_above_the_compared_alphabet_still_counts():
    """Two negated classes share every code point above `[pii] lint_alphabet`,
    so alternating them under a repeat is refused even though no character
    below the limit is common to both (review of W-255)."""
    from fux.ingest.pii import _lint

    assert _lint(r"(?:[^\x00-\x7f]|[^\x80-˿])*", 0) is not None
    assert _lint("(?:一|丁x)*", 0) is not None
    assert _lint(r"(?:a|b)*", 0) is None


def test_the_lint_runs_once_per_rule_not_once_per_apply(monkeypatch):
    """W-264 DoD 1: the 6 s redact phase was `_lint` re-parsing every pattern on
    every `apply` (260 180 calls at rung-10000). Redacting many strings must
    lint each rule once, however many strings it is applied to."""
    calls = []
    real = pii._lint
    monkeypatch.setattr(pii, "_lint", lambda pattern, flags: calls.append(pattern) or real(pattern, flags))
    pii._compile.cache_clear()
    rules = pii.parse(
        {"rule": [
            {"name": "email", "pattern": SAFE[0], "replacement": "[PII:email]"},
            {"name": "card", "pattern": r"\b[0-9]{16}\b", "replacement": "[PII:card]", "validate": "luhn"},
        ]},
        origin="test",
    )
    for n in range(200):
        pii.redact(rules, f"doc {n}: mail a{n}@example.com card 4242424242424242")
    assert sorted(calls) == sorted({r.pattern for r in rules})
