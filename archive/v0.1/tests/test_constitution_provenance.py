"""Constitution hardening — regression tests for the verification SLIPs (R1 rows 2, 4, 5).

Each test reproduces an attack that originally passed `fux gate` clean and asserts it now
blocks (exit 2, `tampered`). $0, stdlib, deterministic — no LLM on this path.
"""
from __future__ import annotations

from fux import config, constitution, gate, loader, paths, provenance
from conftest import write_rule

CON = """---
id: con-r
type: rule
status: active
tier: constitutional
---
**Rule:** money amounts are integer cents, never floats.
"""
STD = """---
id: std-r
type: rule
status: active
---
**Rule:** a normal convention.
"""
DEBATE = "# Debate: money is integer cents\nA: floats lose pennies.\nB: agreed.\nHuman: ratified.\n"


def _ratify(project, rid, debate_hash=None):
    cfg = config.load(paths.Footprint(project).config)
    rules = loader.resolve(project, cfg).rules
    return constitution.ratify(project, rules, rid, by="Arpit", date="2026-06-17",
                               debate_hash=debate_hash)


# --- Row 2: add a constitutional rule without `fux ratify` ---------------------------------

def test_unratified_constitutional_rule_blocks(project):
    """Originally SLIPPED: a tier:constitutional rule with no ratification block passed clean."""
    write_rule(project, "con-r", CON)            # never ratified — no .lock, no content_seal
    code, report = gate.run(project)
    assert code == 2 and "tampered" in report
    assert "un-ratified" in report


# --- Row 5: promote a standard rule via a tier: frontmatter edit ---------------------------

def test_promote_standard_via_tier_edit_blocks(project):
    """Originally SLIPPED: flipping tier:constitutional on a standard rule passed clean."""
    write_rule(project, "std-r", STD)
    code, _ = gate.run(project)
    assert code == 0                             # standard rule alone is clean
    p = project / ".fux" / "rules" / "std-r.md"
    p.write_text(p.read_text().replace("status: active",
                                       "status: active\ntier: constitutional"), encoding="utf-8")
    code, report = gate.run(project)
    assert code == 2 and "tampered" in report    # promotion into the apex without ratify → blocks


# --- Row 4: edit a ratified debate transcript ---------------------------------------------

def test_transcript_tamper_blocks(project):
    """Originally SLIPPED: rewriting a ratified transcript fired nothing."""
    write_rule(project, "con-r", CON)
    src = project / "con-r.debate.md"
    src.write_text(DEBATE, encoding="utf-8")
    # ratify with the transcript → pins it to .fux/debates/con-r.md + stamps debate_hash
    cfg = config.load(paths.Footprint(project).config)
    rules = loader.resolve(project, cfg).rules
    dhash = provenance.transcript_hash(src)
    canon = provenance.transcript_path(project, "con-r")
    canon.parent.mkdir(parents=True, exist_ok=True)
    canon.write_bytes(src.read_bytes())
    constitution.ratify(project, rules, "con-r", by="Arpit", date="2026-06-17", debate_hash=dhash)
    code, _ = gate.run(project)
    assert code == 0                             # ratified + transcript intact → clean
    canon.write_text(DEBATE.replace("integer cents", "floats are fine"), encoding="utf-8")
    code, report = gate.run(project)
    assert code == 2 and "tampered" in report    # transcript drift → blocks
    assert "transcript" in report


def test_missing_transcript_blocks(project):
    """A stamped debate_hash with no transcript on disk cannot be verified → blocks."""
    write_rule(project, "con-r", CON)
    _ratify(project, "con-r", debate_hash="deadbeefdeadbeef")  # stamp, but never pin a file
    code, report = gate.run(project)
    assert code == 2 and "tampered" in report
    assert "missing" in report


def test_non_constitutional_transcript_edit_does_not_block(project):
    """Provenance is constitutional-only: a standard rule's transcript edit must not block."""
    findings = provenance.check_provenance(project, loader.resolve(
        project, config.load(paths.Footprint(project).config)).rules)
    assert findings == []                        # no ratified constitutional rule → nothing fires
