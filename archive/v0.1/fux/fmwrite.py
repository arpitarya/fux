"""Frontmatter serializer — writes the dict back as YAML-subset (fix-mode)."""
from __future__ import annotations

# Stable key order so diffs stay clean across regenerations.
ORDER = ["id", "domain", "type", "subtype", "scope", "status", "tier", "principle",
         "enforcement", "created", "updated", "author", "aliases", "keywords",
         "code_refs", "related", "edges", "seal", "ratification", "check", "examples"]


def dump(fm: dict, body: str) -> str:
    keys = [k for k in ORDER if k in fm] + [k for k in fm if k not in ORDER]
    lines = ["---"]
    for k in keys:
        lines += _emit(k, fm[k])
    lines.append("---")
    return "\n".join(lines) + "\n" + body.rstrip("\n") + "\n"


def _emit(key: str, val, indent: int = 0) -> list[str]:
    pad = " " * indent
    if isinstance(val, dict):
        out = [f"{pad}{key}:"]
        for k, v in val.items():
            out += _emit(k, v, indent + 2)
        return out
    if isinstance(val, list):
        if val and isinstance(val[0], dict):
            out = [f"{pad}{key}:"]
            for item in val:
                first = True
                for k, v in item.items():
                    prefix = f"{pad}  - " if first else f"{pad}    "
                    out.append(f"{prefix}{k}: {_scalar(v)}")
                    first = False
            return out
        return [f"{pad}{key}:"] + [f"{pad}  - {_scalar(v)}" for v in val]
    return [f"{pad}{key}: {_scalar(val)}"]


def _scalar(v) -> str:
    if v is None:
        return ""
    if isinstance(v, bool):
        return "true" if v else "false"
    s = str(v)
    # Quote when the bare token would round-trip through `scalars.scalar()` as a
    # NON-string — bool (`true`/`false`), None (`null`/`~`/``), or a flow list
    # (`[…]`) — or carries a YAML-significant char. Emitting such a string bare
    # flips its parsed type on the next read, which (e.g. for a ratified rule's
    # `expect: "true"` example) changes `content_seal` and raises a false
    # `tampered`. Keep the writer's output a fixed point of the reader.
    reparses_nonstring = s in ("true", "false", "null", "~", "") or s[:1] == "["
    return f'"{s}"' if (reparses_nonstring or ":" in s or s.strip() != s) else s
