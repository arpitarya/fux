"""Unit suite for the per-type converters."""

from __future__ import annotations

import struct
import zlib
from pathlib import Path

from fux.ingest.convert import convert
from fux.ingest.walk import SourceFile


def sf(rel: str, kind: str, lang: str = "", tmp: Path = Path(".")) -> SourceFile:
    return SourceFile(rel=rel, abspath=tmp / rel, stype="docs", kind=kind, lang=lang)


def tiny_png(width: int = 3, height: int = 2) -> bytes:
    def chunk(tag: bytes, payload: bytes) -> bytes:
        return (
            struct.pack(">I", len(payload))
            + tag
            + payload
            + struct.pack(">I", zlib.crc32(tag + payload))
        )

    ihdr = struct.pack(">IIBBBBB", width, height, 8, 0, 0, 0, 0)
    raw = b"".join(b"\x00" + b"\x80" * width for _ in range(height))
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", ihdr)
        + chunk(b"IDAT", zlib.compress(raw))
        + chunk(b"IEND", b"")
    )


def test_md_strips_frontmatter_and_offsets():
    data = b"---\ntitle: My Doc\nowner: someone\n---\n# Heading\n\nbody text\n"
    result = convert(sf("a.md", "md"), data, 256)
    assert result.body.startswith("# Heading")
    assert result.source_meta == {"title": "My Doc", "owner": "someone"}
    assert result.line_offset == 4  # body line 1 == source line 5
    assert result.converter == "native-md"


def test_md_without_frontmatter_offset_zero():
    result = convert(sf("a.md", "md"), b"plain body\n", 256)
    assert result.line_offset == 0 and result.body == "plain body\n"


def test_code_fenced_with_language():
    result = convert(sf("x.py", "code", lang="python"), b"print('hi')\n", 256)
    assert result.body == "```python\nprint('hi')\n```\n"
    assert result.line_offset == -1  # body line 2 == source line 1


def test_json_flattened_and_raw():
    data = b'{"a": {"b": 1}, "c": [true, "x"]}'
    result = convert(sf("d.json", "json"), data, 256)
    assert "- `a.b`: 1" in result.body
    assert "- `c[0]`: True" in result.body
    assert "```json" in result.body
    assert result.line_offset is None
    assert result.converter == "json-flatten"


def test_invalid_json_falls_back_to_raw():
    result = convert(sf("d.json", "json"), b"{nope", 256)
    assert result.converter == "json-raw"
    assert result.warnings and "invalid JSON" in result.warnings[0]


def test_yaml_fenced_as_text():
    result = convert(sf("s.yaml", "yaml"), b"key: value\n", 256)
    assert result.body == "```yaml\nkey: value\n```\n"
    assert result.converter == "yaml-fence"


def test_binary_masquerading_as_md_skipped():
    result = convert(sf("evil.md", "md"), b"\x00\x01\x02binary", 256)
    assert result.skipped == "binary content"


def test_huge_file_truncated_with_warning():
    data = ("line of text\n" * 2000).encode()  # ~26 KB
    result = convert(sf("big.txt", "txt"), data, 4)
    assert result.truncated is True
    assert len(result.body.encode()) <= 4 * 1024 + 1
    assert any("truncated" in w for w in result.warnings)


def test_png_dimensions_parsed():
    result = convert(sf("logo.png", "image"), tiny_png(3, 2), 256)
    assert "format: png" in result.body
    assert "dimensions: 3×2" in result.body
    assert result.converter == "image-stub"


def test_gif_dimensions_parsed():
    data = b"GIF89a" + struct.pack("<HH", 7, 9) + b"\x00" * 10
    result = convert(sf("x.gif", "image"), data, 256)
    assert "dimensions: 7×9" in result.body


def test_jpeg_dimensions_parsed():
    # minimal SOI + SOF0 segment
    sof = b"\xff\xc0" + struct.pack(">HBHH", 11, 8, 20, 30) + b"\x03"
    data = b"\xff\xd8" + sof + b"\xff\xd9"
    result = convert(sf("x.jpg", "image"), data, 256)
    assert "dimensions: 30×20" in result.body


def test_unknown_image_format_graceful():
    result = convert(sf("x.png", "image"), b"not an image", 256)
    assert "format: unknown" in result.body


def test_office_without_extra_is_skipped_with_reason(monkeypatch):
    import builtins

    real_import = builtins.__import__

    def no_markitdown(name, *a, **k):
        if name == "markitdown":
            raise ImportError("nope")
        return real_import(name, *a, **k)

    monkeypatch.setattr(builtins, "__import__", no_markitdown)
    result = convert(sf("r.pdf", "office"), b"%PDF-1.4", 256)
    assert result.skipped is not None and "markitdown" in result.skipped


def test_unicode_content_survives():
    result = convert(sf("u.md", "md"), "# Café\n\nnaïve — ✓\n".encode(), 256)
    assert "Café" in result.body and "naïve — ✓" in result.body
