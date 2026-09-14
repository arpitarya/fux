"""`fux add` / `fux remove` / `fux update` — the corpus, as a first-class verb.

The three committed source lists (`.fux/sources/dirs`, `.fux/sources/urls` and
`.fux/formats.toml`) are what fux indexes. Until W-63 only one of them had a command — `fux url` — so
the corpus, the thing the whole engine is about, was the part of fux you
maintained by hand.

## One sentence keeps three verbs from overlapping

**`add` and `remove` write lines; `update` never touches one.**

Everything else follows. Attribute edits belong to `add`, which is already an
upsert. Re-reading a source belongs to `update`, which is why it can take an
entry without that meaning "create it". And `fux update` subsumes
`fux ingest --refresh-urls`, which leaves the engine with exactly **two**
named networked paths instead of three: `fux add <URL>` and `fux update`.

## `add` does the work, and that is a decision

`fux add docs/` records **and ingests**. `fux add <URL>` records **and fetches
that one URL** — scoped to the URL just added, announced on stderr, and
`--no-fetch` opts out. Recording a URL without fetching it is a no-op, so any
other default would mean "ingest by default" silently did not apply to the
one entry kind where it costs something.

The precedent surveyed: `uv add` locks and syncs by default, `helm repo add`
records *and* fetches. The rejected pole is `cargo add` and `git remote add`,
which record and never build — right for a manifest nobody reads until the
next command, wrong for an index whose entire value is being current.

## What this module does not do

It does not render errors — `cli.main` is the only boundary (SR-CLI
decision 3), so everything here raises. It does not open a socket: the fetch
`add` performs is `ingest.run`'s, behind the same consumer-fetcher contract
every other fetch uses. And it never writes the index itself — `add`,
`remove` and `update` all end in **one** `ingest.run`, because a second write
path is how L3's byte-identical guarantee breaks.

## It edits one line, never the file

A regenerating writer would be simpler and would silently eat the grouping
comments a human left behind — and under
[SR-URL-LIST](../../records/0116_url-list.md) decision 3 those comments are
the reason the file is maintainable at all. So an add inserts one line at its
sorted position, an update rewrites that one line and keeps its trailing
comment, and a removal deletes it. Every other byte is untouched. The loader
sorts regardless (decision 4), so the insertion position is a courtesy to the
reader, not a correctness property.

A fux-written line carries **every** attribute, explicitly, even where the
value equals the default (decision 12): a generated file holds no implicit
state, so changing a policy is a one-word diff rather than the appearance or
disappearance of a key.

## `types` is TOML, and its editor is `typesfile`

Since 2026-09-11 the types list is `.fux/formats.toml` (SR-TYPES decision 12),
so every verb here branches on `sourcelist.TYPES` and hands the edit to
[`ingest/typesfile.py`](ingest/typesfile.py). **The rule above still holds** —
one line of the file changes, every other byte is kept — and the editor
**refuses** a layout it did not write rather than reformatting it. A bare
`*.ext` a decoder reads becomes a `[decoders]` line; anything else is an
`include` glob. There is no exclusion: `fux remove --types` deletes a line or
says the pattern is not there, and `.fux/.fuxignore` is where a file is kept out.
"""

from __future__ import annotations

import json as json_mod
import re
from pathlib import Path

from .config import (
    CONFIG_NAME,
    DEFAULT_TYPES_FILE,
    find_root,
    load,
)
from .errors import FuxError
from .ingest import fuxignore, sourcelist, typesfile

# -- which list, and where it lives ----------------------------------------


def dispatch(entry: str, args=None) -> sourcelist.ListSpec:
    """Which list an entry belongs to. **The entry decides; a flag disambiguates.**

    `http(s)://…` is a URL and nothing else is, so URLs need no flag. `dirs`
    is the fallback rather than `types` because it is the common case *and*
    because it already accepts both a directory and a single file — a type
    pattern (`*.pdf`) is the rare, deliberate act, so it is the one that has
    to say `--types`.

    There is no sniffing of `*` to mean "a type pattern": `docs/*` is a
    perfectly reasonable thing to want in `dirs`, and guessing between the two
    on a glob character would be wrong exactly when it mattered.

    **Anything with a `scheme://` is a URL, not just `http`.** Dispatching on
    `http(s)://` alone sent `ftp://x/a` to `dirs`, where it was refused for
    being missing from disk — an answer about the wrong thing entirely.
    Someone who typed a scheme meant a URL, so it goes to the list that has
    an opinion about URLs and gets told the real reason: that one takes
    `http(s)` only.
    """
    if getattr(args, "types", False):
        return sourcelist.TYPES
    if _SCHEME_RE.match(entry):
        return sourcelist.URLS
    return sourcelist.DIRS


#: `scheme://` — RFC 3986 §3.1's scheme grammar, anchored, with the `//` that
#: distinguishes a URL from a Windows drive letter or a `key: value` note.
_SCHEME_RE = re.compile(r"[a-zA-Z][a-zA-Z0-9+.\-]*://")


def normalize_entry(entry: str, spec: sourcelist.ListSpec) -> str:
    """The entry as it should be written. **`docs/` and `docs` are one entry.**

    Found by using it: `fux add docs/` on a list already holding `docs` wrote
    a *second* line for the same directory. The parser dedupes on the exact
    string, so it cannot see that duplicate — which makes the list say two
    things where the corpus has one, and makes `fux remove docs` and
    `fux remove docs/` disagree about whether a line exists.

    Only `dirs` needs it: a URL's trailing slash is significant (`/a/` and
    `/a` can be different pages, and only the server knows), and `types`
    rejects a trailing slash outright.
    """
    if spec is sourcelist.DIRS and entry != "/":
        stripped = entry.rstrip("/")
        return stripped or entry
    return entry


