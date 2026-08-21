"""`fux add` / `fux remove` / `fux update` — the corpus, as a first-class verb.

The three committed source lists (`.fux/sources/dirs`, `urls`, `types`) are
what fux indexes. Until W-63 only one of them had a command — `fux url` — so
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

It does not render errors — `cli.main` is the only boundary (ADR-CLI
decision 3), so everything here raises. It does not open a socket: the fetch
`add` performs is `ingest.run`'s, behind the same consumer-fetcher contract
every other fetch uses. And it never writes the index itself — `add`,
`remove` and `update` all end in **one** `ingest.run`, because a second write
path is how L3's byte-identical guarantee breaks.

## It edits one line, never the file

A regenerating writer would be simpler and would silently eat the grouping
comments a human left behind — and under
[ADR-URL-LIST](../../docs/adr/0018_url-list.md) decision 3 those comments are
the reason the file is maintainable at all. So an add inserts one line at its
sorted position, an update rewrites that one line and keeps its trailing
comment, and a removal deletes it. Every other byte is untouched. The loader
sorts regardless (decision 4), so the insertion position is a courtesy to the
reader, not a correctness property.

A fux-written line carries **every** attribute, explicitly, even where the
value equals the default (decision 12): a generated file holds no implicit
state, so changing a policy is a one-word diff rather than the appearance or
disappearance of a key.
"""

from __future__ import annotations

import re
from pathlib import Path

from .config import (
    CONFIG_NAME,
    DEFAULT_TYPES_FILE,
    DEFAULT_URLS_FILE,
    find_root,
    load,
)
from .errors import FuxError
from .ingest import sourcelist

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
        return root / (config.url.urls_file if config.url is not None else DEFAULT_URLS_FILE)
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
    if not path.is_file():
        return []
    return sourcelist.parse(path.read_text(encoding="utf-8"), spec, origin=str(path))


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


def add(
    path: Path, value: str, overrides: dict[str, str], spec: sourcelist.ListSpec
) -> tuple[str, str, str]:
    """Add or update one line. Returns `(action, new_line, previous_line)`."""
    text = path.read_text(encoding="utf-8") if path.is_file() else ""
    lines = text.split("\n")

    existing = sourcelist.parse(text, spec, origin=str(path))
    prior = next((e for e in existing if e.value == value and not e.exclude), None)
    attrs = spec.defaults() | (prior.attrs if prior is not None else {}) | overrides
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


