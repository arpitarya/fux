"""PR3 — batch + linked-document ingestion (docs/batch-ingest-handoff.md).

Covers the engine-side, deterministic, $0 surface of `/fux ingest`'s batch mode:
the draft review queue (ingestqueue), bounded depth-1 link discovery
(ingestfollow), reduce-before-draft (ingestreduce), and the guard that none of
these three new modules import a network/LLM/PDF/Excel/Word/OCR/vision library.
The fetching/extracting/drafting itself stays the host agent's job (the skill).
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import pytest

from fux import ingestfollow, ingestqueue, ingestreduce
from fux.ingestqueue import Item


# ── batch: source-list expansion + dedup ─────────────────────────────────────

def test_expand_sources_expands_globs_sorted_and_dedups(tmp_path):
    for n in ("b.pdf", "a.pdf", "c.txt"):
        (tmp_path / n).write_text("x", encoding="utf-8")
    out = ingestqueue.expand_sources(["*.pdf", "*.pdf", "c.txt"], tmp_path)
    # globs expand deterministically (sorted), dedup preserves first-seen order
    assert [Path(p).name for p in out] == ["a.pdf", "b.pdf", "c.txt"]


def test_expand_sources_passes_urls_through_untouched(tmp_path):
    out = ingestqueue.expand_sources(
        ["https://x/a", "https://x/a", "https://y/b"], tmp_path)
    assert out == ["https://x/a", "https://y/b"]


@pytest.mark.parametrize("source,expected", [
    ("https://x/api", "url"),
    ("doc.pdf", "pdf"), ("sheet.xlsx", "xlsx"), ("data.csv", "xlsx"),
    ("memo.docx", "docx"), ("notes.txt", "txt"), ("scan.png", "image"),
    ("config.json", "json"), ("conf.yaml", "yaml"), ("conf.yml", "yaml"),
    ("https://x/openapi.json", "openapi"), ("https://x/swagger.yaml", "openapi"),
])
def test_classify_type_covers_the_new_enum(source, expected):
    assert ingestqueue.classify_type(source) == expected


# ── batch: the draft review queue ────────────────────────────────────────────

def test_queue_records_mixed_draft_and_failed_status(project):
    items = [
        Item(source="a.pdf", source_type="pdf", status="draft",
             draft_id="rule-a", source_hash="h1"),
        Item(source="https://x/404", source_type="url", status="failed",
             reason="404 Not Found"),
    ]
    ingestqueue.upsert(project, items)
    rows = ingestqueue.read(project)
    by_src = {r.source: r for r in rows}
    assert by_src["a.pdf"].status == "draft" and by_src["a.pdf"].draft_id == "rule-a"
    assert by_src["https://x/404"].status == "failed"
    assert by_src["https://x/404"].reason == "404 Not Found"


def test_queue_partial_failure_does_not_drop_the_good_rows(project):
    """A failing source coexists with successful drafts in one queue (§2)."""
    ingestqueue.upsert(project, [Item(source="ok.pdf", status="draft", source_hash="h1"),
                                 Item(source="bad", status="failed", reason="boom")])
    statuses = {r.status for r in ingestqueue.read(project)}
    assert statuses == {"draft", "failed"}
    assert len(ingestqueue.read(project)) == 2


def test_queue_dedups_by_source_hash(project):
    """Re-ingesting an identical doc (same source_hash) updates, never duplicates."""
    ingestqueue.upsert(project, [Item(source="v1.pdf", status="draft",
                                      draft_id="r", source_hash="same")])
    ingestqueue.upsert(project, [Item(source="v2-copy.pdf", status="draft",
                                      draft_id="r2", source_hash="same")])
    rows = ingestqueue.read(project)
    assert len(rows) == 1
    assert rows[0].source == "v2-copy.pdf" and rows[0].draft_id == "r2"


def test_queue_never_contains_an_active_row(project):
    """The queue's only statuses are draft|failed — nothing auto-activates (§2)."""
    ingestqueue.upsert(project, [Item(source="a", status="draft", source_hash="h"),
                                 Item(source="b", status="failed", reason="x")])
    assert all(r.status in ("draft", "failed") for r in ingestqueue.read(project))