def list_path(root: Path, spec: sourcelist.ListSpec) -> Path:
    """Where a list lives — the configured path, or the default.

    A repo with no `[sources.url]` block still has a URL list path: the
    command that puts the first URL in it should not also demand you configure
    the source first.
    """
    if spec is sourcelist.URLS:
        config = load(root)
        return root / config.urls_file
    if spec is sourcelist.DIRS:
        return root / load(root).dirs_file
    return root / DEFAULT_TYPES_FILE


def _read(path: Path, spec: sourcelist.ListSpec) -> list[sourcelist.Entry]:
    """Parse a list, treating a missing file as an empty one.

    Missing is legal *here* and nowhere else: `add` exists to create the first
    line, so demanding the file already exist would make the command useless
    at the only moment it is unambiguous. Ingest still fails loudly on a
    missing list, which is the read path where absence is a real problem.
    """
    if spec is sourcelist.TYPES:
        return _type_entries(path)
    if not path.is_file():
        return []
    return sourcelist.parse(path.read_text(encoding="utf-8"), spec, origin=str(path))


def _types_root(path: Path) -> Path:
    """The repo root a `.fux/formats.toml` path sits in."""
    return path.parents[len(Path(DEFAULT_TYPES_FILE).parts) - 1]


def _type_entries(path: Path) -> list[sourcelist.Entry]:
    """`.fux/formats.toml` as the entries every verb here already speaks.

    **An `include` glob and a `[decoders]` binding are both a pattern** to a
    verb: `*.md` with no decoder, `*.csv` with `decoder=csv`. Each is complete by
    construction — the TOML has nothing implicit to be missing — so `fux add`'s
    listing never marks one as a line fux did not write.

    A leftover `.fux/sources/types` is refused here too, so no verb can write
    the new file while the old one still sits beside it.
    """
    typesfile.check_legacy(_types_root(path))
    if not path.is_file():
        return []
    listed = typesfile.parse(path.read_text(encoding="utf-8"), origin=str(path))
    full = frozenset({"decoder"})
    entries = [
        sourcelist.Entry(value=glob, attrs={"decoder": ""}, lineno=0, declared=full)
        for glob in listed.include
    ]
    entries += [
        sourcelist.Entry(value=f"*.{ext}", attrs={"decoder": name}, lineno=0, declared=full)
        for ext, name in listed.decoders.items()
    ]
    return sorted(entries, key=lambda e: e.value)


def _add_type(path: Path, value: str, overrides: dict[str, str]) -> tuple[str, str, str]:
    """`add` for `.fux/formats.toml`: a binding if a decoder reads it, an `include` glob if not.

    **A bare `*.ext` already in `include` moves** when it gains a decoder — the
    file may not state one extension twice (SR-TYPES decision 12), and fux's
    own edit is the last thing that should trip that error.
    """
    text = path.read_text(encoding="utf-8") if path.is_file() else ""
    origin = str(path)
    listed = typesfile.parse(text, origin=origin)
    ext = typesfile.pattern_extension(value)
    name = overrides.get("decoder")
    if name is None:
        name = listed.decoders.get(ext, "") if ext else ""
    if name:
        if ext is None:
            raise FuxError(
                f"decoder={name} on {value!r}: a binding is per extension - dispatch sees a "
                f"suffix and nothing about which glob admitted the file - so it only goes on a "
                f"bare `*.ext` pattern. Nothing was written"
            )
        new, action, previous = typesfile.set_decoder(text, ext, name, origin=origin)
        line = sourcelist.render_line(f"*.{ext}", {"decoder": name}, sourcelist.TYPES)
        if previous:
            before = sourcelist.render_line(f"*.{ext}", {"decoder": previous}, sourcelist.TYPES)
        elif value in listed.include:
            action, before = "updated", value
        else:
            before = ""
    else:
        new, action = typesfile.add_include(text, value, origin=origin)
        line, before = value, ""
    if new != text:
        path.write_text(new, encoding="utf-8", newline="\n")
    return action, line, before


# -- writing one line ------------------------------------------------------


def _write(path: Path, lines: list[str]) -> None:
    """Write the lines back, always ending in exactly one newline.

    A committed text file without a trailing newline makes the next diff touch
    a line nobody edited, which is the opposite of what a one-line writer is
    for.
    """
    text = "\n".join(lines).rstrip("\n")
    # `newline="\n"` disables the platform-default translation write_text()
    # otherwise applies — without it this would commit CRLF on Windows and LF
    # everywhere else, breaking L3's byte-identical guarantee across machines.
    path.write_text(text + "\n" if text else "", encoding="utf-8", newline="\n")


def _split(raw: str) -> tuple[str, str]:
    """One raw line -> (its entry text, its trailing comment including the `#`)."""
    body = sourcelist.strip_comment(raw)
    return body, raw[len(body) :]


def _entry_value(raw: str) -> str | None:
    """The entry a raw line declares, or None for a blank or comment line.

    Includes any leading `!`, so an exclusion and its include are distinct
    keys here exactly as they are in the parser.
    """
    body, _ = _split(raw)
    stripped = body.strip()
    return stripped.split()[0] if stripped else None


def _insert_at(lines: list[str], value: str) -> int:
    """The index where `value` belongs, keeping the entry block sorted."""
    for i, raw in enumerate(lines):
        existing = _entry_value(raw)
        if existing is not None and existing > value:
            return i
    # No later entry: land after the last one rather than after the file's
    # trailing blank lines, so a generated list stays a single block.
    last = max((i for i, raw in enumerate(lines) if _entry_value(raw) is not None), default=None)
    return last + 1 if last is not None else _after_preamble(lines)


def _after_preamble(lines: list[str]) -> int:
    """The first index past the file's leading comment block, blanks trimmed."""
    i = 0
    while i < len(lines) and (not lines[i].strip() or lines[i].lstrip().startswith("#")):
        i += 1
    return i


