"""`fux setup` — one setup command, interactive *and* flag-driven.

Interactive wizard by default (clig.dev convention); every prompt has a flag;
`-y` accepts defaults; re-runs are idempotent and preserve user-edited keys the
wizard doesn't manage (the existing fux.toml is parsed and merged, not
clobbered). Agent-integration flags (`--agents --skills --hooks`) are wired in
:mod:`fux.agents.generate`.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import tomllib

from .config import CONFIG_NAME, DEFAULT_EXCLUDES, SOURCE_TYPES
from .errors import FuxError

_TYPE_PROMPTS = {
    "docs": "Docs folders (md/txt/office)",
    "code": "Code folders (py/js/…)",
    "data": "Data folders (json/yaml)",
    "images": "Image folders (png/jpg)",
}


def cmd_setup(args) -> int:
    root = Path.cwd()
    path = root / CONFIG_NAME
    existing: dict = {}
    if path.is_file():
        try:
            existing = tomllib.loads(path.read_text(encoding="utf-8"))
        except tomllib.TOMLDecodeError as exc:
            raise FuxError(f"existing {CONFIG_NAME} is not valid TOML: {exc}") from exc

    sources = _resolve_sources(args, existing, root)
    merged = _merge(existing, sources)
    text = _dump_toml(merged)
    changed = not path.is_file() or path.read_text(encoding="utf-8") != text
    if changed:
        path.write_text(text, encoding="utf-8")

    summary = " · ".join(
        f"{t}: {', '.join(sources[t]) if sources[t] else '—'}" for t in SOURCE_TYPES
    )
    print(f"{'wrote' if changed else 'unchanged'} {CONFIG_NAME}  ({summary})")

    if getattr(args, "agents", False) or getattr(args, "skills", False) or getattr(args, "hooks", False):
        from .agents.generate import generate_agent_files

        results = generate_agent_files(
            root,
            agents=getattr(args, "agents", False),
            skills=getattr(args, "skills", False),
            hooks=getattr(args, "hooks", False),
        )
        for rel, state in results:
            print(f"{state:>9}  {rel}")

    if changed and not any(sources.values()):
        print("hint: no source folders configured yet — re-run `fux setup` or edit fux.toml")
    elif changed:
        print("next: run `fux ingest`")
    return 0


def _resolve_sources(args, existing: dict, root: Path) -> dict[str, list[str]]:
    prior = existing.get("sources", {}) if isinstance(existing.get("sources"), dict) else {}
    resolved: dict[str, list[str]] = {}
    for t in SOURCE_TYPES:
        default = [d for d in prior.get(t, []) if isinstance(d, str)]
        if not default and t == "docs" and not prior:
            default = ["docs"] if (root / "docs").is_dir() else []
        flag_val = getattr(args, t, None)
        if flag_val is not None:
            resolved[t] = _split_dirs(flag_val)
        elif args.yes:
            resolved[t] = default
        else:
            resolved[t] = _prompt(_TYPE_PROMPTS[t], default)
    return resolved


def _split_dirs(values: list[str]) -> list[str]:
    out: list[str] = []
    for v in values:
        out.extend(p.strip().rstrip("/") for p in v.split(",") if p.strip())
    return out


def _prompt(label: str, default: list[str]) -> list[str]:
    shown = ", ".join(default) if default else "none"
    try:
        raw = input(f"{label} [{shown}]: ").strip()
    except EOFError:  # non-interactive stdin behaves like -y
        return default
    if not raw:
        return default
    if raw.lower() in ("-", "none"):
        return []
    return _split_dirs([raw])


def _merge(existing: dict, sources: dict[str, list[str]]) -> dict:
    """Managed keys updated, user keys preserved, defaults filled where absent."""
    merged = dict(existing)
    merged["sources"] = {t: sources[t] for t in SOURCE_TYPES}
    ingest = dict(existing.get("ingest", {}))
    ingest.setdefault("max_kb", 256)
    ingest.setdefault("exclude", list(DEFAULT_EXCLUDES))
    merged["ingest"] = ingest
    engine = dict(existing.get("engine", {}))
    bm25f = dict(engine.get("bm25f", {}))
    for key, default in (("heading", 3.0), ("path", 2.0), ("body", 1.0), ("k1", 1.2), ("b", 0.75)):
        bm25f.setdefault(key, default)
    engine["bm25f"] = bm25f
    merged["engine"] = engine
    answer = dict(existing.get("answer", {}))
    answer.setdefault("max_sentences", 5)
    merged["answer"] = answer
    return merged


# -- deterministic TOML writer (subset: tables of scalars/lists) -----------

_SECTION_ORDER = ("sources", "ingest", "engine", "answer")


def _dump_toml(data: dict) -> str:
    lines = [f"# {CONFIG_NAME} — Fux project configuration (managed by `fux setup`)", ""]
    ordered = [k for k in _SECTION_ORDER if k in data] + sorted(
        k for k in data if k not in _SECTION_ORDER
    )
    for section in ordered:
        value = data[section]
        if not isinstance(value, dict):
            lines.insert(2, f"{section} = {_fmt_value(value)}")
            continue
        _dump_table(lines, section, value)
    return "\n".join(lines).rstrip("\n") + "\n"


def _dump_table(lines: list[str], name: str, table: dict) -> None:
    scalars = {k: v for k, v in table.items() if not isinstance(v, dict)}
    subtables = {k: v for k, v in table.items() if isinstance(v, dict)}
    if scalars or not subtables:
        lines.append(f"[{name}]")
        for key, value in scalars.items():
            lines.append(f"{key} = {_fmt_value(value)}")
        lines.append("")
    for sub, subtable in subtables.items():
        _dump_table(lines, f"{name}.{sub}", subtable)


def _fmt_value(value) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return repr(value)
    if isinstance(value, list):
        return "[" + ", ".join(_fmt_value(v) for v in value) + "]"
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False)
    raise FuxError(f"cannot serialize {type(value).__name__} into {CONFIG_NAME}")
