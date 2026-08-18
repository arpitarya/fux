"""The canonical byte encoding — the one function every committed line goes
through. `work/compare/index-format.compare.md` §7 binding rules: sorted
keys, `(",",":")` separators, `ensure_ascii=False`, no floats, no nulls, NFC
text. Enforced here, not trusted of callers — a bug in `ingest/` should fail
loudly at the write boundary, not silently corrupt committed bytes.
"""

from __future__ import annotations

import json
import unicodedata

from ..errors import FuxError

# Legal JSON, hostile to every line-oriented tool downstream (git diff, the
# byte-prefilter scanner, M5's merge driver): str.splitlines()-class readers
# split on these even though `json.dumps(ensure_ascii=False)` writes them raw.
# Keep shard files strictly one-record-per-`\n` at the character level too.
_HOSTILE_LINE_BREAKS = (" ", " ", "")

_MAX_DEPTH = 64


def canonical_dumps(record: dict) -> bytes:
    """Encode one record as its canonical committed line (with trailing `\\n`)."""
    _validate(record, path="$", depth=0)
    text = json.dumps(record, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return (text + "\n").encode("utf-8")


def _validate(value, *, path: str, depth: int) -> None:
    if depth > _MAX_DEPTH:
        raise FuxError(f"canonicalization: nesting too deep at {path} (> {_MAX_DEPTH})")
    if isinstance(value, float):
        raise FuxError(f"canonicalization: float at {path} — no floats in committed bytes ({value!r})")
    if value is None:
        raise FuxError(f"canonicalization: null at {path} — no nulls in committed bytes")
    if isinstance(value, str):
        _validate_text(value, path=path)
        return
    if isinstance(value, dict):
        for key, sub in value.items():
            if not isinstance(key, str):
                raise FuxError(f"canonicalization: non-string key at {path} ({key!r})")
            _validate_text(key, path=f"{path}.<key>")
            _validate(sub, path=f"{path}.{key}", depth=depth + 1)
        return
    if isinstance(value, (list, tuple)):
        for i, sub in enumerate(value):
            _validate(sub, path=f"{path}[{i}]", depth=depth + 1)
        return
    if isinstance(value, (bool, int)):
        return
    raise FuxError(f"canonicalization: unsupported type at {path} ({type(value).__name__})")


def _validate_text(value: str, *, path: str) -> None:
    if value.isascii():  # ASCII is NFC by definition — skip the unicodedata call
        return
    if unicodedata.normalize("NFC", value) != value:
        raise FuxError(f"canonicalization: non-NFC text at {path} — normalize before writing ({value!r})")
    if any(ch in value for ch in _HOSTILE_LINE_BREAKS):
        raise FuxError(
            f"canonicalization: text at {path} contains a non-\\n line separator "
            "(U+2028/U+2029/U+0085) — hostile to line-oriented tooling"
        )
    try:
        value.encode("utf-8")
    except UnicodeEncodeError as exc:
        raise FuxError(f"canonicalization: text at {path} is not valid UTF-8 ({exc})") from exc