def _source_defaults(root: Path, spec: sourcelist.ListSpec) -> dict[str, str]:
    """`[sources.url]`'s policy, in the line grammar's own words.

    Only the keys that are also line attributes, and only for the URL list —
    `dirs` has no source-wide table to read. A repo with no `[sources.url]`
    (or an unreadable `fux.toml`) resolves to nothing, so the engine defaults
    stand exactly as before.
    """
    if spec is not sourcelist.URLS:
        return {}
    try:
        url = load(root).url
    except FuxError:
        return {}
    if url is None:
        return {}
    # `fetcher` is a PATH and `fetch=` is a stem: `.fux/fetchers/cdp.py` -> `cdp`
    # (SR-FETCHER decision 5, one key carrying both).
    return {
        "fetch": Path(url.fetcher).stem,
        "meta": url.meta,
        "keep": "true" if url.keep else "false",
        "ttl": url.ttl,
        "enrich": "true" if url.enrich else "false",
        "update": url.update,
    }


def add(
    path: Path,
    value: str,
    overrides: dict[str, str],
    spec: sourcelist.ListSpec,
    source_defaults: dict[str, str] | None = None,
) -> tuple[str, str, str]:
    """Add or update one line. Returns `(action, new_line, previous_line)`.

    `source_defaults` is the **source-wide policy** — `[sources.url]`'s
    `fetcher`, `meta`, `keep`, `ttl`, `enrich` and `update` — resolved by the
    caller.

    ⚠ **Without it, `fux add` overrode the consumer's own configuration**
    (W-140 row 5, fixed 2026-09-11). Every generated line states every
    attribute ([SR-URL-LIST](../../records/0116_url-list.md) decision 12),
    and the values stated came from `spec.defaults()` — **the ENGINE's
    built-ins**. So a team with `[sources.url] ttl = "7d"` got `ttl=24h`
    written onto every line `fux add` produced, and the middle layer of a
    three-layer resolution was dead for every CLI-written line: the layer
    exists precisely so a whole intranet can be configured in one place.

    **Stating the resolved value keeps decision 12 whole** — the line still
    holds no implicit state and a change is still a one-word diff — while the
    word it states is the consumer's policy rather than a default they had
    already overridden.
    """
    if spec is sourcelist.TYPES:
        return _add_type(path, value, overrides)
    text = path.read_text(encoding="utf-8") if path.is_file() else ""
    lines = text.split("\n")

    existing = sourcelist.parse(text, spec, origin=str(path))
    prior = next((e for e in existing if e.value == value and not e.exclude), None)
    attrs = (
        spec.defaults()
        | {k: v for k, v in (source_defaults or {}).items() if k in spec.defaults()}
        | (prior.attrs if prior is not None else {})
        | overrides
    )
    body = sourcelist.render_line(value, attrs, spec)

    for i, raw in enumerate(lines):
        if _entry_value(raw) != value:
            continue
        _, comment = _split(raw)
        previous = raw
        lines[i] = body + (f"  {comment.strip()}" if comment.strip() else "")
        _write(path, lines)
        return ("unchanged" if lines[i] == previous else "updated"), lines[i], previous

    lines.insert(_insert_at(lines, value), body)
    _write(path, lines)
    return "added", body, ""


def remove(path: Path, value: str) -> str:
    """Delete the line declaring `value`. Returns it, or raises if it is not there."""
    if not path.is_file():
        raise FuxError(f"{path} does not exist — nothing to remove")
    lines = path.read_text(encoding="utf-8").split("\n")
    for i, raw in enumerate(lines):
        if _entry_value(raw) == value:
            removed = lines.pop(i)
            _write(path, lines)
            return removed
    raise FuxError(f"{value} is not in {path}")


# -- remove-by-coverage ----------------------------------------------------


def _normalized(entry: str) -> str:
    """A `dirs` entry as a path for coverage comparison — no trailing slash.

    `docs` and `docs/` are the same directory, and a rule that said otherwise
    would make `fux remove docs/onboarding.md` behave differently depending on
    how somebody typed an unrelated line months ago.
    """
    return entry.rstrip("/")


def _covering_ancestor(value: str, entries: list[sourcelist.Entry]) -> str | None:
    """The listed entry that pulls `value` into the walk, if any.

    Includes are literal paths, not globs — `walk_sources` recurses into
    `root / entry` — so coverage is a path-prefix question and not a match
    question. Exclusions are the ones that glob.
    """
    target = _normalized(value)
    for entry in entries:
        if entry.exclude:
            continue
        base = _normalized(entry.value)
        if target == base or target.startswith(base + "/"):
            return entry.value
    return None


