"""YAML-subset scalar coercion + flow-list splitting (frontmatter helper)."""
from __future__ import annotations


def scalar(raw: str):
    """Coerce a raw token to str/list/bool/None, honouring quotes and flow lists."""
    raw = raw.strip()
    if raw.startswith("[") and raw.endswith("]"):
        inner = raw[1:-1].strip()
        return [scalar(x) for x in split_flow(inner)] if inner else []
    if len(raw) >= 2 and raw[0] in "'\"" and raw[-1] == raw[0]:
        return raw[1:-1]
    if raw in ("true", "false"):
        return raw == "true"
    if raw in ("null", "~", ""):
        return None
    return raw


def split_flow(inner: str) -> list[str]:
    """Split a flow-list body on top-level commas (nested brackets respected)."""
    parts, depth, cur = [], 0, ""
    for ch in inner:
        if ch == "," and depth == 0:
            parts.append(cur)
            cur = ""
        else:
            depth += (1 if ch == "[" else -1 if ch == "]" else 0)
            cur += ch
    if cur.strip():
        parts.append(cur)
    return parts
