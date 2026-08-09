"""`fux impact <file>` — downstream blast radius of changing a file ($0, §18.1).

The "maintain code" brain capability: before you touch a file, see what it can
break — invariants to re-verify, governing rules whose *why* may go stale, and
the callers that depend on its symbols. Stdlib graph traversal; no LLM.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from fux import explain, graphquery
from fux.model import Rule


@dataclass
class Impact:
    target: str
    symbols: list[str] = field(default_factory=list)        # symbols defined here
    governing: list[Rule] = field(default_factory=list)     # rules that govern it
    invariants: list[Rule] = field(default_factory=list)    # governing ⊃ machine-checkable
    callers: list[str] = field(default_factory=list)        # precise `calls` dependents
    referenced_by: list[str] = field(default_factory=list)  # loose `references` (INFERRED)
    related: list[str] = field(default_factory=list)        # one-hop related rule ids
    in_graph: bool = True

    @property
    def empty(self) -> bool:
        return not (self.governing or self.callers or self.referenced_by)


def _norm(file_rel: str) -> str:
    return file_rel.replace("\\", "/").lstrip("./").rstrip("/")


def run(root: Path, file_rel: str) -> Impact:
    """Compute the blast radius of editing ``file_rel`` from the built graph."""
    target = _norm(file_rel)
    graph = graphquery.load(root)            # raises SystemExit if no graph yet
    ids = {n["id"] for n in graph["nodes"]}
    # Symbols defined in the file (contains edges: file → symbol).
    symbols = sorted(e["target"] for e in graph["edges"]
                     if e["type"] == "contains" and e["source"] == target)
    sym_set = set(symbols) | {target}

    # Split precise `calls` from loose `references` (INFERRED) so real callers
    # aren't drowned by generic-name collisions (value/total/get).
    callers: set[str] = set()
    referenced_by: set[str] = set()
    for e in graph["edges"]:
        if e["target"] not in sym_set:
            continue
        dependent = e["source"].split("::", 1)[0]
        if dependent == target:
            continue
        if e["type"] == "calls":
            callers.add(dependent)
        elif e["type"] == "references":
            referenced_by.add(dependent)
    referenced_by -= callers                 # a precise call beats a loose ref

    governing = explain.refs(root, target)
    invariants = [r for r in governing if r.type == "invariant" or r.fm.get("check")]
    related = sorted({rid for r in governing for rid in r.related})

    return Impact(target=target, symbols=symbols, governing=governing,
                  invariants=invariants, callers=sorted(callers),
                  referenced_by=sorted(referenced_by),
                  related=related, in_graph=target in ids)


def render(im: Impact) -> str:
    """A maintenance checklist, ordered by how expensive it is to get wrong."""
    out = [f"# impact of changing {im.target}"]
    if not im.in_graph:
        out.append("_(not a graphed file — `fux build` may be stale, or the path is wrong)_")
    inv_ids = {r.id for r in im.invariants}

    def section(title: str, items: list[str], cap: int | None = None) -> None:
        if not items:
            return
        out.extend(["", f"## {title}"])
        out.extend(f"- {x}" for x in (items[:cap] if cap else items))
        if cap and len(items) > cap:
            out.append(f"  …and {len(items) - cap} more")

    section("Invariants that must still hold — run `fux verify`",
            [f"**{r.id}** ({r.type})" + (f" — `{r.fm['check']}`" if r.fm.get("check") else "")
             for r in im.invariants])
    section("Governing rules — update the *why* if behaviour changed",
            [f"{r.id} ({r.type}) — {r.title}" for r in im.governing if r.id not in inv_ids])
    if im.related:
        out += ["", "## Related knowledge to review", "  " + ", ".join(im.related)]
    section(f"Downstream callers ({len(im.callers)} file(s) call into this — re-test)", im.callers)
    section(f"Possibly affected ({len(im.referenced_by)} reference these names — lower confidence)",
            im.referenced_by, cap=10)
    if im.empty:
        out += ["", "No governing rules and no downstream callers found — low blast "
                "radius, or this file isn't graphed/governed yet."]
    return "\n".join(out).strip() + "\n"
