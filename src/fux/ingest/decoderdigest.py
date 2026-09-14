"""What the reuse key knows about a decoder — the missing input to extraction.

Ingest reuses a document's extracted record when its source bytes are unchanged.
A decoder is the *other* input, and it was not in the key:
[SR-DECODE](../../../records/0139_decode.md) decision 11a read, in as many
words, *"There is no decoder digest. Stated, not fixed."* So a fix to `pdf.py`
reached an unchanged PDF only on `fux ingest --full`, and a corpus that never ran
one went on serving text the current code would not produce — while ingest
reported success and `fux doctor` stayed green.

## Why this lives in `ingest/` and not in `decode/`

**It is a reuse-key concern, and `decode/` is a read plane.** Putting it beside
`registry()` was the first shape, and `tests/test_node_twins.py` rejected it:
`node/src/decode/registry.mjs` is that module's twin, Node **reads** an index and
never builds one, so the change would have left the twin permanently "behind" for
a function Node must never grow. Porting it would have been dead code; narrowing
the twin check would have opened a hole over the decode path's real behaviour.

Reading `Decoder.origin` — which the registry already publishes — gets the same
answer from outside, and leaves the read plane alone.

## Two digest kinds, because the two sources afford different discipline

| decoder | digest | why |
|---|---|---|
| built-in | `pdf@3` — the module's `VERSION` | fux owns this tree, so it can require a hand bump and hold it with a test. A constant does not move on a comment or a docstring |
| `.fux/decoders/` | `logdoc@sha:1a2b…` — sha of the file | fux can require nothing of a consumer's file and hold nothing about it. A forgotten bump there would silently pin a whole format to stale extraction. The file is committed, so its sha is as stable as the rule it stands for |

⚠ **A consumer decoder therefore re-extracts on a whitespace edit.** That is the
cheap direction of being wrong, and it is chosen deliberately.

## Per EXTENSION, which is the whole design call

A single corpus-wide digest would re-extract every document on any decoder
change — the entire markdown corpus for a fix to the `.pptx` reader, and every
consumer's repo on every engine release. Keyed by extension, a bumped decoder
re-extracts its own documents and nothing else. That is the *"too coarse
re-ingests every corpus, too fine misses the case"* line W-166 was opened to
place.

**Markdown and plain text carry no entry**, because no decoder claims them —
they are read by `extract.py`, whose `RULES_VERSION` is the other half of W-166.

**Deterministic (L3):** both kinds are functions of source-tree bytes, never of
time, and the map is built in sorted order.
"""

from __future__ import annotations

import hashlib
import importlib
from pathlib import Path

#: `Decoder.origin` for a built-in, as `decode._load_builtin` spells it.
BUILTIN_PREFIX = "built-in:"


def _module_version(name: str) -> int:
    """`VERSION` from a built-in decoder module, or `0` when it declares none.

    **`0` rather than a raise**, because this runs inside every ingest: a
    decoder that has lost its constant should re-extract once and be caught by
    `tests/decode/test_decoder_versions.py`, not stop the run. The test is where
    the discipline is enforced; this is where it is read.
    """
    try:
        module = importlib.import_module(f".{name}", "fux.decode")
    except Exception:  # pragma: no cover - the registry already loaded it
        return 0
    version = getattr(module, "VERSION", 0)
    return version if isinstance(version, int) else 0


def of(decoder) -> str:
    """One decoder's digest, from its `origin`."""
    origin = getattr(decoder, "origin", "") or ""
    name = getattr(decoder, "name", "") or "?"
    if origin.startswith(BUILTIN_PREFIX):
        return f"{name}@{_module_version(origin[len(BUILTIN_PREFIX):])}"
    try:
        raw = Path(origin).read_bytes()
    except OSError:
        # Unreadable consumer file: a digest that cannot be computed must not
        # read as "unchanged", or the reuse key would carry stale extraction
        # forward on exactly the run that could not check it.
        return f"{name}@sha:unreadable"
    return f"{name}@sha:{hashlib.sha256(raw).hexdigest()[:16]}"


def binding_digests(root: Path | None = None) -> dict[str, str]:
    """`{extension: digest}` for every bound decoder — the reuse key's input."""
    from .. import decode as decode_mod

    return {ext: of(decoder) for ext, decoder in sorted(decode_mod.registry(root).items())}