def test_queue_round_trips_trust_flags(project):
    ingestqueue.upsert(project, [Item(source="scan.png", source_type="image",
                                      status="draft", trust="verify-source",
                                      draft_id="money", source_hash="h")])
    r = ingestqueue.read(project)[0]
    assert r.trust == "verify-source" and r.source_type == "image"
    assert "verify-source" in ingestqueue.render(project)


def test_queue_render_is_empty_message_when_no_queue(project):
    assert "empty" in ingestqueue.render(project).lower()


# ── --follow-links: bounded depth-1 discovery ────────────────────────────────

PAGE = """<html><body>
  <a href="/docs/a.pdf">A</a>
  <a href="https://same.test/docs/b.xlsx">B</a>
  <a href="report.docx">rel</a>
  <a href="https://other.test/c.pdf">offsite</a>
  <a href="/scripts/evil.exe">exe</a>
  <a href="/archive.zip">zip</a>
  <a href="/page2.html">another page</a>
  <a href="/docs/a.pdf">dup</a>
</body></html>"""
BASE = "https://same.test/index.html"


def test_follow_links_same_origin_allowlist_and_dedup():
    got = ingestfollow.discover(PAGE, BASE)
    # allow-listed docs only, same-origin only, deduped, depth-1 (no .html page)
    assert got == ["https://same.test/docs/a.pdf",
                   "https://same.test/docs/b.xlsx",
                   "https://same.test/report.docx"]
    assert not any(u.endswith((".exe", ".zip", ".html")) for u in got)
    assert not any("other.test" in u for u in got)


def test_follow_links_cross_origin_widens():
    got = ingestfollow.discover(PAGE, BASE, cross_origin=True)
    assert "https://other.test/c.pdf" in got


def test_follow_links_cap_refuses_with_message_not_silent_truncate():
    many = "".join(f'<a href="/d{i}.pdf">x</a>' for i in range(25))
    with pytest.raises(ingestfollow.FollowError) as exc:
        ingestfollow.discover(many, BASE, max_n=20)
    assert "over the --max 20 cap" in str(exc.value)


def test_follow_links_is_depth_1_only_never_recurses():
    """`discover` only ever reads the one page it is given — page links (.html)
    are never returned, so it cannot descend."""
    assert ingestfollow.discover(PAGE, BASE) and \
        not any(u.endswith(".html") for u in ingestfollow.discover(PAGE, BASE))


def test_direct_file_url_skips_discovery():
    assert ingestfollow.is_direct_file("https://x/circular.pdf")
    assert ingestfollow.is_direct_file("https://x/openapi.json")
    assert ingestfollow.is_direct_file("https://x/api/openapi")     # spec hint
    assert not ingestfollow.is_direct_file("https://x/some/page")


# ── reduce-before-draft ──────────────────────────────────────────────────────

def test_reduce_cuts_tokens_and_reports_before_after():
    body = ("# Heading\n\n"
            + "\n\n".join(f"Filler paragraph number {i} with nothing of note." for i in range(40))
            + "\n\nThe rate limit must not exceed 100 requests per minute.")
    out, stats = ingestreduce.reduce(body, "pdf")
    assert stats["after_tokens"] < stats["before_tokens"]
    assert stats["saved_tokens"] > 0
    assert "must not exceed 100" in out          # the rule-bearing passage is kept
    assert "Filler paragraph number 20" not in out


def test_reduce_full_bypasses_reduction():
    body = "irrelevant chatter " * 50
    out, stats = ingestreduce.reduce(body, "pdf", full=True)
    assert out == body
    assert stats["before_tokens"] == stats["after_tokens"]


def test_reduce_excel_never_sends_the_full_grid():
    rows = ["id,name,amount"] + [f"{i},item{i},{i*10}" for i in range(200)]
    rows.append("total,=SUM(C2:C201),required")
    out, stats = ingestreduce.reduce("\n".join(rows), "xlsx")
    assert "id,name,amount" in out               # schema/header kept
    assert "=SUM" in out                         # formula kept
    assert "100,item100,1000" not in out         # a bulk data row dropped
    assert stats["after_tokens"] < stats["before_tokens"]


