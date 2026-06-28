"""Guard: Fux's maintenance/enforcement path imports no LLM client AND no network
client AND no PDF/Excel/OCR/vision library, and the default install (no extras) is
model-free + offline — the $0 promise (handoff §0/§9.1, plan §0; ingest-files §1)."""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import fux

FUX_DIR = Path(fux.__file__).resolve().parent

# The deterministic maintenance/enforcement path — none of these may import a model
# client or open the network. `howto` (the `fux how` command) is on this fence too:
# it must be pure recall over the in-repo registry, never a fetch or a model call.
MAINT = ["check", "gate", "verify", "seal", "constitution", "critic", "criticloop",
         "baseline", "findings", "hooks", "hookio", "touch", "mcpserver", "lint",
         "stats", "fix", "recall", "howto", "registry", "clihelp", "cdp_utils",
         "selfbuild"]
# `criticllm.py` is the ONE sanctioned edge — the opt-in `[critic]` headless judge, never on
# the maintenance path. Every other module is scanned.
EDGE = "criticllm.py"
# The two sanctioned network/file-reading modules — both lazily imported, never reachable
# from the maintenance path: `fetchrules` (the $0 fetch-rules extractor; also the engine-side
# optional `pypdf` PDF path) and `ingest` (the opt-in `--recheck`, which imports `fetchrules`
# lazily and only behind the `[scrape]` extra).
NET_EDGE = {"fetchrules.py", "ingest.py"}
# LLM *API clients*. `sentence_transformers` (the [embeddings] LOCAL model extra) is allowed —
# it is not an LLM client and is never on the default import path.
FORBIDDEN = re.compile(
    r"\b(?:import|from)\s+(anthropic|openai|cohere|litellm|google\.generativeai|mistralai)\b")
# Network clients. urllib.request/http.client/socket/requests/httpx must not be reachable
# from the maintenance path; cdp_utils computes an endpoint *string* but opens no socket.
# `urllib.parse` (pure URL-string manipulation, no socket) is NOT a network client — the
# bounded link-discovery helper (ingestfollow) uses it to apply the same-origin fence.
NETWORK = re.compile(
    r"\b(?:import|from)\s+(urllib\.request|urllib\.error|http\.client|socket|"
    r"requests|httpx|aiohttp)\b")
# PDF/Excel/OCR/vision libraries (ingest-files §1/§6): extraction for these source types is
# the HOST AGENT's job (its own pdf/xlsx/vision skills), never the engine's. `pypdf` is the
# one sanctioned exception, confined to the `fetchrules.py` edge above for the unrelated,
# already-shipped `fux fetch-rules --raw` PDF path.
DOC_LIB = re.compile(
    r"\b(?:import|from)\s+(pypdf|PyPDF2|pdfplumber|fitz|openpyxl|xlrd|pandas|"
    r"pytesseract|PIL|Pillow|cv2|easyocr)\b")


def test_maintenance_path_imports_no_llm_client():
    for name in MAINT:
        src = (FUX_DIR / f"{name}.py").read_text(encoding="utf-8")
        hit = FORBIDDEN.search(src)
        assert hit is None, f"fux/{name}.py imports an LLM client: {hit.group(0)!r}"


def test_maintenance_path_imports_no_network_client():
    """check/gate/verify/seal/recall/howto (+ help/registry/cdp_utils) never fetch."""
    for name in MAINT:
        src = (FUX_DIR / f"{name}.py").read_text(encoding="utf-8")
        hit = NETWORK.search(src)
        assert hit is None, f"fux/{name}.py imports a network client: {hit.group(0)!r}"


def test_only_the_two_edges_may_touch_the_network():
    """Across the package, only `fetchrules`/`scrape` (both lazily imported, opt-in)
    may name a network client — proving no stray fetch on any default path."""
    for py in sorted(FUX_DIR.glob("*.py")):
        if py.name in NET_EDGE:
            continue
        hit = NETWORK.search(py.read_text(encoding="utf-8"))
        assert hit is None, f"fux/{py.name} imports a network client: {hit.group(0)!r}"


def test_only_the_opt_in_edge_may_reference_a_model_client():
    """Across the whole package, only `criticllm.py` (the `[critic]` edge) may name a model
    client — proving there is no stray model import on any default path."""
    for py in sorted(FUX_DIR.glob("*.py")):
        if py.name == EDGE:
            continue
        hit = FORBIDDEN.search(py.read_text(encoding="utf-8"))
        assert hit is None, f"fux/{py.name} imports an LLM client: {hit.group(0)!r}"


def test_maintenance_path_imports_no_doc_or_vision_library():
    """check/gate/verify/seal/recall/howto etc. never import a PDF/Excel/OCR/vision lib —
    extraction for those source types is the host agent's job (ingest-files §1)."""
    for name in MAINT:
        src = (FUX_DIR / f"{name}.py").read_text(encoding="utf-8")
        hit = DOC_LIB.search(src)
        assert hit is None, f"fux/{name}.py imports a doc/vision library: {hit.group(0)!r}"


def test_only_fetchrules_may_reference_a_doc_or_vision_library():
    """Across the package, only `fetchrules.py` (the lazy, optional `[pdf]` extra for the
    unrelated `fux fetch-rules` URL/PDF path) may name a PDF/Excel/OCR/vision library — proving
    `fux ingest`'s PDF/Excel/image branches stay entirely agent-side."""
    for py in sorted(FUX_DIR.glob("*.py")):
        if py.name == "fetchrules.py":
            continue
        hit = DOC_LIB.search(py.read_text(encoding="utf-8"))
        assert hit is None, f"fux/{py.name} imports a doc/vision library: {hit.group(0)!r}"


def test_default_install_is_model_free_and_offline():
    """A fresh interpreter importing fux + the enforcement path + `fux how` + even the critic
    edge pulls in no LLM client and no network client (both are imported lazily, only behind an
    opt-in). Run in a subprocess so it is independent of whatever other tests imported."""
    code = (
        "import importlib, sys\n"
        "for m in ['fux','fux.check','fux.gate','fux.constitution','fux.seal','fux.hooks',\n"
        "          'fux.recall','fux.howto','fux.registry','fux.clihelp','fux.cdp_utils',\n"
        "          'fux.selfbuild','fux.critic','fux.criticloop','fux.criticllm']:\n"
        "    importlib.import_module(m)\n"
        "bad = [m for m in ('anthropic','openai','cohere','litellm','mistralai') if m in sys.modules]\n"
        "assert not bad, ('llm', bad)\n"
        "net = [m for m in ('requests','httpx','aiohttp') if m in sys.modules]\n"
        "assert not net, ('net', net)\n"
        "print('model-free offline')\n"
    )
    out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    assert out.returncode == 0, out.stderr
    assert "model-free offline" in out.stdout
