"""Constitutional integrity — tamper-evidence, ratification & the lock ($0, deterministic).
A ratified constitutional rule (§6) carries `ratification.content_seal`, recorded in
`.fux/constitution.lock`; `fux check` recomputes both → always-blocking `tampered`; `fux
ratify` is the only path that stamps them. No LLM, no new deps."""
from __future__ import annotations

import json
from pathlib import Path

from fux import seal
from fux.findings import Finding
from fux.model import Rule

LOCK = "constitution.lock"                       # under .fux/
_VOLATILE = {"ratification", "seal", "updated"}  # change without changing meaning


def content_seal(rule: Rule) -> str:
    """Tamper fingerprint: hash of the rule's normalized body + governing frontmatter
    (volatile seal/ratification/updated excluded). Reuses seal.py's hash + whitespace fold."""
    gov = {k: v for k, v in rule.fm.items() if k not in _VOLATILE}
    blob = json.dumps(gov, sort_keys=True, ensure_ascii=False, default=str)
    return seal._hash(blob + "\n" + " ".join(rule.body.split()))


def _constitutional(rules: list[Rule]) -> list[Rule]:
    return [r for r in rules if str(r.fm.get("tier")) == "constitutional"]


def check_tamper(rules: list[Rule]) -> list[Finding]:
    """`tampered` for any ratified constitutional rule whose recomputed content_seal no
    longer matches its stamped `ratification.content_seal` (a body/meaning edit)."""
    out: list[Finding] = []
    for r in _constitutional(rules):
        stored = (r.fm.get("ratification") or {}).get("content_seal")
        if stored and content_seal(r) != stored:
            out.append(Finding("tampered", r.id,
                                "body/frontmatter changed since ratification — constitutional "
                                "rules never change in place; supersede + re-ratify"))
    return out


def lock_manifest(rules: list[Rule]) -> dict[str, str]:
    """The expected lock — {id: stamped content_seal} for every ratified constitutional rule."""
    out = {r.id: (r.fm.get("ratification") or {}).get("content_seal")
           for r in _constitutional(rules)}
    return {k: v for k, v in sorted(out.items()) if v}


def _lock_path(root: Path) -> Path:
    return root / ".fux" / LOCK


def _read_lock(root: Path) -> dict[str, str]:
    p = _lock_path(root)
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def check_lock(root: Path, rules: list[Rule]) -> list[Finding]:
    """`tampered` wherever `.fux/constitution.lock` and the live ratified set diverge —
    a constitutional rule added, deleted, or re-stamped outside `fux ratify`."""
    locked, current = _read_lock(root), lock_manifest(rules)
    out: list[Finding] = []
    for rid in sorted(set(locked) | set(current)):
        lo, cu = locked.get(rid), current.get(rid)
        if lo == cu:
            continue
        why = ("missing/un-ratified on disk — restore + `fux ratify`" if cu is None
               else "absent from the lock — `fux ratify` to record" if lo is None
               else "content_seal differs from the lock — changed outside `fux ratify`")
        out.append(Finding("tampered", rid, "constitution.lock mismatch: " + why))
    return out


def ratify(root: Path, rules: list[Rule], rule_id: str, by: str, date: str,
           debate_hash: str | None = None) -> Rule:
    """The only path into the constitutional tier: stamp ratification.{by,date,content_seal,
    debate_hash?}, freeze the code seal, rewrite `.fux/constitution.lock`. Raises if id absent
    or not constitutional. Deterministic — no LLM, no clock (caller supplies date + hash)."""
    from fux import fmwrite
    rule = next((r for r in rules if r.id == rule_id), None)
    if rule is None:
        raise KeyError(rule_id)
    if str(rule.fm.get("tier")) != "constitutional":
        raise ValueError(f"{rule_id} is tier={rule.fm.get('tier', 'standard')}, not constitutional")
    rat = {"by": by, "date": date, "content_seal": content_seal(rule)}
    rule.fm["ratification"] = {**rat, "debate_hash": debate_hash} if debate_hash else rat
    if (code_seal := seal.current(root, rule)):
        rule.fm["seal"] = code_seal
    rule.path.write_text(fmwrite.dump(rule.fm, rule.body), encoding="utf-8")
    lock = _lock_path(root)
    lock.parent.mkdir(parents=True, exist_ok=True)
    lock.write_text(json.dumps(lock_manifest(rules), indent=2, sort_keys=True) + "\n",
                    encoding="utf-8")
    return rule
