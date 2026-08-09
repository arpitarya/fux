"""`fux doctor` — whole-install/corpus diagnosis (handoff 0005 §C).

Seven groups (environment, capabilities, config, corpus, consistency, agent
surface, self-test), each a list of :class:`Check`. Every failing check names
what is wrong, why it matters, and the exact fix command — a check that only
reports is half-built. Exit 0 healthy, 1 problems found; `--json` mirrors the
same structure for agents (schema documented in docs/example/DEBUG.md).
"""

from __future__ import annotations

import json as _json
import shutil
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from . import __version__
from .config import SOURCE_TYPES, find_root, load
from .errors import FuxError

PY_MIN = (3, 11)


@dataclass
class Check:
    name: str
    ok: bool
    detail: str
    why: str = ""
    fix: str = ""

    def to_json(self) -> dict:
        out = {"name": self.name, "ok": self.ok, "detail": self.detail}
        if not self.ok:
            if self.why:
                out["why"] = self.why
            if self.fix:
                out["fix"] = self.fix
        return out


@dataclass
class Group:
    name: str
    checks: list[Check] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return all(c.ok for c in self.checks)

    def to_json(self) -> dict:
        return {"name": self.name, "ok": self.ok, "checks": [c.to_json() for c in self.checks]}


def run(start: Path | None = None) -> list[Group]:
    """The seven groups. A missing `fux.toml` short-circuits after `config`."""
    groups = [_environment(), _capabilities()]
    config_group = _config_group(start)
    groups.append(config_group)
    if not any(c.name == "fux.toml" and c.ok for c in config_group.checks):
        return groups
    root = find_root(start)
    config = load(root)
    groups.append(_corpus_group(config))
    groups.append(_consistency_group(config))
    groups.append(_agent_surface_group(root))
    groups.append(_self_test_group())
    return groups


# -- environment --------------------------------------------------------------


def _environment() -> Group:
    checks = []
    checks.append(Check("fux version", True, f"fux {__version__}"))
    py_ok = sys.version_info[:2] >= PY_MIN
    checks.append(
        Check(
            "python version",
            py_ok,
            f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            why=f"fux requires Python >= {'.'.join(map(str, PY_MIN))} (tomllib, modern typing)",
            fix=f"install Python >= {'.'.join(map(str, PY_MIN))}",
        )
    )
    checks.append(Check("install path", True, str(Path(__file__).parent)))
    checks.append(_bundled_model_check())
    return Group("environment", checks)


def _bundled_model_check() -> Check:
    from .embed.model import DATA_PATH

    meta_path = DATA_PATH.parent / "model.json"
    if not DATA_PATH.is_file():
        return Check(
            "bundled model", True,
            "not bundled (source install — `--lexical-only` still works)",
        )
    if not meta_path.is_file():
        return Check("bundled model", True, f"present, {DATA_PATH.stat().st_size} bytes (unpinned)")
    import hashlib

    try:
        meta = _json.loads(meta_path.read_text(encoding="utf-8"))
    except ValueError:
        return Check(
            "bundled model", False, "model.json is not valid JSON",
            why="the pinned sha256 can't be checked — a corrupt bundle can silently degrade hybrid search",
            fix="reinstall fux-engine, or rebuild via tools/distill/distill.py",
        )
    actual = hashlib.sha256(DATA_PATH.read_bytes()).hexdigest()
    expected = meta.get("sha256", "")
    if actual != expected:
        return Check(
            "bundled model", False, f"sha256 {actual[:12]}… != pinned {expected[:12]}…",
            why="a tampered or corrupt model bundle can silently degrade hybrid search results",
            fix="reinstall fux-engine from PyPI, or rebuild via tools/distill/distill.py",
        )
    return Check("bundled model", True, f"present, sha256 verified ({DATA_PATH.stat().st_size} bytes)")


# -- capabilities: optional, never fail health --------------------------------


def _capabilities() -> Group:
    checks = [
        _capability("markitdown", _has_module("markitdown"), "pip install 'fux-engine[ingest]'"),
        _capability("docling", _has_module("docling"), "pip install docling"),
        _capability(
            "tesseract", shutil.which("tesseract") is not None,
            "brew install tesseract (macOS) / apt install tesseract-ocr (Linux)",
        ),
        _capability(
            "Chrome for CDP", _has_chrome_binary(),
            "install Google Chrome/Chromium, then `fux ingest --web` with "
            "[sources.web] render = \"cdp\" (doctor checks the binary only — "
            "not network-reachable; not the query path)",
        ),
        _capability(
            "websocket-client (CDP fallback)", _has_module("websocket"),
            "pip install websocket-client (optional — the hand-rolled RFC 6455 client is primary)",
        ),
    ]
    return Group("capabilities", checks)