def test_reduce_contract_keeps_keys_drops_long_example_values():
    spec = ('{\n  "required": ["id"],\n'
            '  "paths": {\n    "/users": {}\n  },\n'
            '  "example": "' + "x" * 500 + '"\n}')
    out, _ = ingestreduce.reduce(spec, "openapi")
    assert "required" in out and "paths" in out
    assert "x" * 500 not in out                  # long example value trimmed


def test_reduce_incremental_drafts_only_changed_sections():
    old = "# A\n\nalpha must hold.\n\n# B\n\nbeta must hold."
    new = "# A\n\nalpha must hold.\n\n# B\n\nbeta must hold NOW differently."
    delta = ingestreduce.changed_sections(old, new)
    assert "NOW differently" in delta
    assert "alpha must hold" not in delta        # unchanged section excluded


# ── trust: nothing auto-ratifies; regulatory/image flagged ───────────────────

def test_regulatory_and_image_money_drafts_are_flagged_in_the_queue(project):
    ingestqueue.upsert(project, [
        Item(source="https://tax.gov/vat", source_type="url", status="draft",
             trust="draft-verify", draft_id="vat", source_hash="h1"),
        Item(source="invoice.png", source_type="image", status="draft",
             trust="verify-source", draft_id="amt", source_hash="h2"),
    ])
    flags = {r.draft_id: r.trust for r in ingestqueue.read(project)}
    assert flags["vat"] == "draft-verify"
    assert flags["amt"] == "verify-source"
    # still drafts — never auto-active/ratified
    assert all(r.status == "draft" for r in ingestqueue.read(project))


# ── Swagger/OpenAPI contract-drift via --recheck (generic source_hash) ───────

def test_recheck_flags_openapi_contract_drift_when_spec_changes(project, tmp_path):
    """A Swagger/OpenAPI draft re-checks like any source: when the spec file
    changes, `fux ingest --recheck` raises source-drift (handoff §0 standout)."""
    from fux import ingest
    spec = tmp_path / "openapi.json"
    spec.write_text('{"paths": {"/users": {"get": {}}}}', encoding="utf-8")
    h = ingest.source_hash(spec.read_text(encoding="utf-8"))
    (project / ".fux" / "rules").mkdir(parents=True, exist_ok=True)
    (project / ".fux" / "rules" / "users-get.md").write_text(
        f"---\nid: users-get\ntype: convention\nstatus: draft\n"
        f'source: "{spec}"\nsource_type: "openapi"\nfetched: "2026-06-23"\n'
        f'source_hash: "{h}"\n---\n\n**Rule:** GET /users exists.\n', encoding="utf-8")
    spec.write_text('{"paths": {}}', encoding="utf-8")     # endpoint dropped
    findings = ingest.recheck(project)
    assert any(f.kind == "source-drift" and f.rule_id == "users-get" for f in findings)


# ── guard: the three new modules import no parser/network/LLM library ─────────

FUX_DIR = Path(__import__("fux").__file__).resolve().parent
_NEW = ["ingestqueue.py", "ingestfollow.py", "ingestreduce.py"]
# `urllib.parse` (URL-string manipulation, no socket) is allowed; `urllib.request` is not.
_BANNED = re.compile(
    r"\b(?:import|from)\s+(anthropic|openai|cohere|litellm|mistralai|"
    r"urllib\.request|urllib\.error|http\.client|socket|requests|httpx|aiohttp|"
    r"pypdf|PyPDF2|pdfplumber|fitz|openpyxl|xlrd|pandas|pytesseract|PIL|cv2|easyocr)\b")


@pytest.mark.parametrize("name", _NEW)
def test_new_ingest_modules_import_no_parser_network_or_llm_library(name):
    hit = _BANNED.search((FUX_DIR / name).read_text(encoding="utf-8"))
    assert hit is None, f"fux/{name} imports a forbidden library: {hit and hit.group(0)!r}"


def test_new_ingest_modules_are_offline_and_model_free_on_import():
    code = ("import importlib, sys\n"
            "for m in ['fux.ingestqueue','fux.ingestfollow','fux.ingestreduce']:\n"
            "    importlib.import_module(m)\n"
            "bad = [m for m in ('anthropic','openai','requests','httpx','pypdf','openpyxl','PIL')\n"
            "       if m in sys.modules]\n"
            "assert not bad, bad\n"
            "print('clean')\n")
    out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    assert out.returncode == 0, out.stderr
    assert "clean" in out.stdout
