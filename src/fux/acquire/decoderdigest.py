"""What the reuse key knows about a decoder — the missing input to extraction.

Ingest reuses a document's extracted record when its source bytes are unchanged.
A decoder is the *other* input, and it was not in the key:
[SR-DECODE](../../../records/0139_decode.md) decision 11a read, in as many
words, *"There is no decoder digest. Stated, not fixed."* So a fix to `pdf.py`
reached an unchanged PDF only on `fux ingest --full`, and a corpus that never ran
one went on serving text the current code would not produce — while ingest
reported success and `fux doctor` stayed green.

## Why this lives in `acquire/` and not in `decode/`

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
| packaged | `pkg:fux-decoder-pdf@4.2.0/pdf@3` — the declared distribution, its version, and the module's `VERSION`; **its reuse key is `pdf@3`** | fux owns these packages, so it can require a hand bump and hold it with a test; the distribution and its version name exactly which code read the document (SR-PLUGINS P12, W-289). Until W-289 phase 2 this row was a *built-in*, `pdf@3`, shipped inside fux-core |
| `.fux/decoders/` | `logdoc@sha:1a2b…` — sha of the file | fux can require nothing of a consumer's file and hold nothing about it. A forgotten bump there would silently pin a whole format to stale extraction. The file is committed, so its sha is as stable as the rule it stands for |

⚠ **A consumer decoder therefore re-extracts on a whitespace edit.** That is the
cheap direction of being wrong, and it is chosen deliberately.

## The package version names; it does not key (W-289 ruling 1)

**The `pkg:<dist>@<version>/` head is REGISTER's, never the reuse key's**
(Arpit, 2026-10-20). Every release moves every package's version in lockstep
(SR-PLUGINS P11), so a key that carried it would re-extract every decoded
document on every release while no decoder's output moved. `reuse_key()` strips
the head, leaving `<module>@<VERSION>+<ext tail>`; a decoder's own `VERSION` is
what moves when its output moves, and the test that holds a hand bump holds it.
`of()` still mints the full string, so a committed REGISTER row names the exact
distribution that produced it.

## Decoder extensions ride in the key (W-288)

Either kind is then followed by `+<ext>@<VERSION>` for every decoder extension
its `USES` names, in declared order: `docx@2+table@1+ooxml@1+xml@1+zip@1+limits@1`,
`docx@sha:1a2b…+table@1+…`. [SR-DECODE](../../../records/0139_decode.md)
decision 24. Before it, a fix to a shared helper moved no decoder's `VERSION`
and no consumer copy's bytes, so an existing corpus kept the old output until
`--full` — decision 11a's trap, one layer down. **A consumer copy needs this as
much as a packaged decoder does:** the seeded copies in `.fux/decoders/` import
`fux.decode.ext` from the installed engine, so an engine upgrade changes their
output while their sha stands still.

## Per EXTENSION, which is the whole design call

A single corpus-wide digest would re-extract every document on any decoder
change — the entire markdown corpus for a fix to the `.pptx` reader, and every
consumer's repo on every engine release. Keyed by extension, a bumped decoder
re-extracts its own documents and nothing else. That is the *"too coarse
re-ingests every corpus, too fine misses the case"* line W-166 was opened to
place.

**Markdown and plain text carry no entry**, because no decoder claims them —
they are read by `extract.py`, whose `RULES_VERSION` is the other half of W-166.

**Deterministic (L4):** both kinds are functions of source-tree bytes, never of
time, and the map is built in sorted order.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from ..constants import fixed

#: `Decoder.origin` for a decoder from a declared plugin package (P12).
PACKAGE_PREFIX = fixed("decoders", "package_prefix")


def _extension_version(name: str) -> int:
    """`VERSION` of decoder extension `name`, or `0` — `_module_version`'s rule."""
    try:
        from ..decode import ext as ext_mod

        version = ext_mod.version(name)
    except Exception:  # pragma: no cover - `_uses_of` already refused unknown names
        return 0
    return version if isinstance(version, int) else 0


def _packaged_version(origin: str, name: str) -> int:
    """`VERSION` of a packaged decoder module, from `pkg:<dist>@<v>/<module>`.

    Read from `sys.modules`, where the registry's verified load put it — this
    never imports a package the registry did not (SR-PLUGINS P3).
    """
    import sys

    from .. import plugins

    dist = origin[len(PACKAGE_PREFIX):].partition("@")[0]
    try:
        module = sys.modules.get(f"{plugins.package_named(dist).module}.{name}")
    except Exception:  # pragma: no cover - the registry already validated the name
        return 0
    version = getattr(module, "VERSION", 0)
    return version if isinstance(version, int) else 0


def name_of(digest: str) -> str:
    """The decoder module a digest names: `pdf` from `pdf@3`, from `pdf@sha:…`
    and from `pkg:fux-decoder-pdf@4.2.0/pdf@3+limits@1`."""
    if digest.startswith(PACKAGE_PREFIX):
        _package, _slash, digest = digest.partition("/")
    return digest.partition("@")[0]


def package_of(digest: str) -> "str | None":
    """`<dist>@<version>` from a packaged decoder's digest, else `None`."""
    if not digest.startswith(PACKAGE_PREFIX):
        return None
    return digest[len(PACKAGE_PREFIX):].partition("/")[0]


def of(decoder) -> str:
    """One decoder's digest, from its `origin` and its `uses`.

    A packaged decoder reads `pkg:<dist>@<version>/<module>@<VERSION>+<ext>@<v>…`
    (SR-PLUGINS P12): the distribution that read the document, the module, and
    the W-288 extension tail. This is the REGISTER string; the reuse key is
    `reuse_key()` of it, which drops the package head (W-289 ruling 1).
    """
    origin = getattr(decoder, "origin", "") or ""
    name = getattr(decoder, "name", "") or "?"
    tail = "".join(f"+{ext}@{_extension_version(ext)}" for ext in getattr(decoder, "uses", ()))
    if origin.startswith(PACKAGE_PREFIX):
        return f"{origin}@{_packaged_version(origin, name)}{tail}"
    try:
        raw = Path(origin).read_bytes()
    except OSError:
        # Unreadable consumer file: a digest that cannot be computed must not
        # read as "unchanged", or the reuse key would carry stale extraction
        # forward on exactly the run that could not check it.
        return f"{name}@sha:unreadable{tail}"
    return f"{name}@sha:{hashlib.sha256(raw).hexdigest()[: fixed('decoders', 'digest_hex')]}{tail}"


def reuse_key(digest: str) -> str:
    """What the reuse key compares: `digest` without a `pkg:<dist>@<version>/` head.

    `pkg:fux-decoder-pdf@4.2.0/pdf@3+limits@1` -> `pdf@3+limits@1`; any other
    digest is its own key. A lockstep release bump therefore re-extracts nothing
    (W-289 ruling 1); a moved module `VERSION` or extension tail still does.
    """
    if digest.startswith(PACKAGE_PREFIX):
        _package, _slash, digest = digest.partition("/")
    return digest


def reuse_keys(digests: dict[str, str]) -> dict[str, str]:
    """`reuse_key` over a `{extension: digest}` map, keys unchanged."""
    return {ext: reuse_key(digest) for ext, digest in digests.items()}


def binding_digests(root: Path | None = None) -> dict[str, str]:
    """`{extension: digest}` for every bound decoder — the reuse key's input."""
    from .. import decode as decode_mod

    return {ext: of(decoder) for ext, decoder in sorted(decode_mod.registry(root).items())}