_CHROME_BINARIES = (
    "google-chrome", "google-chrome-stable", "chromium", "chromium-browser",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
)


def _has_chrome_binary() -> bool:
    return any(
        shutil.which(name) or Path(name).is_file() for name in _CHROME_BINARIES
    )


def _capability(name: str, available: bool, install: str) -> Check:
    detail = "available" if available else f"not installed — {install}"
    return Check(name, True, detail)


def _has_module(name: str) -> bool:
    try:
        __import__(name)
        return True
    except ImportError:
        return False


# -- config --------------------------------------------------------------------


def _config_group(start: Path | None) -> Group:
    checks = []
    try:
        root = find_root(start)
    except FuxError as exc:
        checks.append(
            Check(
                "fux.toml", False, str(exc),
                why="no config means no sources, no ingest, nothing to query",
                fix="fux setup",
            )
        )
        return Group("config", checks)
    checks.append(Check("fux.toml", True, str((root / "fux.toml").resolve())))
    config = load(root)
    for stype in SOURCE_TYPES:
        for src_dir in config.sources.get(stype, ()):
            base = root / src_dir if not Path(src_dir).is_absolute() else Path(src_dir)
            if not base.is_dir():
                checks.append(
                    Check(
                        f"[sources] {stype} = {src_dir!r}", False, "directory does not exist",
                        why="this entry will never contribute documents to the corpus",
                        fix=f"fix the path in fux.toml, or `mkdir -p {src_dir}`",
                    )
                )
                continue
            count = sum(1 for p in base.rglob("*") if p.is_file())
            if count == 0:
                checks.append(
                    Check(
                        f"[sources] {stype} = {src_dir!r}", False,
                        "directory exists but matches 0 files",
                        why="the #1 silent misconfig — this entry contributes nothing, "
                        "and `fux ingest` will not warn you",
                        fix=f"check fux.toml — did you mean a different directory for [sources] {stype}?",
                    )
                )
            else:
                checks.append(Check(f"[sources] {stype} = {src_dir!r}", True, f"{count} files"))
    if not any(config.sources.values()):
        checks.append(
            Check(
                "[sources]", False, "no source folders configured",
                why="`fux ingest` has nothing to convert",
                fix="fux setup --docs <dir>",
            )
        )
    checks.append(Check("[ingest] exclude", True, ", ".join(config.ingest.exclude)))
    return Group("config", checks)


# -- corpus ----------------------------------------------------------------


def _corpus_group(config) -> Group:
    from .index import backend_for
    from .ingest.manifest import read as manifest_read

    checks = []
    root = config.root
    manifest = manifest_read(root)
    checks.append(Check("manifest", bool(manifest), f"{len(manifest)} sources tracked"))
    lock_path = root / "fux.lock"
    checks.append(
        Check(
            "fux.lock", lock_path.is_file(),
            "present" if lock_path.is_file() else "missing",
            why="no committed ledger — `fux ingest --check` cannot work on a fresh clone",
            fix="fux ingest",
        )
    )
    state_dir = root / ".fux" / "state"
    checks.append(
        Check(
            "state plane (.fux/state/)", state_dir.is_dir(),
            "present" if state_dir.is_dir() else "missing",
            why="a fresh clone cannot answer before `fux ingest` without it",
            fix="fux ingest",
        )
    )
    backend = backend_for(config)
    try:
        files = backend.load(root)
        chunks = sum(len(m.get("chunks", [])) for m in files.values())
        fmt = "sqlite" if backend.__name__.endswith("sqlstore") else "json"
        checks.append(Check("index", True, f"{fmt} · {len(files)} docs · {chunks} chunks"))
    except Exception as exc:  # noqa: BLE001 — any load failure is a diagnosis, not a crash
        checks.append(
            Check(
                "index", False, f"failed to load ({exc})",
                why="queries will fail or fall back to doc-level state",
                fix="fux ingest",
            )
        )
    for label, rel in (("cache (.fux/cache/)", ".fux/cache"), ("index (.fux/index/)", ".fux/index")):
        path = root / rel
        size = sum(p.stat().st_size for p in path.rglob("*") if p.is_file()) if path.is_dir() else 0
        checks.append(Check(label, True, f"{size} bytes" if path.is_dir() else "absent"))
    return Group("corpus", checks)


# -- consistency -------------------------------------------------------------


