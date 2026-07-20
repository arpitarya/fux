"""`fux components` — the design-system registry + data-binding catalog ($0, §18.3).

The runtime-generation prerequisite: so Orff composes UI from existing primitives
and binds to real data instead of inventing either. Pure stdlib analysis over the
built graph + source files — component names with their prop fields, plus the
hooks and DTOs a generated component must wire to. Never calls an LLM.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from fux.astextract import sanitize_lines
from fux.graphquery import load

_DECL = re.compile(r"\b(?:interface|type)\s+(\w+)\b")
_MEMBER = re.compile(r"^\s*(?:readonly\s+)?([A-Za-z_]\w*)\s*(\?)?\s*:\s*(.+?);?\s*$")
# Source-scan patterns — backend-independent (work with or without tree-sitter).
_PROPS = re.compile(r"(?:export\s+)?(?:interface|type)\s+(\w+)Props\b")
_DTO = re.compile(r"(?:export\s+)?(?:interface|type)\s+(\w+DTO)\b")
_HOOK = re.compile(r"(?:export\s+)?(?:const|(?:async\s+)?function)\s+(use[A-Z]\w*)")
_TS = (".ts", ".tsx")


def _props_of(text: str, name: str) -> list[dict]:
    """Extract the field list of an `interface/type <name>` block, depth-1 only."""
    san, lines = sanitize_lines(text), text.split("\n")
    start = next((i for i, s in enumerate(san)
                  if (m := _DECL.search(s)) and m.group(1) == name), None)
    if start is None:
        return []
    depth, opened, out = 0, False, []
    for k in range(start, len(san)):
        at_start = depth
        if opened and at_start == 1:
            mm = _MEMBER.match(lines[k])
            if mm and not lines[k].lstrip().startswith(("//", "*", "/*")):
                out.append({"name": mm.group(1), "optional": bool(mm.group(2)),
                            "type": mm.group(3).strip().rstrip(";")})
        for ch in san[k]:
            if ch == "{":
                depth += 1; opened = True
            elif ch == "}":
                depth -= 1
        if opened and depth <= 0:
            break
    return out


def registry(root: Path, scope: str | None = None) -> dict:
    """Components (name + props), data hooks (use*), and DTOs, by scanning the
    TS/TSX sources that the graph covers. Backend-independent — relies on naming
    conventions in the text, not on tree-sitter symbol nodes."""
    graph = load(root)                       # raises SystemExit if no graph yet
    files = sorted({n["file"] for n in graph["nodes"]
                    if n.get("type") == "code-file" and (n.get("file") or "").endswith(_TS)
                    and (not scope or n["file"].startswith(scope))})
    comps, hooks, dtos, seen = [], [], [], set()
    for rel in files:
        try:
            text = (root / rel).read_text(encoding="utf-8")
        except OSError:
            continue
        for i, line in enumerate(sanitize_lines(text), 1):
            if (m := _PROPS.search(line)):
                comps.append({"name": m.group(1), "file": rel, "line": i,
                              "props": _props_of(text, m.group(1) + "Props")})
            if (d := _DTO.search(line)):
                dtos.append({"name": d.group(1), "file": rel})
            if (h := _HOOK.search(line)) and (h.group(1), rel) not in seen:
                seen.add((h.group(1), rel))
                hooks.append({"name": h.group(1), "file": rel})
    key = lambda x: x["name"]
    return {"components": sorted(comps, key=key),
            "hooks": sorted(hooks, key=key), "dtos": sorted(dtos, key=key)}


def render(reg: dict, kind: str = "all") -> str:
    out: list[str] = []
    if kind in ("all", "components"):
        out.append(f"## Components ({len(reg['components'])}) — compose from these")
        for c in reg["components"]:
            ps = ", ".join(p["name"] + ("?" if p["optional"] else "") for p in c["props"])
            out.append(f"- **{c['name']}** ({c['file']}) — props: {ps or '—'}")
        out.append("")
    if kind in ("all", "hooks"):
        out.append(f"## Data hooks ({len(reg['hooks'])}) — bind to these, don't refetch")
        out += [f"- {h['name']} ({h['file']})" for h in reg["hooks"]]
        out.append("")
    if kind in ("all", "dtos"):
        out.append(f"## DTOs ({len(reg['dtos'])}) — the data shapes")
        out += [f"- {d['name']} ({d['file']})" for d in reg["dtos"]]
    return "\n".join(out).rstrip() + "\n"


def render_json(reg: dict) -> str:
    return json.dumps(reg, indent=2, ensure_ascii=False) + "\n"
