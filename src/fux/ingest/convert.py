"""Per-type converters: source bytes → markdown body + provenance hints.

Everything here is stdlib. Office/PDF is the one opt-in exception: it runs only
when the `markitdown` extra is importable, and a missing extra is a *skip with a
reason*, never an error — the `$0` read path must not grow dependencies.
"""

from __future__ import annotations

import json
import struct
from dataclasses import dataclass, field

from ..frontmatter import parse as fm_parse
from .walk import SourceFile


@dataclass
class ConvertResult:
    body: str = ""
    source_meta: dict = field(default_factory=dict)  # md frontmatter, preserved
    line_offset: int | None = 0  # source_line = body_line + offset; None = synthetic
    converter: str = ""
    skipped: str | None = None  # reason, when the file can't be ingested
    truncated: bool = False
    warnings: list[str] = field(default_factory=list)


def convert(sf: SourceFile, data: bytes, max_kb: int) -> ConvertResult:
    if sf.kind in ("md", "txt", "code", "json", "yaml") and b"\0" in data[:8192]:
        return ConvertResult(skipped="binary content", converter="none")
    handler = {
        "md": _convert_md,
        "txt": _convert_txt,
        "code": _convert_code,
        "json": _convert_json,
        "yaml": _convert_yaml,
        "image": _convert_image,
        "office": _convert_office,
    }[sf.kind]
    result = handler(sf, data, max_kb)
    if result.body and not result.body.endswith("\n"):
        result.body += "\n"
    return result


def _decode(data: bytes) -> str:
    return data.decode("utf-8", errors="replace")


def _cap(text: str, max_kb: int) -> tuple[str, bool]:
    limit = max_kb * 1024
    if len(text.encode("utf-8")) <= limit:
        return text, False
    clipped = text.encode("utf-8")[:limit].decode("utf-8", errors="ignore")
    cut = clipped.rfind("\n")
    return (clipped[:cut] if cut > 0 else clipped), True


def _convert_md(sf: SourceFile, data: bytes, max_kb: int) -> ConvertResult:
    fm = fm_parse(_decode(data))
    body, truncated = _cap(fm.body, max_kb)
    warnings = [f"{sf.rel}: truncated at {max_kb} KB"] if truncated else []
    return ConvertResult(
        body=body,
        source_meta=fm.meta,
        line_offset=fm.body_start_line - 1,
        converter="native-md",
        truncated=truncated,
        warnings=warnings,
    )


def _convert_txt(sf: SourceFile, data: bytes, max_kb: int) -> ConvertResult:
    body, truncated = _cap(_decode(data), max_kb)
    warnings = [f"{sf.rel}: truncated at {max_kb} KB"] if truncated else []
    return ConvertResult(
        body=body, converter="native-txt", truncated=truncated, warnings=warnings
    )


def _convert_code(sf: SourceFile, data: bytes, max_kb: int) -> ConvertResult:
    text, truncated = _cap(_decode(data).rstrip("\n"), max_kb)
    body = f"```{sf.lang}\n{text}\n```"
    warnings = [f"{sf.rel}: truncated at {max_kb} KB"] if truncated else []
    # body line 2 is source line 1: the opening fence costs one line.
    return ConvertResult(
        body=body, line_offset=-1, converter="code-fence", truncated=truncated, warnings=warnings
    )


def _convert_json(sf: SourceFile, data: bytes, max_kb: int) -> ConvertResult:
    text = _decode(data)
    try:
        obj = json.loads(text)
    except ValueError as exc:
        raw, truncated = _cap(text, max_kb)
        return ConvertResult(
            body=f"```json\n{raw}\n```",
            line_offset=-1,
            converter="json-raw",
            truncated=truncated,
            warnings=[f"{sf.rel}: invalid JSON ({exc}); ingested as raw text"],
        )
    flat = [f"- `{path}`: {value!r}" for path, value in _flatten(obj)]
    raw, truncated = _cap(text.rstrip("\n"), max_kb)
    body = "## Keys\n\n" + "\n".join(flat) + f"\n\n## Raw\n\n```json\n{raw}\n```"
    return ConvertResult(
        body=body, line_offset=None, converter="json-flatten", truncated=truncated
    )


def _flatten(obj, prefix: str = ""):
    if isinstance(obj, dict):
        for key, value in obj.items():
            yield from _flatten(value, f"{prefix}.{key}" if prefix else str(key))
    elif isinstance(obj, list):
        for i, value in enumerate(obj):
            yield from _flatten(value, f"{prefix}[{i}]")
    else:
        yield prefix or "(root)", obj


def _convert_yaml(sf: SourceFile, data: bytes, max_kb: int) -> ConvertResult:
    # stdlib has no YAML parser; fence it as text (v1 decision, see handoff 0001).
    text, truncated = _cap(_decode(data).rstrip("\n"), max_kb)
    warnings = [f"{sf.rel}: truncated at {max_kb} KB"] if truncated else []
    return ConvertResult(
        body=f"```yaml\n{text}\n```",
        line_offset=-1,
        converter="yaml-fence",
        truncated=truncated,
        warnings=warnings,
    )


def _convert_image(sf: SourceFile, data: bytes, max_kb: int) -> ConvertResult:
    fmt, dims = _image_dims(data)
    lines = [
        f"Image file `{sf.rel}`.",
        "",
        f"- format: {fmt or 'unknown'}",
        f"- dimensions: {f'{dims[0]}×{dims[1]}' if dims else 'unknown'}",
        f"- size: {len(data)} bytes",
        "",
        "*(metadata stub — inferred tier; OCR/description is the advanced tier)*",
    ]
    return ConvertResult(body="\n".join(lines), line_offset=None, converter="image-stub")


def _image_dims(data: bytes) -> tuple[str | None, tuple[int, int] | None]:
    if data[:8] == b"\x89PNG\r\n\x1a\n" and len(data) >= 24:
        w, h = struct.unpack(">II", data[16:24])
        return "png", (w, h)
    if data[:6] in (b"GIF87a", b"GIF89a") and len(data) >= 10:
        w, h = struct.unpack("<HH", data[6:10])
        return "gif", (w, h)
    if data[:2] == b"\xff\xd8":
        return "jpeg", _jpeg_dims(data)
    return None, None


def _jpeg_dims(data: bytes) -> tuple[int, int] | None:
    i, n = 2, len(data)
    while i + 9 < n:
        if data[i] != 0xFF:
            i += 1
            continue
        marker = data[i + 1]
        if 0xC0 <= marker <= 0xCF and marker not in (0xC4, 0xC8, 0xCC):
            h, w = struct.unpack(">HH", data[i + 5 : i + 9])
            return (w, h)
        if marker in (0xD8, 0x01) or 0xD0 <= marker <= 0xD7:
            i += 2
            continue
        (seglen,) = struct.unpack(">H", data[i + 2 : i + 4])
        i += 2 + seglen
    return None


def _convert_office(sf: SourceFile, data: bytes, max_kb: int) -> ConvertResult:
    try:
        from markitdown import MarkItDown  # optional extra, never a runtime dep
    except ImportError:
        return ConvertResult(
            skipped="requires the markitdown extra (pip install 'fux-engine[ingest]')",
            converter="markitdown",
        )
    try:
        text = MarkItDown().convert(str(sf.abspath)).text_content
    except Exception as exc:  # converter bugs must not kill the ingest run
        return ConvertResult(skipped=f"markitdown failed: {exc}", converter="markitdown")
    body, truncated = _cap(text, max_kb)
    return ConvertResult(
        body=body, line_offset=None, converter="markitdown", truncated=truncated
    )