def remove_or_exclude(path: Path, spec: sourcelist.ListSpec, value: str) -> tuple[str, str, str]:
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
    """
    entries = _read(path, spec)

    if any(e.value == value and not e.exclude for e in entries):
        return "removed", remove(path, value).strip(), ""

    if not spec.allow_exclusions:
        raise FuxError(
            f"{value} is not in {path}. `{spec.kind}` has no exclusions — every entry is a line, "
            "so there is nothing to subtract from and nothing to remove but a line that exists"
        )

    if any(e.value == value and e.exclude for e in entries):
        raise FuxError(
            f"{value} is already excluded in {path}. `!` subtracts and nothing adds back, so "
            "there is nothing further to remove — delete the `!` line to put it back"
        )

    ancestor = _covering_ancestor(value, entries)
    if ancestor is None:
        raise FuxError(
            f"{value} is not in {path}: it has no line of its own, and no listed entry covers it. "
            f"Both were checked. `fux add {value}` would list it; nothing needs removing"
        )

    lines = (path.read_text(encoding="utf-8") if path.is_file() else "").split("\n")
    line = f"!{value}"
    lines.insert(_insert_at(lines, line), line)
    _write(path, lines)
    return "excluded", line, f"{ancestor} still listed; this path is subtracted from it"


# -- flags -> recorded attributes ------------------------------------------


def _overrides(args, spec: sourcelist.ListSpec) -> dict[str, str]:
    """Flags -> the attributes to record. Two flags for one attribute is an error.

    `--cdp --http` has no defensible meaning, and picking one silently is how a
    scripted call records the opposite of what it meant.

    A flag that names an attribute this list does not have is also an error
    rather than a silent no-op — `fux add docs/ --cdp` is someone believing
    something about the entry they just wrote, and the closed attribute set
    (ADR-URL-LIST decision 11) is only worth having if it is enforced on the
    way in as well as on the way out.
    """
    pairs = (("fetch", ("cdp", "http")), ("meta", ("plain", "hashed")), ("archived", ("archived",)))
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
        overrides[attribute] = "true" if attribute == "archived" else given[0]
    return overrides


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


def _ingest(root: Path, args, *, refresh_urls: bool = False, only_urls=None):
    """Every verb's single way into the index (L3). Imported lazily (ADR-CLI 7)."""
    from .ingest import ingest_and_report

    return ingest_and_report(root, args, refresh_urls=refresh_urls, only_urls=only_urls)


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

    entries = _read(path, spec)
    if any(e.value == entry and e.exclude for e in entries):
        raise FuxError(
            f"{entry} is excluded in {_rel(root, path)}. There is no un-exclude by design — "
            f"`!` subtracts and nothing adds back, so delete the `!{entry}` line to index it again"
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

    if getattr(args, "dry_run", False):
        preview = sourcelist.render_line(entry, spec.defaults() | overrides, spec)
        print(f"would add {preview}")
        print(f"  in {_rel(root, path)}")
        print(f"  then: {_plan(spec, args)}")
        return 0

    path.parent.mkdir(parents=True, exist_ok=True)
    if spec is sourcelist.TYPES and not path.is_file():
        _seed_types(path)
    action, line, previous = add(path, entry, overrides, spec)
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

    report = _ingest(root, args, refresh_urls=refresh, only_urls=only_urls)

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
        print(
            "  → the line is listed, and the type allowlist rejects it. "
            f"`fux add '*{Path(entry).suffix}' --types` allows it; "
            "adding a file never overrides the allowlist"
        )
    return 0


def _seed_types(path: Path) -> None:
    """Write the built-in allowlist before adding the first custom pattern.

    **Because the file replaces the default rather than extending it.** An
    absent `types` file means `gitdir.DEFAULT_TYPES` applies (ADR-TYPES); the
    moment one exists, it is the whole allowlist. So `fux add '*.pdf' --types`
    on a repo with no types file would have written a one-line file and
    silently un-indexed every markdown document in the corpus — an invisible
    filter, which is the exact defect W-55 was opened about.

    Seeding is the honest fix: the file starts by stating what was already
    true, so the diff shows the allowlist growing by one rather than being
    replaced by one.
    """
    from .ingest.gitdir import DEFAULT_TYPES

    header = [
        "# What counts as a document. One pattern per line; `!` subtracts.",
        "#",
        "# fux created this file when the first pattern was added. The lines",
        "# below are the built-in default, written out explicitly: this file",
        "# REPLACES that default rather than extending it, so leaving them out",
        "# would have un-indexed every document already in the corpus.",
        "#",
        "# See ADR-TYPES.",
        "",
    ]
    _write(path, header + list(DEFAULT_TYPES))


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
        else:
            ancestor = _covering_ancestor(entry, entries)
            if ancestor is None:
                raise FuxError(
                    f"{entry} is not in {_rel(root, path)}: no line of its own, and no listed "
                    "entry covers it. Both were checked"
                )
            print(f"would exclude !{entry} — covered by {ancestor}, which stays listed")
        print(f"  in {_rel(root, path)}")
        return 0

    before = _index_ids(root) if not getattr(args, "no_ingest", False) else set()
    before_edges = _inbound_edges(root) if before else {}

    action, line, detail = remove_or_exclude(path, spec, entry)
    print(f"{action:9s} {line}")
    print(f"  in {_rel(root, path)}" + (f" — {detail}" if detail else ""))

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
        return _check(root, entry)

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
            print(f"fetching  {len(listed)} listed URL(s) (network)", file=sys.stderr)

    report = _ingest(root, args, refresh_urls=refresh, only_urls=only_urls)
    for s in report.skipped:
        if s.rel_path.startswith(("http://", "https://")):
            print(f"  ! {s.rel_path} — {s.reason}; prior record kept", file=sys.stderr)
    return 0


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


def _check(root: Path, entry: str | None) -> int:
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
    fresh = 0
    unverified = 0

    for doc_id in sorted(index):
        record = index[doc_id]
        if record.get("src") == "git":
            path = root / record["loc"]
            if not path.is_file():
                stale.append(f"  gone   {record['loc']:<28} indexed, not on disk")
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
        else:
            unverified += 1

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
