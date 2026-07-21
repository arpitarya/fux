"""Capture a concluded `/fux debate` or decision-council as a tamper-evident ADR,
routed to the right store by content (decision-capture-handoff.md).

`$0`, stdlib, deterministic: the *debating* is the host agent's tokens; the capture
— format the ADR, seal it, route it — is pure harness. Firewall (ADR 0001): a money
decision routes to **elgar** and fux keeps only `elgar://decision/<id>`, never the
body. `check.py` re-verifies the seal + the link-only firewall on every run.
"""
from __future__ import annotations

from pathlib import Path

from fux import constitution, fmwrite, paths, provenance
from fux.findings import Finding
from fux.model import Rule

ROUTES = ("fux", "anton", "elgar")
_SECTIONS = ("decision", "why", "crux", "strongest_dissent", "what_would_reverse")
# The only body a fux-side elgar record may carry — the link, nothing of the payload.
_STUB = ("The decision body lives in elgar (private). Per ADR 0001 fux holds only the\n"
         "link below — never the money content.\n\n- elgar_ref: {ref}")


def build_adr(meta: dict, sections: dict) -> tuple[dict, str]:
    """Frontmatter + Markdown body for an ADR from the agent's verdict. Deterministic."""
    fm = {"id": meta["id"], "type": "adr", "status": "active", "date": meta["date"],
          "decided_by": meta["decided_by"], "method": meta["method"], "route": meta["route"]}
    title = sections.get("title") or meta["id"].replace("-", " ")
    parts = [f"# ADR — {title}"]
    for key in _SECTIONS:
        if sections.get(key):
            parts.append(f"## {key.replace('_', ' ').title()}\n{sections[key].strip()}")
    return fm, "\n\n".join(parts) + "\n"


def capture(root: Path, meta: dict, sections: dict, debate: Path | None = None) -> Path:
    """Write the routed, sealed ADR. money/elgar → link-only stub (firewall, ADR 0001)."""
    if meta["route"] not in ROUTES:
        raise ValueError(f"route must be one of {ROUTES}")
    fp = paths.Footprint(root)
    target = fp.decisions / f"{meta['id']}.md"
    target.parent.mkdir(parents=True, exist_ok=True)

    if meta["route"] == "elgar":
        ref = f"elgar://decision/{meta['id']}"
        fm, body = build_adr(meta, {"title": sections.get("title")})
        fm["elgar_ref"] = ref
        body = f"# ADR — {sections.get('title') or meta['id']}\n\n" + _STUB.format(ref=ref) + "\n"
    else:
        fm, body = build_adr(meta, sections)

    sealed = Rule(id=str(fm["id"]), type="adr", fm=fm, body=body, path=target, layer="project")
    rat: dict = {"by": meta["decided_by"], "date": meta["date"],
                 "content_seal": constitution.content_seal(sealed)}
    if debate is not None:
        canon = provenance.transcript_path(root, meta["id"])
        canon.parent.mkdir(parents=True, exist_ok=True)
        if debate.resolve() != canon.resolve():
            canon.write_bytes(debate.read_bytes())
        rat["debate_hash"] = provenance.transcript_hash(canon)
    fm["ratification"] = rat
    target.write_text(fmwrite.dump(fm, body), encoding="utf-8")
    return target


def _decisions(rules: list[Rule]) -> list[Rule]:
    return [r for r in rules if str(r.fm.get("type")) == "adr"
            and (r.fm.get("ratification") or {}).get("content_seal")]


def check_seals(rules: list[Rule]) -> list[Finding]:
    """`tampered` for a captured ADR whose body/frontmatter changed since capture."""
    out: list[Finding] = []
    for r in _decisions(rules):
        stored = r.fm["ratification"]["content_seal"]
        if constitution.content_seal(r) != stored:
            out.append(Finding("tampered", r.id, "decision record changed since capture — "
                               "content_seal mismatch; ADRs are immutable, supersede instead"))
    return out


def check_firewall(rules: list[Rule]) -> list[Finding]:
    """ADR 0001: a fux-side elgar decision must be **link-only** — the body minus the
    heading + canonical stub must be empty; any residual (a money figure, a portfolio
    note) is a firewall breach, regardless of the seal."""
    out: list[Finding] = []
    for r in rules:
        if str(r.fm.get("type")) != "adr":
            continue
        if r.fm.get("route") != "elgar" and not r.fm.get("elgar_ref"):
            continue
        ref = r.fm.get("elgar_ref")
        if not ref:
            out.append(Finding("firewall", r.id, "route: elgar but no elgar_ref link"))
            continue
        rest = "\n".join(ln for ln in r.body.splitlines() if not ln.startswith("# "))
        if rest.replace(_STUB.format(ref=ref), "").strip():
            out.append(Finding("firewall", r.id, "elgar-routed decision is not link-only — "
                               "fux must hold only the elgar:// link, never the body (ADR 0001)"))
    return out
