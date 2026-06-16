"""Guard: Fux's maintenance/enforcement path imports no LLM client, and the default
install (no extras) is model-free — the $0 promise (handoff §9.1, plan §0)."""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import fux

FUX_DIR = Path(fux.__file__).resolve().parent

# The deterministic maintenance/enforcement path — none of these may import a model client.
MAINT = ["check", "gate", "verify", "seal", "constitution", "critic", "criticloop",
         "baseline", "findings", "hooks", "hookio", "touch", "mcpserver", "lint", "stats", "fix"]
# `criticllm.py` is the ONE sanctioned edge — the opt-in `[critic]` headless judge, never on
# the maintenance path. Every other module is scanned.
EDGE = "criticllm.py"
# LLM *API clients*. `sentence_transformers` (the [embeddings] LOCAL model extra) is allowed —
# it is not an LLM client and is never on the default import path.
FORBIDDEN = re.compile(
    r"\b(?:import|from)\s+(anthropic|openai|cohere|litellm|google\.generativeai|mistralai)\b")


def test_maintenance_path_imports_no_llm_client():
    for name in MAINT:
        src = (FUX_DIR / f"{name}.py").read_text(encoding="utf-8")
        hit = FORBIDDEN.search(src)
        assert hit is None, f"fux/{name}.py imports an LLM client: {hit.group(0)!r}"


def test_only_the_opt_in_edge_may_reference_a_model_client():
    """Across the whole package, only `criticllm.py` (the `[critic]` edge) may name a model
    client — proving there is no stray model import on any default path."""
    for py in sorted(FUX_DIR.glob("*.py")):
        if py.name == EDGE:
            continue
        hit = FORBIDDEN.search(py.read_text(encoding="utf-8"))
        assert hit is None, f"fux/{py.name} imports an LLM client: {hit.group(0)!r}"


def test_default_install_is_model_free():
    """A fresh interpreter importing fux + the enforcement path + even the critic edge pulls in
    no LLM client (the edge imports its model lazily). Run in a subprocess so it is independent
    of whatever other tests imported."""
    code = (
        "import importlib, sys\n"
        "for m in ['fux','fux.check','fux.gate','fux.constitution','fux.seal','fux.hooks',\n"
        "          'fux.critic','fux.criticloop','fux.criticllm']:\n"
        "    importlib.import_module(m)\n"
        "bad = [m for m in ('anthropic','openai','cohere','litellm','mistralai') if m in sys.modules]\n"
        "assert not bad, bad\n"
        "print('model-free')\n"
    )
    out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    assert out.returncode == 0, out.stderr
    assert "model-free" in out.stdout
