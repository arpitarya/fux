"""Tests for the web-rules / self-docs / CLI-help features (handoff A–D):

- D: grouped `--help`, `fux help <cmd>`, cli.md regenerated from the registry.
- C: `fux how` returns the right command deterministically (byte-stable).
- B: CDP endpoint resolves by the full precedence chain (default 9299).
- A: scrape drafts carry provenance + status: draft; recheck flags source-drift.
"""
from __future__ import annotations

import pathlib

import pytest

from fux import cdp_utils, clihelp, howto, registry, scrape
from fux.findings import Finding

REPO = pathlib.Path(__file__).resolve().parent.parent


# ── D · command registry + help ─────────────────────────────────────────────

def test_registry_is_single_source_and_complete():
    # Every registered command names a real group; names are unique.
    names = [c.name for c in registry.COMMANDS]
    assert len(names) == len(set(names)), "duplicate command in registry"
    for c in registry.COMMANDS:
        assert c.group in registry.GROUPS
        assert c.desc and c.example.startswith("fux ")


def test_registry_matches_the_cli_dispatch_surface():
    """Every non-internal subcommand has a registry entry, and vice versa."""
    from fux import cli
    sub = cli.build_parser()._subparsers._group_actions[0].choices  # type: ignore[attr-defined]
    dispatch = {n for n in sub if not n.startswith("hook-") and n != "help"}
    reg = {c.name for c in registry.COMMANDS}
    assert dispatch == reg, f"drift: dispatch-only={dispatch - reg}, registry-only={reg - dispatch}"


def test_grouped_help_groups_by_group_not_a_flat_dump():
    out = clihelp.grouped_help()
    for title in ("Authoring", "Verification", "Governance", "Runtime"):
        assert title in out
    # descriptions are aligned (two-space gutter after the widest name)
    assert "  scaffold .fux/" in out


def test_command_help_shows_example_and_related():
    out = clihelp.command_help("refs")
    assert "fux refs src/tax.py" in out          # the copy-paste example
    assert "reverse lookup" in out               # the description
    assert "related:" in out and "impact" in out
    assert "unknown command" in clihelp.command_help("nope")


def test_cli_md_is_generated_from_the_registry_no_drift():
    md = (REPO / "docs" / "cli.md").read_text(encoding="utf-8")
    block = clihelp.render_cli_md_block()
    assert block in md, "docs/cli.md is stale — regenerate it from the registry"


# ── C · `fux how` deterministic answers ─────────────────────────────────────

# A fixed question set → the exact command we expect (byte-stable, $0).
HOW_CASES = [
    ("which rules govern a file", "refs"),
    ("find rules that govern this path", "refs"),
    ("how does drift detection work", "check"),
    ("scrape a website into rules", "scrape"),
    ("draft rules from a web page", "scrape"),
    ("what does fux cost / save money", "savings"),
    ("ratify a constitutional rule", "ratify"),
    ("retrieve relevant rules for a question", "recall"),
]


@pytest.mark.parametrize("question,expected", HOW_CASES)
def test_how_returns_the_right_command(question, expected):
    result = howto.answer(question, top=3)
    assert result["hits"], f"no hit for {question!r}"
    assert result["hits"][0]["command"] == expected, result["hits"]


def test_how_is_byte_stable_across_runs():
    q = "which rules govern a file"
    assert howto.render(howto.answer(q)) == howto.render(howto.answer(q))


def test_how_renders_command_and_explanation():
    out = howto.render(howto.answer("which rules govern a file"))
    assert "fux refs" in out and "reverse lookup" in out


def test_how_explain_is_a_fenced_host_agent_prompt_not_an_engine_call():
    prompt = howto.explain_prompt(howto.answer("scrape a website into rules"))
    assert prompt.startswith("```explain")
    assert "host agent" in prompt and "not the $0 engine path" in prompt


# ── B · CDP endpoint precedence ─────────────────────────────────────────────

def test_cdp_default_is_9299(monkeypatch):
    monkeypatch.delenv("FUX_CDP_HOST", raising=False)
    monkeypatch.delenv("FUX_CDP_PORT", raising=False)
    assert cdp_utils.resolve() == ("127.0.0.1", 9299)
    assert cdp_utils.endpoint() == "http://127.0.0.1:9299"


