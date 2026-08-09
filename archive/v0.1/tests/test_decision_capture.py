"""Decision capture — routed, tamper-evident ADRs + the ADR 0001 money firewall
(decision-capture-handoff.md). The capture path is $0/deterministic; the firewall
guarantees a fux-side money decision is link-only, never the body.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from fux import check, config, constitution, decisioncapture, fmwrite, initcmd, loader, paths
from fux.findings import blocking
from fux.model import Rule


@pytest.fixture
def proj(tmp_path):
    root = tmp_path / "p"
    root.mkdir()
    initcmd.run(root)
    return root


def _rules(root: Path):
    return loader.resolve(root, config.load(paths.Footprint(root).config)).rules


def _verdict():
    return {"title": "Use Postgres", "decision": "Adopt Postgres.",
            "why": "ACID + ops familiarity.", "crux": "durability vs raw speed"}


def test_fux_route_writes_full_sealed_adr(proj):
    meta = {"id": "use-pg", "date": "2026-06-29", "decided_by": "Arpit",
            "method": "debate", "route": "fux"}
    target = decisioncapture.capture(proj, meta, _verdict())
    assert target == paths.Footprint(proj).decisions / "use-pg.md"
    fm, body = fmwrite_split(target)
    assert fm["type"] == "adr" and fm["route"] == "fux"
    assert fm["ratification"]["content_seal"]
    assert "Adopt Postgres." in body
    assert not check.run(proj)               # clean: seal + firewall pass


def test_money_route_is_link_only(proj):
    meta = {"id": "pf-q3", "date": "2026-06-29", "decided_by": "Arpit",
            "method": "decision-council", "route": "elgar"}
    target = decisioncapture.capture(proj, meta, {"title": "Q3 portfolio"})
    assert "elgar://decision/pf-q3" in target.read_text(encoding="utf-8")
    fm, body = fmwrite_split(target)
    assert fm["elgar_ref"] == "elgar://decision/pf-q3"
    assert "equity" not in body and "₹" not in body and "Rs" not in body
    assert not check.run(proj)               # link-only → firewall passes


def test_editing_a_captured_adr_trips_tampered(proj):
    meta = {"id": "use-pg", "date": "2026-06-29", "decided_by": "A",
            "method": "debate", "route": "fux"}
    target = decisioncapture.capture(proj, meta, _verdict())
    target.write_text(target.read_text(encoding="utf-8") + "\nsneaky edit\n", encoding="utf-8")
    kinds = {f.kind for f in check.run(proj)}
    assert "tampered" in kinds


def test_firewall_flags_money_in_an_elgar_record(proj):
    """A sealed elgar record that is NOT link-only is a firewall breach (ADR 0001)."""
    fp = paths.Footprint(proj)
    p = fp.decisions / "leak.md"
    p.parent.mkdir(parents=True, exist_ok=True)
    fm = {"id": "leak", "type": "adr", "status": "active", "date": "2026-06-29",
          "decided_by": "A", "method": "debate", "route": "elgar",
          "elgar_ref": "elgar://decision/leak"}
    body = "# ADR — leak\n\nMoved Rs 5,00,000 to equity.\n"
    r = Rule(id="leak", type="adr", fm=fm, body=body, path=p, layer="project")
    fm["ratification"] = {"by": "A", "date": "2026-06-29",
                          "content_seal": constitution.content_seal(r)}
    p.write_text(fmwrite.dump(fm, body), encoding="utf-8")
    findings = check.run(proj)
    fw = [f for f in findings if f.kind == "firewall"]
    assert fw and fw[0].rule_id == "leak"
    assert blocking(findings, mode="report")  # firewall blocks in ANY mode


def fmwrite_split(path: Path):
    from fux import frontmatter
    fm, body = frontmatter.split(path.read_text(encoding="utf-8"))
    return fm, body