def remove_or_exclude(
    root: Path, path: Path, spec: sourcelist.ListSpec, value: str
) -> tuple[str, str, str]:
    """Take `value` out of the corpus. Returns `(action, line, detail)`.

    **Two ways in, so two ways out** (W-63 decision 4). A path with its own
    line leaves by deleting that line. A path with no line of its own is in
    the corpus because an ancestor is listed — so it leaves by an exclusion,
    which is the subtraction the grammar already has.

    The alternative was deleting the ancestor's line and re-adding its
    siblings, which is a many-line diff for a one-document change, and which
    silently changes what happens when a new sibling appears.

    The verb says which branch it took, because "removed" and "excluded" are
    different facts about the file and a reader of the diff needs to know
    which one they are looking at.

    ⚠ **The exclusion is written into `.fux/.fuxignore`, not as a `!` line
    here** (W-165 fix 1). `!` in `dirs` keeps being *read* — SR-DIR-LIST
    decision 2a, and every line anyone already wrote goes on working — but
    `.fuxignore` is where exclusion lives (SR-FUXIGNORE), and a verb that kept
    writing into the older of two spellings was the migration that record
    called *"a migration we now owe"*. `fux doctor` names the survivors.
    """
    if spec is sourcelist.TYPES:
        typesfile.check_legacy(_types_root(path))
        if not path.is_file():
            raise FuxError(f"{path} does not exist — nothing to remove")
        text = path.read_text(encoding="utf-8")
        new, removed = typesfile.remove(text, value, origin=str(path))
        path.write_text(new, encoding="utf-8", newline="\n")
        return "removed", removed, ""

    entries = _read(path, spec)

    if any(e.value == value and not e.exclude for e in entries):
        return "removed", remove(path, value).strip(), ""

    if not spec.allow_exclusions:
        raise FuxError(
            f"{value} is not in {path}. `{spec.kind}` has no exclusions — every entry is a line, "
            "so there is nothing to subtract from and nothing to remove but a line that exists"
        )

    if any(e.value == value and e.exclude for e in entries):
        # **The `!` line is left exactly as it is.** It already excludes, so
        # there is nothing to do; rewriting it into `.fuxignore` here would be
        # a migration performed as a side effect of a verb that was asked to
        # remove something already removed. `doctor` is where the move is
        # offered, at a moment the reader chose (W-165 fix 1).
        raise FuxError(
            f"{value} is already excluded by a `!` line in {path}, which is left alone. "
            "`!` subtracts there and nothing adds back, so there is nothing further to "
            f"remove — delete that line to put it back. Exclusions are written to "
            f"{fuxignore.IGNORE_FILE} now; `fux doctor` names the `!` lines still here"
        )

    ancestor = _covering_ancestor(value, entries)
    if ancestor is None:
        raise FuxError(
            f"{value} is not in {path}: it has no line of its own, and no listed entry covers it. "
            f"Both were checked. `fux add {value}` would list it; nothing needs removing"
        )

    line = fuxignore.add_exclusion(root, value, is_dir=(root / value).is_dir())
    return "excluded", line, f"{ancestor} still listed; this path is subtracted from it"


# -- flags -> recorded attributes ------------------------------------------


def _overrides(args, spec: sourcelist.ListSpec) -> dict[str, str]:
    """Flags -> the attributes to record. Two flags for one attribute is an error.

    `--cdp --http` has no defensible meaning, and picking one silently is how a
    scripted call records the opposite of what it meant.

    A flag that names an attribute this list does not have is also an error
    rather than a silent no-op — `fux add docs/ --cdp` is someone believing
    something about the entry they just wrote, and the closed attribute set
    (SR-URL-LIST decision 11) is only worth having if it is enforced on the
    way in as well as on the way out.
    """
    pairs = (
        ("fetch", ("cdp", "http")),
        ("meta", ("plain", "hashed")),
        ("archived", ("archived",)),
        ("keep", ("keep", "no_keep")),
        ("update", ("no_update",)),
    )
    #: Flags that NAME a boolean attribute rather than carrying its value.
    #: `--cdp` records `fetch=cdp` -- the flag is the value. `--no-keep`
    #: records `keep=false`, where it is not.
    #:
    #: ⚠ **`--no-update` records `update=never`, not `update=false`.** The
    #: attribute is two WORDS (`auto`/`never`), deliberately, so it can never be
    #: mistaken for the duration-valued `ttl=` sitting beside it.
    boolean = {
        "archived": {"archived": "true"},
        "keep": {"keep": "true", "no_keep": "false"},
        "update": {"no_update": "never"},
    }
    overrides: dict[str, str] = {}
    for attribute, flags in pairs:
        given = [flag for flag in flags if getattr(args, flag, False)]
        if len(given) > 1:
            raise FuxError(f"--{given[0]} and --{given[1]} both set `{attribute}` — pick one")
        if not given:
            continue
        if spec.attribute(attribute) is None:
            raise FuxError(
                f"--{given[0]} sets `{attribute}`, which `{spec.kind}` does not have. "
                f"Its attribute set is closed and is "
                f"{', '.join(spec.names) if spec.names else 'empty'}"
            )
        overrides[attribute] = boolean.get(attribute, {}).get(given[0], given[0])
    ttl = getattr(args, "ttl", None)
    if ttl is not None:
        attribute = spec.attribute("ttl")
        if attribute is None:
            raise FuxError(
                f"--ttl sets `ttl`, which `{spec.kind}` does not have. Its attribute set "
                f"is closed and is {', '.join(spec.names) if spec.names else 'empty'}"
            )
        # Validated by the SAME rule the file grammar uses, so `--ttl 1x` and a
        # hand-written `ttl=1x` fail identically. Two validators would drift.
        fault = attribute.reject(ttl)
        if fault is not None:
            raise FuxError(f"--ttl {ttl!r} {fault}")
        overrides["ttl"] = ttl
    return overrides


def _drop_acquired(root: Path, spec: sourcelist.ListSpec, entry: str) -> None:
    """Forget the retained bytes for a URL that is no longer listed.

    SR-ACQUIRED decision 9 keeps sweeping and eviction apart, and this is
    neither: it is the removal that makes a blob unreferenced in the first
    place. The blob FILE is left for `fux update`'s sweep rather than unlinked
    here — content addressing means two URLs can share one blob, and deleting
    it because one of them went would silently break the other.

    ⚠ **Advisory to the last.** A failure here costs a stale manifest entry
    that the next sweep collects anyway; it must never turn `fux remove` into
    a command that half-worked.
    """
    if spec.kind != "urls":
        return
    try:
        from .store import acquired

        blobs = acquired.read_manifest(root)
        if entry not in blobs:
            return
        blobs.pop(entry)
        acquired.write_manifest(root, blobs)
        gone = acquired.sweep(root, blobs)
        if gone:
            print(f"  dropped {gone} retained blob(s) from .fux/acquired/")
    except Exception:
        pass