def test_cdp_config_over_default(monkeypatch):
    monkeypatch.delenv("FUX_CDP_HOST", raising=False)
    monkeypatch.delenv("FUX_CDP_PORT", raising=False)
    assert cdp_utils.resolve({"cdp_host": "10.0.0.1", "cdp_port": 1234}) == ("10.0.0.1", 1234)


def test_cdp_env_over_config(monkeypatch):
    monkeypatch.setenv("FUX_CDP_HOST", "envhost")
    monkeypatch.setenv("FUX_CDP_PORT", "8000")
    assert cdp_utils.resolve({"cdp_host": "cfg", "cdp_port": 1234}) == ("envhost", 8000)


def test_cdp_flag_over_env_and_config(monkeypatch):
    monkeypatch.setenv("FUX_CDP_HOST", "envhost")
    monkeypatch.setenv("FUX_CDP_PORT", "8000")
    assert cdp_utils.resolve({"cdp_port": 1234}, host_flag="flaghost",
                             port_flag=9999) == ("flaghost", 9999)


def test_cdp_in_config_defaults_and_template():
    from fux import config
    assert config.DEFAULTS["cdp_port"] == 9299
    assert config.DEFAULTS["cdp_host"] == "127.0.0.1"
    assert "cdp_port = 9299" in config.default_toml()


# ── A · scrape provenance + recheck ─────────────────────────────────────────

def _draft(root, rid, source, hsh, *, regulatory=False):
    rtype = "regulatory" if regulatory else "convention"
    extra = "**Why:** scraped draft — verify against the primary source.\n" if regulatory else ""
    (root / ".fux" / "rules").mkdir(parents=True, exist_ok=True)
    (root / ".fux" / "rules" / f"{rid}.md").write_text(
        f"---\nid: {rid}\ntype: {rtype}\nstatus: draft\n"
        f'source: "{source}"\nfetched: "2026-06-23"\nsource_hash: "{hsh}"\n---\n\n'
        f"**Rule:** something.\n{extra}", encoding="utf-8")


def test_schema_accepts_provenance_fields_additively(project):
    from fux import schema
    fm = {"id": "api-x", "type": "convention", "status": "draft",
          "source": "https://x", "fetched": "2026-06-23", "source_hash": "abc123"}
    assert schema.validate(fm) == []
    # existing rules with no provenance still validate
    assert schema.validate({"id": "y", "type": "rule", "status": "active"}) == []


def test_scrape_drafts_are_draft_with_provenance(project):
    text = "Rate limit: 100 requests per minute."
    h = scrape.source_hash(text)
    _draft(project, "api-rate", "https://docs.example.com/api", h)
    from fux import loader, config, paths
    rules = {r.id: r for r in loader.resolve(project, config.load(paths.Footprint(project).config)).rules}
    r = rules["api-rate"]
    assert r.status == "draft"                       # never auto-active
    assert r.fm["source"] and r.fm["fetched"] and r.fm["source_hash"]


def test_regulatory_draft_is_flagged_verify_against_source(project):
    _draft(project, "vat-rate", "https://tax.gov/vat", "deadbeef", regulatory=True)
    body = (project / ".fux" / "rules" / "vat-rate.md").read_text(encoding="utf-8")
    assert "type: regulatory" in body
    assert "verify against the primary source" in body


def test_recheck_flags_source_drift_when_hash_changed(project, monkeypatch):
    from fux import fetchrules
    _draft(project, "api-rate", "https://docs.example.com/api", "stale000")
    monkeypatch.setattr(fetchrules, "fetch_text",
                        lambda url: "the page changed materially since first scraped")
    findings = scrape.recheck(project)
    assert any(f.kind == "source-drift" and f.rule_id == "api-rate" for f in findings)


def test_recheck_silent_when_source_unchanged(project, monkeypatch):
    from fux import fetchrules
    text = "stable content"
    _draft(project, "api-rate", "https://docs.example.com/api", scrape.source_hash(text))
    monkeypatch.setattr(fetchrules, "fetch_text", lambda url: text)
    assert scrape.recheck(project) == []


def test_source_hash_is_whitespace_and_case_canonical():
    assert scrape.source_hash("Hello   World") == scrape.source_hash("hello world")
    assert isinstance(scrape.source_hash("x"), str) and len(scrape.source_hash("x")) == 16


def test_source_drift_is_a_known_finding_kind_but_never_blocks():
    from fux import findings
    assert "source-drift" in findings.KINDS
    f = Finding("source-drift", "r", "changed")
    assert findings.blocking([f], mode="strict") == []   # opt-in advisory, never gates