def _consistency_group(config) -> Group:
    from .ingest.lock import check as lock_check

    checks = []
    try:
        status = lock_check(config)
    except Exception as exc:  # noqa: BLE001
        return Group("consistency", [Check("three-way check", False, str(exc))])
    checks.append(
        Check(
            "drift (source ↔ lock)", not status.drift, f"{len(status.drift)} drifted",
            why="a source changed since the last ingest; queries answer from stale text",
            fix="fux ingest",
        )
    )
    checks.append(
        Check(
            "stale (web max_age_days)", not status.stale, f"{len(status.stale)} stale",
            why="a crawled page is past its freshness horizon",
            fix="fux ingest --web",
        )
    )
    checks.append(
        Check(
            "desync (state ↔ lock)", not status.desync, f"{len(status.desync)} desynced",
            why="the committed state plane disagrees with fux.lock — a fresh clone would answer wrong",
            fix="fux ingest",
        )
    )
    return Group("consistency", checks)


# -- agent surface -----------------------------------------------------------


def _agent_surface_group(root: Path) -> Group:
    checks = []
    checks.append(_presence("AGENTS.md", root / "AGENTS.md"))
    for name in ("fux-query", "fux-ingest", "fux-debug"):
        checks.append(_presence(f"skill: {name}", root / ".claude" / "skills" / name / "SKILL.md"))
    settings = root / ".claude" / "settings.json"
    if settings.is_file():
        try:
            data = _json.loads(settings.read_text(encoding="utf-8"))
            wired = "UserPromptSubmit" in data.get("hooks", {})
            checks.append(
                Check(
                    "hooks (.claude/settings.json)", True,
                    "wired" if wired else "present but no fux hooks",
                )
            )
        except ValueError:
            checks.append(
                Check(
                    "hooks (.claude/settings.json)", False, "not valid JSON",
                    why="Claude Code will refuse to load a malformed settings file",
                    fix="fix the JSON syntax, then re-run `fux setup --hooks`",
                )
            )
    else:
        checks.append(Check("hooks (.claude/settings.json)", True, "not installed"))
    return Group("agent surface", checks)


def _presence(name: str, path: Path) -> Check:
    return Check(name, True, "present" if path.is_file() else "not installed")


# -- self-test ----------------------------------------------------------------


def _self_test_group() -> Group:
    """Ingest a temp doc, query it, assert the citation resolves — the whole
    path end to end, in a scratch dir untouched by the real corpus."""
    try:
        with tempfile.TemporaryDirectory(prefix="fux-doctor-") as tmp:
            scratch = Path(tmp)
            (scratch / "docs").mkdir()
            probe = "the-fux-doctor-self-test-canary-term"
            (scratch / "docs" / "canary.md").write_text(
                f"# Canary\n\nThis document exists to prove {probe} end to end.\n",
                encoding="utf-8",
            )
            from .config import load as load_config
            from .ingest import ingest_paths
            from .kernel import retrieve

            (scratch / "fux.toml").write_text('[sources]\ndocs = ["docs"]\n', encoding="utf-8")
            config = load_config(scratch)
            report = ingest_paths(config)
            if report.total != 1:
                return Group(
                    "self-test",
                    [Check("ingest", False, f"expected 1 document, got {report.total}")],
                )
            graph = retrieve(config, probe, k=1, lexical_only=True)
            if not graph.passages:
                return Group(
                    "self-test",
                    [
                        Check(
                            "query", False, "the canary document did not rank for its own term",
                            why="ingest→index→query is broken somewhere in this install",
                            fix="re-install fux-engine, or file a bug",
                        )
                    ],
                )
            cited = scratch / graph.passages[0].file
            if not cited.is_file():
                return Group(
                    "self-test",
                    [Check("citation resolves", False, f"{graph.passages[0].file} not on disk")],
                )
            return Group("self-test", [Check("ingest → index → query → citation", True, "ok")])
    except Exception as exc:  # noqa: BLE001 — a doctor crash must still report, not explode
        return Group("self-test", [Check("self-test", False, f"unexpected failure: {exc}")])


# -- CLI handler ----------------------------------------------------------------


def cmd_doctor(args) -> int:
    groups = run()
    healthy = all(g.ok for g in groups)
    if args.json:
        print(_json.dumps({"healthy": healthy, "groups": [g.to_json() for g in groups]}, ensure_ascii=False))
        return 0 if healthy else 1
    for group in groups:
        mark = "✓" if group.ok else "✗"
        print(f"[{mark}] {group.name}")
        for check in group.checks:
            mark = "  ok" if check.ok else "  FAIL"
            print(f"{mark}  {check.name}: {check.detail}")
            if not check.ok:
                if check.why:
                    print(f"        why: {check.why}")
                if check.fix:
                    print(f"        fix: {check.fix}")
    print()
    print("healthy" if healthy else "problems found — see FAIL rows above")
    return 0 if healthy else 1