def _root() -> Path:
    root = find_root()
    if root is None:
        raise FuxError(f"no {CONFIG_NAME} or .git found — run from inside a configured repo")
    return root


# -- the verbs -------------------------------------------------------------


def _rel(root: Path, path: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:  # a configured list outside the repo root
        return str(path)


def _ingest(root: Path, args, *, refresh_urls: bool = False, only_urls=None, first_fetch=None):
    """Every verb's single way into the index (L3). Imported lazily (SR-CLI 7)."""
    from .ingest import ingest_and_report

    return ingest_and_report(
        root, args, refresh_urls=refresh_urls, only_urls=only_urls, first_fetch=first_fetch
    )


def _index_ids(root: Path) -> set[str]:
    from . import store as store_mod

    return set(store_mod.read_index(root))


def cmd_add(args) -> int:
    """Record an entry in the list its shape implies, then ingest it."""
    import sys

    root = _root()
    entry = getattr(args, "entry", None)
    if not entry:
        return _list_all(root)

    spec = dispatch(entry, args)
    entry = normalize_entry(entry, spec)
    path = list_path(root, spec)
    reason = spec.validate(entry)
    if reason is not None:
        raise FuxError(f"{reason}: {entry!r}")
    overrides = _overrides(args, spec)
    source_defaults = _source_defaults(root, spec)

    entries = _read(path, spec)
    if any(e.value == entry and e.exclude for e in entries):
        raise FuxError(
            f"{entry} is excluded in {_rel(root, path)}. There is no un-exclude by design — "
            f"`!` subtracts and nothing adds back, so delete the `!{entry}` line to index it again"
        )
    # **The same refusal for the file `remove` writes to now** (W-165 fix 1).
    # Without this, moving the write target would have quietly turned `add`
    # into the un-exclude the line above exists to refuse: `fux remove docs/a.md`
    # then `fux add docs/a.md` would have written a line that the `.fuxignore`
    # pattern goes on beating, so the command would report success and index
    # nothing. Refusing is the loud direction, and it names the file to edit.
    if spec is sourcelist.DIRS:
        verdict = fuxignore.read(root).decide(
            entry, is_dir=(root / entry).is_dir(), hand_only=True
        )
        if verdict.ignored and verdict.rule is not None:
            raise FuxError(
                f"{entry} is excluded by {fuxignore.IGNORE_FILE}:{verdict.rule.lineno} "
                f"(`{verdict.rule.raw}`), which is consulted first and would keep beating any "
                f"line written here. There is no un-exclude by design — delete that pattern, or "
                f"write `!{entry}` below it, to index it again"
            )
    # A line that breaks the next ingest is worse than a refused command:
    # `walk_sources` raises on a configured source that is not on disk, so a
    # typo'd `add` would otherwise take the whole corpus down until someone
    # hand-edited the file back.
    if spec is sourcelist.DIRS and not (root / entry).exists():
        raise FuxError(
            f"{entry} does not exist (looked in {root / entry}) — nothing would be indexed, and "
            "the next `fux ingest` would fail on it. Nothing was written"
        )

    # A new type pattern records the decoder that would read it ANYWAY, so the
    # written line preserves today's dispatch exactly rather than describing
    # it. Resolved from the LIVE registry, not the built-ins: if a consumer
    # module claims this extension, that module is what fux is about to use,
    # and writing the built-in's name instead would be a line that silently
    # changes behaviour the moment it lands.
    if spec is sourcelist.TYPES and "decoder" not in overrides:
        from .decode import registry as decoder_registry

        ext = _pattern_ext(entry)
        match = decoder_registry(root).get(ext) if ext else None
        if match is not None:
            overrides = overrides | {"decoder": match.name}

    if getattr(args, "dry_run", False):
        preview = sourcelist.render_line(entry, spec.defaults() | overrides, spec)
        print(f"would add {preview}")
        print(f"  in {_rel(root, path)}")
        print(f"  then: {_plan(spec, args)}")
        return 0

    path.parent.mkdir(parents=True, exist_ok=True)
    if spec is sourcelist.TYPES and not path.is_file():
        _seed_types(path)
    action, line, previous = add(path, entry, overrides, spec, source_defaults)
    print(f"{action:9s} {line.strip()}")
    if action == "updated":
        print(f"      was {previous.strip()}")
    print(f"  in {_rel(root, path)}")

    if action == "unchanged":
        # The list already said exactly this, so the index already reflects it.
        # Re-ingesting would be a no-op that looks like work.
        return 0
    if getattr(args, "no_ingest", False):
        return 0

    only_urls = None
    refresh = False
    if spec is sourcelist.URLS and not getattr(args, "no_fetch", False):
        if load(root).url is None:
            print(
                f"  no [sources.url] in {CONFIG_NAME}, so nothing can fetch this line yet — "
                "`fux setup` writes a fetcher; `fux update` fetches once one exists",
                file=sys.stderr,
            )
        else:
            refresh, only_urls = True, {entry}
            print(f"fetching  {entry} (network — this URL only)", file=sys.stderr)

    # ⚠ **The add's ONE fetch, and the only exemption a pin has.**
    # `--no-update` writes `update=never`, and until 2026-09-11 the ingest
    # filter dropped the line before the fetch — so the add wrote a line,
    # fetched nothing, and exited 1 saying the fetch failed, while `--help` and
    # [SR-URL-LIST](../records/0116_url-list.md) decision 14 both promised one
    # fetch (W-140 row 3). Every run after this one is pinned.
    report = _ingest(
        root, args, refresh_urls=refresh, only_urls=only_urls, first_fetch=only_urls
    )

    skipped = next((s for s in report.skipped if s.rel_path == entry), None)
    if skipped is None:
        return 0

    if refresh:
        # **The line stays written.** Recording and fetching are separate
        # outcomes, and deleting the line because the site was down would make
        # the committed corpus a function of network weather.
        print(f"  the line is written; the fetch failed: {skipped.reason}", file=sys.stderr)
        return 1

    # A skip that is not a fetch failure is a **fact about the corpus**, not an
    # error: the line is listed and correct, and one of the other two inclusion
    # conditions rejected the file. Exiting 1 here said "the fetch failed"
    # about a PDF nobody tried to fetch — found by running the verb.
    if skipped.reason == "not an indexed file type":
        # ASCII only: a Windows console runs cp1252 and `→` (U+2192) is not in
        # it, so this line crashed `fux add` on both Windows arms of CI. See
        # `tests/test_windows_console_safe.py` — second occurrence of this
        # failure class, so it is a check now rather than a lesson.
        print(
            "  -> the line is listed, and the type allowlist rejects it. "
            f"`fux add '*{Path(entry).suffix}' --types` allows it; "
            "adding a file never overrides the allowlist"
        )
    return 0


def _seed_types(path: Path) -> None:
    """Write the built-in allowlist before adding the first custom pattern.

    **Because the file replaces the default rather than extending it.** An
    absent types file means `gitdir.DEFAULT_TYPES` applies (SR-TYPES); the
    moment one exists, it is the whole allowlist. So `fux add '*.pdf' --types`
    on a repo with no types file would have written a one-entry file and
    silently un-indexed every markdown document in the corpus — an invisible
    filter, which is the exact defect W-55 was opened about.

    Seeding is the honest fix: the file starts by stating what was already
    true, so the diff shows the allowlist growing by one rather than being
    replaced by one. The bindings fux would have derived are written as
    `[decoders]` lines, so the map does not decay from its first entry.
    """
    from .decode import builtin_bindings
    from .ingest.gitdir import DEFAULT_TYPES

    bindings = {ext.lstrip("."): name for ext, name in builtin_bindings().items()}
    prose = [glob for glob in DEFAULT_TYPES if typesfile.pattern_extension(glob) not in bindings]
    header = "\n".join(
        [
            "# Which files are documents, and which decoder reads each one. See SR-TYPES.",
            "#",
            "# fux created this file when the first pattern was added. What is below is",
            "# the built-in default, written out: this file REPLACES that default rather",
            "# than extending it, so leaving it out would have un-indexed every document",
            "# already in the corpus.",
            "#",
            "# `include` lists globs that are already text. `[decoders]` maps an",
            "# extension to the module that reads it, and a bound extension IS a",
            "# document. Nothing here subtracts: exclusions live in .fux/.fuxignore.",
        ]
    )
    text = typesfile.render(prose, bindings, header=header)
    path.write_text(text, encoding="utf-8", newline="\n")


def _pattern_ext(pattern: str) -> str:
    """The extension a bare `*.ext` pattern names, with its dot (`.pdf`), or `""`.

    A thin wrapper over `typesfile.pattern_extension`, which is **the one
    definition** of that shape; the registry this feeds keys on the dotted form.
    """
    ext = typesfile.pattern_extension(pattern)
    return f".{ext}" if ext else ""


def _plan(spec: sourcelist.ListSpec, args) -> str:
    """What `add` would do after writing the line — for `--dry-run`."""
    if getattr(args, "no_ingest", False):
        return "nothing (--no-ingest)"
    if spec is sourcelist.URLS and not getattr(args, "no_fetch", False):
        return "fetch this URL only, then ingest"
    return "ingest (no network)"


def cmd_remove(args) -> int:
    """Take an entry out of the corpus — by deleting its line, or excluding it."""
    root = _root()
    entry = args.entry
    spec = dispatch(entry, args)
    entry = normalize_entry(entry, spec)
    path = list_path(root, spec)
    reason = spec.validate(entry)
    if reason is not None:
        raise FuxError(f"{reason}: {entry!r}")

    if getattr(args, "dry_run", False):
        entries = _read(path, spec)
        if any(e.value == entry and not e.exclude for e in entries):
            print(f"would remove  {entry} — it has its own line")
        elif spec is sourcelist.TYPES:
            raise FuxError(
                f"{entry} is not in {_rel(root, path)}. The types list has no exclusions: to "
                "keep matching files out of the index, write the pattern in .fux/.fuxignore"
            )
        else:
            ancestor = _covering_ancestor(entry, entries)
            if ancestor is None:
                raise FuxError(
                    f"{entry} is not in {_rel(root, path)}: no line of its own, and no listed "
                    "entry covers it. Both were checked"
                )
            if any(e.value == entry and e.exclude for e in entries):
                raise FuxError(
                    f"{entry} is already excluded by a `!` line in {_rel(root, path)}, which "
                    "would be left alone. Delete that line to put it back"
                )
            is_dir = (root / entry).is_dir()
            pattern = fuxignore.exclusion_pattern(entry, is_dir=is_dir)
            covering = fuxignore.read(root).decide(entry, is_dir=is_dir, hand_only=True)
            if covering.ignored and covering.rule is not None:
                print(
                    f"would write nothing — `{covering.rule.raw}` at "
                    f"{fuxignore.IGNORE_FILE}:{covering.rule.lineno} already excludes {entry}"
                )
                return 0
            print(f"would exclude {pattern} — covered by {ancestor}, which stays listed")
            print(f"  in {fuxignore.IGNORE_FILE}, leaving {_rel(root, path)} untouched")
            return 0
        print(f"  in {_rel(root, path)}")
        return 0

    before = _index_ids(root) if not getattr(args, "no_ingest", False) else set()
    before_edges = _inbound_edges(root) if before else {}

    action, line, detail = remove_or_exclude(root, path, spec, entry)
    print(f"{action:9s} {line}")
    # **The file the line was actually written to**, which stopped being one
    # file on 2026-09-14: a deletion edits the source list, an exclusion writes
    # `.fux/.fuxignore` (W-165 fix 1). Naming the list either way would point a
    # reader at a file `git diff` shows unchanged.
    written = _rel(root, path) if action == "removed" else fuxignore.IGNORE_FILE
    print(f"  in {written}" + (f" — {detail}" if detail else ""))
    _drop_acquired(root, spec, entry)

    if getattr(args, "no_ingest", False):
        return 0

    _ingest(root, args)

    dropped = before - _index_ids(root)
    if not dropped:
        print("  nothing left the index — it was already not indexed")
        return 0
    if len(dropped) == 1:
        print(f"  dropped {next(iter(dropped))} from the index")
    else:
        print(f"  dropped {len(dropped)} documents from the index")
    inbound = sum(before_edges.get(doc_id, 0) for doc_id in dropped)
    if inbound:
        print(f"  dropped {inbound} inbound edge(s) in the graph")
    return 0


def _inbound_edges(root: Path) -> dict[str, int]:
    """doc id -> how many *other* documents point at it right now.

    Read before the ingest, because afterwards both the target and the edges
    into it are gone and the number cannot be recovered. Edges from documents
    that are themselves being removed are counted here and subtracted by the
    caller's `dropped` set never containing them twice — a self-consistent
    count of what a reader of the graph loses.
    """
    from . import store as store_mod

    counts: dict[str, int] = {}
    for record in store_mod.read_index(root).values():
        for edge in record.get("edges", ()):
            counts[edge["dst"]] = counts.get(edge["dst"], 0) + 1
    return counts


def cmd_update(args) -> int:
    """Re-read what is already listed. **It never writes a line.**"""
    import sys

    root = _root()
    entry = getattr(args, "entry", None)
    if getattr(args, "check", False):
        return _check(root, entry, as_json=bool(getattr(args, "json", False)))

    config = load(root)
    refresh = False
    only_urls = None

    if entry:
        spec = _locate(root, entry)
        if spec is sourcelist.URLS:
            if config.url is None:
                raise FuxError(
                    f"{entry} is listed, but there is no [sources.url] in {CONFIG_NAME} to fetch "
                    "it with. `fux setup` writes a fetcher"
                )
            refresh, only_urls = True, {entry}
            print(f"fetching  {entry} (network — this entry only)", file=sys.stderr)
    else:
        # No `[sources.url]` means the URL half has nothing to do — **not an
        # error**, unlike the `--refresh-urls` this verb replaces. `update`
        # means "re-read my sources", and a repo with only directories has
        # sources to re-read.
        #
        # An **empty** list counts as nothing to do, for the same reason. The
        # surface capture caught this announcing "fetching every listed URL
        # (network)" against a list with no lines in it — a claim about the
        # network that was not true, which is the one thing an L4 announcement
        # may never be.
        listed = _read(list_path(root, sourcelist.URLS), sourcelist.URLS) if config.url else []
        refresh = bool(listed)
        if refresh:
            only_urls, why = _narrow(
                root,
                listed,
                all_urls=getattr(args, "all", False),
                failed_only=getattr(args, "failed", False),
            )
            if only_urls is not None and not only_urls:
                print(f"nothing to fetch — {why}", file=sys.stderr)
                refresh = False
            elif only_urls is not None:
                print(
                    f"fetching  {len(only_urls)} of {len(listed)} listed URL(s) "
                    f"(network) — {why}. `fux update --all` fetches every one",
                    file=sys.stderr,
                )
            else:
                print(
                    f"fetching  {len(listed)} listed URL(s) (network) — {why}",
                    file=sys.stderr,
                )

    report = _ingest(root, args, refresh_urls=refresh, only_urls=only_urls)
    # Fork 3: a saved fetch is worth one line. An optimisation nobody can see is
    # one nobody can verify — and `validate` is exactly the kind that fails
    # silently in the safe direction, so a run where it stopped working looks
    # identical to one where it never ran.
    if getattr(report, "validated", 0):
        print(
            f"  {report.validated} URL(s) unchanged by validate(); no body fetched",
            file=sys.stderr,
        )
    for s in report.skipped:
        if s.rel_path.startswith(("http://", "https://")):
            print(f"  ! {s.rel_path} — {s.reason}; prior record kept", file=sys.stderr)
    return 0


def _narrow(root: Path, listed, *, all_urls: bool, failed_only: bool = False):
    """Which URLs `fux update` fetches, and one line saying why.

    **W-82 ruling 3, landed 2026-08-28:** narrow is the DEFAULT and `--all`
    overrides. *"If the dirty list is the right thing to refresh, it should not
    have to be asked for. A user typing `fux update` wants a current index, not
    a network sweep."*

    Returns `(None, why)` for a full sweep, or `(set_of_urls, why)` for a narrow
    one — `None` and the empty set mean opposite things, which is the whole
    subtlety here.

    ⚠ **An ABSENT dirty list means SWEEP EVERYTHING, not nothing.** `dirty.read`
    collapses missing-and-unreadable to `[]` because it feeds reporting paths;
    a consumer that *acts* on the list cannot afford that, because empty means
    *fetch nothing*. A repo that has never run the hook, or whose runtime
    directory was wiped, would otherwise have `fux update` quietly stop
    fetching — **the exact "the tail silently stops being refreshed" failure
    ruling 3 warns about**, arriving through a tolerance rather than a decision.
    Fail safe, not fail silent.

    ⚠ **Ruling 3 and ruling 10 land together.** With narrow as the default the
    tail is refreshed by the daemon and by nothing else, so a repo that runs no
    daemon and never commits a URL change will not re-fetch. That is why the
    announcement always names `--all`.
    """
    from .maintain import dirty as dirty_mod

    # ⚠ **`--failed` was PARSED AND NEVER READ** from the day it landed until
    # 2026-09-11 (W-140 row 4). `fux update --failed` ran the ordinary narrow
    # pass, so it fetched the *stale* set and reported it as a success — a flag
    # that silently does something else is worse than one that errors.
    #
    # **It is the most specific selector, so it wins over `--all`.** Asking for
    # the failures and getting a full sweep would be the same defect again in a
    # different costume, and argparse cannot express "more specific" — only
    # "mutually exclusive", which would break every script already passing both.
    if failed_only:
        from .maintain import urlstate as urlstate_mod

        known = {e.value for e in listed if not e.exclude}
        failing = {
            url
            for url, health in urlstate_mod.read(root).urls.items()
            if health.fail_streak > 0 and url in known
        }
        return failing, f"{len(failing)} with a failing last run (`--failed`)"
    if all_urls:
        return None, "`--all`"
    if not dirty_mod.is_readable(root):
        return None, "no dirty list yet, so nothing is known to be stale"

    pending = {i[len("url:"):] for i in dirty_mod.read(root) if i.startswith("url:")}
    known = {e.value for e in listed if not e.exclude}
    targeted = pending & known
    return targeted, f"{len(targeted)} known stale"


def _locate(root: Path, entry: str) -> sourcelist.ListSpec:
    """Which list already declares `entry`, or a loud error.

    `update` re-reads what is listed; it does not create. An entry nobody
    listed is a typo or a misremembered path, and creating it silently is how
    `update` would quietly become a second `add`.
    """
    for spec in (sourcelist.URLS, sourcelist.DIRS, sourcelist.TYPES):
        path = list_path(root, spec)
        candidate = normalize_entry(entry, spec)
        if any(e.value == candidate and not e.exclude for e in _read(path, spec)):
            return spec
    raise FuxError(
        f"{entry} is not in any source list, so there is nothing to update. "
        f"`fux add {entry}` lists it — `update` never creates a line"
    )


# -- `fux update --check` --------------------------------------------------


def _check(root: Path, entry: str | None, *, as_json: bool = False) -> int:
    """What has drifted, writing nothing.

    **Offline for the `dirs` half**, which is most of it: a file's freshness is
    its bytes' sha against the record's, and both are local. A URL's is not,
    so `--check` fetches for those and says so — there is no honest way to
    answer "has this page changed" without asking the page.
    """
    import sys

    from . import store as store_mod
    from .refer import freshness

    index = store_mod.read_index(root)
    if entry:
        index = {i: r for i, r in index.items() if r.get("loc") == entry or i == entry}
        if not index:
            raise FuxError(f"{entry} is not in the index — nothing to check")

    stale: list[str] = []
    #: The same findings as `stale`, structured — one dict per drifted
    #: document. **Built alongside rather than parsed back out of the text**:
    #: a JSON view derived from a human table is a second format that can
    #: disagree with the first.
    findings: list[dict] = []
    fresh = 0
    unverified = 0

    for doc_id in sorted(index):
        record = index[doc_id]
        if record.get("src") == "git":
            path = root / record["loc"]
            if not path.is_file():
                stale.append(f"  gone   {record['loc']:<28} indexed, not on disk")
                findings.append({"id": doc_id, "loc": record["loc"], "state": "gone"})
                continue
            disk = store_mod.content_sha(path.read_bytes())
            verdict = freshness.verify(record["sha"], disk)
            if verdict.current:
                fresh += 1
            else:
                stale.append(
                    f"  stale  {record['loc']:<28} index {_short(record['sha'])} · "
                    f"disk {_short(disk)}"
                )
                findings.append(
                    {
                        "id": doc_id,
                        "loc": record["loc"],
                        "state": "stale",
                        "indexed_sha": record["sha"],
                        "disk_sha": disk,
                    }
                )
        else:
            unverified += 1

    if as_json:
        # ⚠ **Exit 0 either way, in this mode too.** The caller reading JSON is
        # the one that most needs the distinction between *drifted* and
        # *failed*, and `drifted` is in the payload.
        print(
            json_mod.dumps(
                {
                    "drifted": findings,
                    "fresh": fresh,
                    "unchecked_urls": unverified,
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 0

    if unverified:
        print(
            f"  {unverified} url document(s) not checked — verifying one means fetching it, "
            "and `--check` does not go to the network on its own",
            file=sys.stderr,
        )

    for line in stale:
        print(line)
    if fresh:
        print(f"  fresh  {fresh} others")
    if stale:
        print(f"{len(stale)} stale. `fux update` reconciles them.")
    else:
        print("nothing has drifted.")
    # **Exit 0 either way.** Drift is a fact, not a failure — a non-zero exit
    # would make "your docs changed" look like a broken command to any caller
    # that checks status, which is every caller in a script.
    return 0


def _short(sha: str) -> str:
    return f"{sha[:4]}…"


# -- bare `fux add` --------------------------------------------------------


def _list_all(root: Path) -> int:
    """Every list, as the loader sees it: sorted, deduped, fully resolved."""
    for spec in (sourcelist.DIRS, sourcelist.TYPES, sourcelist.URLS):
        path = list_path(root, spec)
        print(f"{_rel(root, path)}:")
        if not path.is_file():
            print(f"  (no file — `fux add` writes one; {spec.kind} falls back to its default)")
            continue
        entries = _read(path, spec)
        if not entries:
            print("  (empty)")
            continue
        for e in entries:
            mark = " " if e.is_complete() else "*"
            prefix = "!" if e.exclude else ""
            body = prefix + e.value if e.exclude else sourcelist.render_line(e.value, e.attrs, spec)
            print(f"{mark} {body}")
        incomplete = [e for e in entries if not e.is_complete() and not e.exclude]
        if incomplete:
            print(
                f"\n* {len(incomplete)} line(s) do not state every attribute, so fux did not "
                "write them. They load fine (the reader is lenient); `fux add <entry>` "
                "rewrites one in full."
            )
    return 0
