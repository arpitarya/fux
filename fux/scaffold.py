"""`fux new <type> <id>` — scaffold a schema-valid rule stub (plan §10.7)."""
from __future__ import annotations

import datetime as _dt
from pathlib import Path

from fux import fmwrite, paths, schema
from fux.model import TYPES

# Body skeletons per type — the prompts that make authoring low-friction.
_BODIES = {
    "formula": "**Rule:** \n\n**Formula:** `…`\n\n**Why:** \n\n**Edge cases:** ",
    "rule": "**Rule:** \n\n**Why:** \n\n**Edge cases:** ",
    "invariant": "**Invariant:** must always hold.\n\n**Why:** \n\n"
                 "(Set `check:` to a Python expr; `fux verify` runs it.)",
    "adr": "**Decision:** \n\n**Context:** \n\n**Options considered:** \n\n"
           "**Consequences:** ",
    "glossary": "**Term:** \n\n**Definition:** ",
    "edge-case": "**Gotcha:** \n\n**Trigger:** \n\n**Guard:** ",
    "convention": "**Convention:** \n\n**Why:** ",
    "regulatory": "**Rule (external):** \n\n**Source:** \n\n**Applies to:** ",
    "runbook": "**When:** \n\n**Steps:**\n1. \n2. ",
    "narrative": "## Overview\n\n",
    "memory": "**Observation:** \n\n**Why:** \n\n**How to apply:** ",
    "spec": "## Requirements\n\n- As a … I want … so that …\n\n"
            "### Acceptance (EARS)\n- WHEN … THE SYSTEM SHALL …",
    "task": "**Task:** \n\n**Done when:** ",
}


def make(root: Path, rtype: str, rid: str, domain: str = "general") -> Path:
    if rtype not in TYPES:
        raise ValueError(f"unknown type '{rtype}'. one of: {', '.join(TYPES)}")
    today = _dt.date.today().isoformat()
    fm = {"id": rid, "domain": domain, "type": rtype, "status": "draft",
          "created": today, "updated": today, "code_refs": [], "related": []}
    if rtype == "memory":
        fm["subtype"], fm["scope"] = "project", "shared"
        fm["status"] = "active"
    errs = schema.validate(fm)
    if errs:
        raise ValueError("template invalid: " + "; ".join(errs))
    target_dir = _dir_for(root, rtype)
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / f"{rid}.md"
    if target.exists():
        raise FileExistsError(target)
    target.write_text(fmwrite.dump(fm, _BODIES.get(rtype, "")), encoding="utf-8")
    return target


def _dir_for(root: Path, rtype: str) -> Path:
    fp = paths.Footprint(root)
    if rtype == "glossary":
        return fp.glossary
    if rtype == "memory":
        return fp.memory / "shared"
    return fp.rules
