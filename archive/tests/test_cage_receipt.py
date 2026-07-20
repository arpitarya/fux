"""Optional cage receipt — fail-open in-tool shim + hook-recall emit.

Covers handoff criteria 2 (cage-absent no-op), 3 (one correct modeled receipt),
4 (no emit on non-saving), 7 (meta shape). Dependency-free: cage is faked via a
stub module in sys.modules, and blocked entirely to prove the cage-absent path.
"""
from __future__ import annotations

import sys
import types

import pytest

from fux import cage_receipt


def _install_fake_cage(monkeypatch):
    """Inject a fake `cage` exposing a spying record_receipt; return the call log."""
    calls: list[dict] = []
    fake = types.ModuleType("cage")
    fake.record_receipt = lambda **kw: calls.append(kw) or "r_test"  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "cage", fake)
    return calls


def _block_cage(monkeypatch):
    """Make `import cage` raise, simulating a cage-less environment."""
    import builtins
    real = builtins.__import__

    def fake_import(name, *a, **k):
        if name == "cage" or name.startswith("cage."):
            raise ImportError("cage blocked for test")
        return real(name, *a, **k)
    monkeypatch.setattr(builtins, "__import__", fake_import)


# ── toks: cage's exact len/4 heuristic (criterion 6, the shared unit) ───────────
def test_toks_matches_len_over_four():
    assert cage_receipt.toks("") == 0
    assert cage_receipt.toks("abcd") == 1
    assert cage_receipt.toks("a" * 10) == 2  # round(10/4) = 2


# ── criterion 2 — cage absent: emit is a silent no-op, never raises ─────────────
def test_emit_noop_when_cage_absent(monkeypatch):
    _block_cage(monkeypatch)
    # would-be saving, but cage import fails → must return None quietly
    assert cage_receipt.emit("fux", 1000, 100, task="t", op="hook-recall") is None


# ── criterion 3 — one correct tokens/modeled receipt when cage present ──────────
def test_emit_files_one_modeled_receipt(monkeypatch):
    calls = _install_fake_cage(monkeypatch)
    cage_receipt.emit("fux", 800, 160, task="sess1", op="hook-recall")
    assert len(calls) == 1
    r = calls[0]
    assert r["tool"] == "fux" and r["unit"] == "tokens"
    assert r["raw_alternative"] == 800 and r["actual"] == 160
    assert r["method"] == "modeled" and r["confidence"] == 0.7
    assert r["task"] == "sess1"
    # saved is DERIVED by cage — the shim must not set it
    assert "saved" not in r


# ── criterion 4 — nothing filed when actual >= raw_alternative ──────────────────
def test_no_emit_on_non_saving(monkeypatch):
    calls = _install_fake_cage(monkeypatch)
    cage_receipt.emit("fux", 100, 100)   # equal → no saving
    cage_receipt.emit("fux", 100, 250)   # negative → no saving
    assert calls == []


# ── criterion 7 — meta is op + counts only, no PII/bodies ───────────────────────
def test_meta_is_op_only(monkeypatch):
    calls = _install_fake_cage(monkeypatch)
    cage_receipt.emit("fux", 500, 50, op="hook-recall")
    assert calls[0]["meta"] == {"op": "hook-recall"}


# ── the hook-recall integration point files a fux receipt from real rules ───────
def test_hook_recall_emits_from_selected_rules(tmp_path, monkeypatch):
    calls = _install_fake_cage(monkeypatch)
    from fux import hooks
    # a selected rule whose whole source file is larger than the distilled payload
    src = tmp_path / "rule.md"
    src.write_text("x" * 4000, encoding="utf-8")   # ~1000 toks whole

    class _Rule:
        path = src
    payload = "y" * 400                              # ~100 toks distilled
    hooks._emit_recall_receipt(tmp_path, {"session_id": "s9"}, [_Rule()], payload)
    assert len(calls) == 1
    r = calls[0]
    assert r["tool"] == "fux" and r["task"] == "s9" and r["meta"] == {"op": "hook-recall"}
    assert r["raw_alternative"] == 1000 and r["actual"] == 100
