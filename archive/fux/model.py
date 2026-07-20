"""The Rule entry — the atomic unit of the Fux substrate (plan §6)."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

_LABEL = re.compile(r"\*\*[^*]+\*\*[:：]?\s*(.*)")

# Rule types (plan §6). narrative/memory are exempt from atomic sizing.
TYPES = ["rule", "formula", "glossary", "invariant", "adr", "edge-case",
         "convention", "regulatory", "runbook", "narrative", "memory",
         "spec", "task"]
LONGFORM = {"narrative", "memory"}
EDGE_KINDS = ["depends-on", "supersedes", "contradicts", "implements"]


@dataclass
class Rule:
    """A single frontmatter entry plus its prose body and provenance."""
    id: str
    type: str
    fm: dict                       # full frontmatter
    body: str
    path: Path                     # source file
    layer: str                     # "global" | "pack:<name>" | "project"

    @property
    def status(self) -> str:
        return str(self.fm.get("status", "active"))

    @property
    def domain(self) -> str:
        return str(self.fm.get("domain", "general"))

    @property
    def title(self) -> str:
        """A readable one-liner: the heading, or the sentence after a **Label:**."""
        for line in self.body.splitlines():
            s = line.strip()
            if not s:
                continue
            if s.startswith("#"):
                text = s.lstrip("# ").strip()
            else:
                m = _LABEL.match(s)
                text = (m.group(1) if m else s).replace("**", "").replace("*", "").strip()
            if text:
                return text[:77].rstrip() + "…" if len(text) > 78 else text
        return self.id

    @property
    def code_refs(self) -> list[str]:
        return list(self.fm.get("code_refs") or [])

    @property
    def related(self) -> list[str]:
        return list(self.fm.get("related") or [])

    def edges(self) -> dict[str, list[str]]:
        e = self.fm.get("edges") or {}
        return {k: list(v or []) for k, v in e.items()} if isinstance(e, dict) else {}

    @property
    def is_active(self) -> bool:
        return self.status not in ("deprecated",)

    def summary(self) -> str:
        """One-line INDEX entry: id, type, title."""
        return f"{self.id} ({self.type}) — {self.title}"


@dataclass
class RuleSet:
    """Resolved effective ruleset: project ⊕ packs ⊕ global, by precedence."""
    rules: list[Rule] = field(default_factory=list)

    def by_id(self) -> dict[str, Rule]:
        return {r.id: r for r in self.rules}

    def active(self) -> list[Rule]:
        return [r for r in self.rules if r.is_active]
