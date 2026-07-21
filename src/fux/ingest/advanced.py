"""Advanced fidelity tier: re-convert one source with a better converter.

`fux ingest --advanced <file|url>` upgrades a single manifest entry:
office/PDF via Docling (layout/table-aware), images via a `tesseract`
subprocess (OCR). Both are extras/host tools — absent-safe with actionable
notices, never runtime deps. The upgrade flips `fidelity: advanced` in the
cache frontmatter and the manifest, and the new text is re-indexed; later
inferred re-ingests keep the advanced entry until the source itself changes
(then honesty wins: it resets to inferred).
"""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

from .. import __version__
from ..config import Config
from ..errors import FuxError
from ..frontmatter import dumps as fm_dumps, parse as fm_parse
from .manifest import read as manifest_read, write as manifest_write

_UPGRADEABLE = {"office": "docling", "image": "tesseract"}


def upgrade(config: Config, target: str) -> str:
    """Upgrade one entry to advanced fidelity; returns a human summary line."""
    entries = manifest_read(config.root)
    entry = _resolve(entries, target, config)
    kind = entry.get("kind", "")
    converter = _UPGRADEABLE.get(kind)
    if converter is None:
        raise FuxError(
            f"no advanced converter for kind {kind!r} ({entry['source']}) — "
            "advanced applies to office/PDF (docling) and images (tesseract)"
        )
    data_path = _source_bytes(config, entry)
    try:
        if converter == "docling":
            body = _docling_convert(data_path)
        else:
            body = _tesseract_convert(data_path, entry)
    finally:
        if data_path.parent == Path(tempfile.gettempdir()):
            data_path.unlink(missing_ok=True)

    cache_path = config.root / entry["cache"]
    fm = fm_parse(cache_path.read_text(encoding="utf-8")) if cache_path.is_file() else None
    meta = fm.meta if fm and fm.meta else _minimal_meta(entry)
    meta["fidelity"] = "advanced"
    meta["converter"] = converter
    if not body.endswith("\n"):
        body += "\n"
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(fm_dumps(meta, body), encoding="utf-8")

    entry["fidelity"] = "advanced"
    entry["converter"] = converter
    entry["fux_version"] = __version__
    manifest_write(config.root, list(entries.values()))

    from ..index import build_index

    chunks = build_index(config, list(entries.values()))
    return f"upgraded {entry['source']} → fidelity: advanced ({converter}); {chunks} chunks indexed"


def _resolve(entries: dict[str, dict], target: str, config: Config) -> dict:
    if target in entries:
        return entries[target]
    try:  # a local path, possibly absolute or ./-relative
        rel = Path(target).resolve().relative_to(config.root.resolve()).as_posix()
        if rel in entries:
            return entries[rel]
    except ValueError:
        pass
    matches = [e for s, e in entries.items() if s.endswith(target)]
    if len(matches) == 1:
        return matches[0]
    hint = "run `fux ingest --list-inferred` to see upgrade candidates"
    if matches:
        raise FuxError(f"{target!r} is ambiguous ({len(matches)} manifest matches) — {hint}")
    raise FuxError(f"{target!r} is not in the manifest — ingest it first, then {hint}")


def _source_bytes(config: Config, entry: dict) -> Path:
    """Path to the original bytes — the local file, or a re-fetch for web entries."""
    if entry.get("origin") in ("url", "attachment"):
        from .web import Fetcher, WebSkip

        try:
            _, data, _ = Fetcher(config.web).fetch(entry["url"])
        except WebSkip as exc:
            raise FuxError(f"cannot re-fetch {entry['url']} for the upgrade: {exc}") from exc
        suffix = Path(entry["cache"]).stem and Path(entry["url"]).suffix or ""
        tmp = tempfile.NamedTemporaryFile(suffix=suffix or ".bin", delete=False)
        tmp.write(data)
        tmp.close()
        return Path(tmp.name)
    path = config.root / entry["source"]
    if not path.is_file():
        raise FuxError(f"source file {entry['source']} no longer exists")
    return path


def _docling_convert(path: Path) -> str:
    try:
        from docling.document_converter import DocumentConverter  # optional extra
    except ImportError as exc:
        raise FuxError(
            "the advanced office/PDF converter needs Docling — pip install docling"
        ) from exc
    try:
        result = DocumentConverter().convert(str(path))
        return result.document.export_to_markdown()
    except Exception as exc:
        raise FuxError(f"docling failed on {path.name}: {exc}") from exc


def _tesseract_convert(path: Path, entry: dict) -> str:
    if shutil.which("tesseract") is None:
        raise FuxError(
            "the advanced image converter needs the tesseract binary — "
            "brew install tesseract / apt install tesseract-ocr"
        )
    proc = subprocess.run(
        ["tesseract", str(path), "stdout"], capture_output=True, text=True, timeout=120
    )
    if proc.returncode != 0:
        raise FuxError(f"tesseract failed on {path.name}: {proc.stderr.strip()[:200]}")
    text = proc.stdout.strip()
    stub = f"Image file `{entry['source']}`."
    if not text:
        return f"{stub}\n\n*(OCR found no text)*"
    return f"{stub}\n\n## Extracted text (OCR)\n\n{text}"


def _minimal_meta(entry: dict) -> dict:
    return {
        "type": "Ingested Document",
        "title": entry.get("title", Path(entry["source"]).stem),
        "description": f"Ingested from {entry['source']} ({entry.get('kind', '')})",
        "timestamp": entry.get("converted_at", ""),
        "source": entry["source"],
        "source_sha256": entry.get("sha256", ""),
        "origin": entry.get("origin", "local"),
        "fidelity": "inferred",
        "converter": entry.get("converter", ""),
        "converted_at": entry.get("converted_at", ""),
        "fux_version": __version__,
    }
