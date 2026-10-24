"""The committed register — one sorted line per document in the index.

**Arpit, 2026-09-20 (W-199 D4):** *"A log file should be generated of every
document that is indexed, and because we are maintaining the index we should
maintain that log file as well — today there is nowhere we document what files
and URLs were ingested."*

`.fux/index/REGISTER`, committed beside the index it describes. **Its shape is
[SR-INGEST](../../../records/0106_ingest.md) decision 22's** — stated there once,
and this module implements it:

```
# fux.register.v2	rules=5
# loc	sha	decoder	[k=v ...]
CHANGELOG.md	e204170f…	prose
archive/PLAN-v0.30.md	2e0ef4e7…	prose	archived=true
https://wiki.example/ops/cold-store	9c1f0b2e…	html@sha:773b7cb1d9a7be6e	fetch=cdp
```

Three tab-separated columns, then zero or more `key=value` in the sources-list
grammar, **present only when they hold a value — no sentinel**. The two `#`
lines are part of the bytes. `rules=` is `extract.RULES_VERSION`, so a bare
decoder (`prose`) is dated once for the whole file instead of per row.

## Why it may be committed when W-200's ledger may not

| | `.fux/runtime/ingest-log.jsonl` ([`ingestlog`](ingestlog.py)) | `.fux/index/REGISTER` (this) |
|---|---|---|
| committed? | **no** — gitignored, derived | **yes** |
| scope | **one run**, what that run consumed | **the corpus**, what the index holds |
| bound by | nothing durable | [L4](../../../records/0006_LAW-4-deterministic.md) byte-identity |
| answers | *"what did this ingest do?"* | *"what is in here, and what read it?"* |

🔴 **[L4](../../../records/0006_LAW-4-deterministic.md) is what makes it
committable at all.** No wall clock, no run id, no ordering that depends on how
the walk was scheduled — sorted by `loc`, byte-identical across runs from the
same sources. It is derived from the same inputs as the index beside it, so it
moves exactly when the index moves — and when the engine's extraction rules do,
which `rules=` says out loud.

🔴 **[L3](../../../records/0005_LAW-3-content-never-durable.md):** paths and
hashes, never content. A `sha` is not content and a `loc` is not a quote.

🔴 **NOT [L9](../../../records/0011_LAW-9-use-record.md), and that is the whole
reason this file may sit on a committed path.** L9 governs *the record of who
went looking*; this records **what the corpus is**. A register line names a
document that exists whether or not anybody ever queried it. ⚠ **It must never
grow a field naming a question, a query or a reader** — the moment it does it
becomes an L9 artifact on a committed path, which is the one thing L9 forbids.

## The reader parses by the header, never by count

A v1 file (`# loc  kind  sha  decoder  fetcher`, 2026-09-20 to 2026-10-13) is
recognised as **old format** and never read as rows; `fux doctor` names it and
the next `fux ingest` rewrites it. A v2 row splits into `loc, sha, decoder,
*attrs`, and **an unknown key is kept**, so an older engine survives a newer
file. The *writer's* key set is closed (`KEYS`): a row fux builds with a key the
record does not state is a bug, and `render` refuses it.

## `fux register [--json]` — the same rows, from the index, never committed

`cmd_register` prints what the file would be **from the index** — the records,
the decoder digest table and the committed URL list — so it cannot drift from
the index beside it. The default output is the file's bytes exactly
(`fux register | diff - .fux/index/REGISTER` is the drift check by hand);
`--json` is one object per document, which is the machine's view and is why no
second committed file exists.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from ..constants import fixed
from ..errors import FuxError

#: The file, under the committed index plane it describes.
NAME = fixed("register", "file")

#: The format marker on line 1 (`# fux.register.v2\trules=<n>`).
FORMAT = fixed("register", "format")

#: The key on the format line that carries `extract.RULES_VERSION`.
RULES_KEY = fixed("register", "rules_key")

#: The column header, line 2. ⚠ **Part of the bytes**, therefore part of the
#: L4 claim — and what lets a reader name the columns without this module.
HEADER = fixed("register", "header")

#: The closed tail-key set, in the order a row states them (SR-INGEST d22).
KEYS: tuple[str, ...] = tuple(fixed("register", "keys"))

#: The v1 column header, recognised as *old format* and never read as rows.
HEADER_V1 = fixed("register", "header_v1")


@dataclass(frozen=True)
class Row:
    loc: str
    sha: str
    decoder: str
    #: The `k=v` tail, in file order. Empty for the common row.
    attrs: tuple[tuple[str, str], ...] = field(default_factory=tuple)

    def rendered(self) -> str:
        tail = tuple(f"{key}={value}" for key, value in self.attrs)
        return "\t".join((self.loc, self.sha, self.decoder, *tail))

    def attr(self, key: str) -> str | None:
        for name, value in self.attrs:
            if name == key:
                return value
        return None


@dataclass(frozen=True)
class Register:
    """What `read` found: a state, the file's `rules=`, and its rows by `loc`.

    `state` is one of `v2` (rows are meaningful), `old` (a v1 header, or a file
    whose first line is not the v2 format line — never read as rows) and
    `missing` (no readable file). `rules` is `None` unless the format line
    carried one.
    """

    state: str
    rules: int | None = None
    rows: dict[str, Row] = field(default_factory=dict)


def path_for(root: Path) -> Path:
    return root / fixed("index", "dir") / NAME


def format_line(rules: int) -> str:
    return f"# {FORMAT}\t{RULES_KEY}={rules}"


def render(rows: list[Row], *, rules: int) -> str:
    """The file's bytes. **Sorted by `loc`, with a trailing newline.**

    ⚠ **Sorted here rather than by the caller**, so no caller can forget and
    produce a register that is correct in content and unstable in bytes — which
    is the failure the L4 claim is about, and the one a reviewer cannot see.

    🔴 **A key outside `KEYS` is refused.** The reader keeps unknown keys so an
    older engine survives a newer file; the writer is this engine, and a key it
    does not state in SR-INGEST decision 22 is a defect, not a feature.
    """
    for row in rows:
        for key, value in row.attrs:
            if key not in KEYS:
                raise FuxError(
                    f"{NAME}: {row.loc!r} carries a tail key {key!r} that decision 22 "
                    f"does not state (known: {', '.join(KEYS)})"
                )
            if not value or any(c.isspace() for c in value):
                raise FuxError(f"{NAME}: {row.loc!r} {key}={value!r} — a value carries no whitespace and is never empty")
    body = "\n".join(row.rendered() for row in sorted(rows, key=lambda r: r.loc))
    head = f"{format_line(rules)}\n{HEADER}\n"
    return f"{head}{body}\n" if body else head


def write(root: Path, rows: list[Row], *, rules: int) -> None:
    """Replace the register atomically. **Never raises on I/O.**

    ⚠ **Best-effort, like the ledger.** A register that can fail an ingest is
    worse than a register that is occasionally a run behind — `fux doctor`'s
    `register` row is what reports the second case, and there is no way for it
    to report the first. (A `FuxError` from `render` is a bug in fux's own rows
    and is not swallowed.)
    """
    text = render(rows, rules=rules)
    try:
        path = path_for(root)
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            if path.read_text(encoding="utf-8") == text:
                return  # byte-identical: leave the file's mtime alone
        except (OSError, UnicodeDecodeError):
            pass
        tmp = path.with_suffix(".tmp")
        tmp.write_text(text, encoding="utf-8")
        tmp.replace(path)
    except OSError:
        return


def parse(text: str) -> Register:
    """A `Register` from the file's text — by the header, never by count."""
    lines = text.splitlines()
    if not lines:
        return Register(state="missing")
    first = lines[0]
    if not first.startswith(f"# {FORMAT}"):
        # A v1 header, or anything else: *old format*, reported rather than read.
        return Register(state="old")
    rules: int | None = None
    for cell in first.split("\t")[1:]:
        key, sep, value = cell.partition("=")
        if sep and key == RULES_KEY and value.isdigit():
            rules = int(value)
    rows: dict[str, Row] = {}
    for line in lines[1:]:
        if not line or line.startswith("#"):
            continue
        try:
            loc, sha, decoder, *tail = line.split("\t")
        except ValueError:
            continue  # fewer than the three columns: a truncated row describes nothing
        if not sha or not decoder:
            continue
        attrs = []
        for cell in tail:
            key, sep, value = cell.partition("=")
            if sep and key:
                attrs.append((key, value))  # unknown keys kept
        rows[loc] = Row(loc=loc, sha=sha, decoder=decoder, attrs=tuple(attrs))
    return Register(state="v2", rules=rules, rows=rows)


def read(root: Path) -> Register:
    """The committed register, parsed. **Never raises.**

    A file that cannot be read is `missing`; one that is not v2 is `old`. A
    truncated or hand-edited v2 row describes nothing and is skipped, for the
    reason `write` is best-effort: this describes the index, it does not gate
    it — `fux doctor` is where the disagreement is reported.
    """
    try:
        text = path_for(root).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return Register(state="missing")
    return parse(text)


# --- the rows, from the index ---------------------------------------------

def url_provenance(root: Path) -> dict[str, tuple[str, str | None]]:
    """`{url doc id: (decoder digest, fetch name)}` from the committed URL list.

    **Read from the list, not from the run** — a networked ingest knows what
    fetched each URL this run and an offline one knows nothing, and a register
    whose URL rows depended on which kind of run wrote it would change bytes
    for no change in the corpus (L4). The list is committed, the decoder stem
    on it is what `urlsrc` decodes with, and the fetcher name is the line's.

    `{}` when there is no URL source, or the list cannot be read: a URL record
    with no line then renders `prose` with no `fetch=`, which is the honest
    answer rather than a guess.
    """
    from ..config import load as load_config
    from ..acquire import urlsrc

    try:
        config = load_config(root)
    except FuxError:
        return {}
    if config.url is None:
        return {}
    try:
        entries = urlsrc.resolve_urls(urlsrc.read_urls(root, config.url.sources_file), config.url)
    except FuxError:
        return {}
    return {
        f"url:{entry.url}": (urlsrc._decoder_name_for(entry.decoder, root), entry.fetch)
        for entry in entries
    }


def rows_from(records: list[dict], provenance: dict[str, tuple[str, str | None]]) -> list[Row]:
    """The register's rows for one index.

    `provenance` is `{id: (decoder, fetch)}` — the decoder digest string that
    read the document and, for a URL, the fetcher name from its line.

    ⚠ **Every record in the index gets a row and nothing else does.** A skip is
    not in the index, and a register that listed skips would change bytes when a
    transient fetch failed — the L4 break this module's docstring is about,
    arriving through a different column.

    The tail: `archived=true` when the record carries it (declared on the
    source entry, SR-ARCHIVED-CONTENT), `fetch=<name>` when a fetcher is
    recorded. Keys in `KEYS` order; absent when they hold nothing.
    """
    from ..acquire import ingestlog

    out: list[Row] = []
    for record in records:
        doc_id = record.get("id", "")
        decoder, fetch = provenance.get(doc_id, (ingestlog.PROSE, None))
        values = {"archived": "true" if record.get("archived") else None, "fetch": fetch or None}
        attrs = tuple((key, values[key]) for key in KEYS if values.get(key))
        out.append(Row(loc=record.get("loc", ""), sha=record.get("sha", ""), decoder=decoder, attrs=attrs))
    return out


def rows_for(root: Path, records: list[dict], decoder_digests: dict[str, str]) -> list[Row]:
    """`rows_from` with provenance resolved the one way both writers share.

    `fux ingest` passes the digest map it built for the reuse key; `fux
    register` builds the same map from the tree. A file row's decoder is the
    digest bound to its extension (or `prose`); a URL row's comes from the
    committed list. **One function, two callers**, so the file and the verb
    cannot disagree.
    """
    from ..acquire import ingestlog

    urls = url_provenance(root)
    provenance: dict[str, tuple[str, str | None]] = {}
    for record in records:
        doc_id = record.get("id", "")
        if record.get("src") == "url":
            provenance[doc_id] = urls.get(doc_id, (ingestlog.PROSE, None))
        else:
            suffix = Path(record.get("loc", "")).suffix.lower()
            provenance[doc_id] = (decoder_digests.get(suffix, ingestlog.PROSE), None)
    return rows_from(records, provenance)


def from_index(root: Path) -> tuple[list[Row], int]:
    """The rows and `rules=` the register would hold for the index on disk."""
    from ..store import reader as reader_mod
    from ..acquire import decoderdigest
    from . import extract as extract_mod

    records = list(reader_mod.read_index(root).values())
    rows = rows_for(root, records, decoderdigest.binding_digests(root))
    return rows, extract_mod.RULES_VERSION


def as_json(row: Row, *, rules: int) -> dict:
    """One `--json` object: `loc`, `sha`, `decoder {name, digest}`, `rules`,
    then every tail key by name. `digest` is `null` for a decoder shipped with
    fux (no `@sha:` tail), which is what `rules` dates."""
    name, _, digest = row.decoder.partition("@sha:")
    out: dict = {
        "loc": row.loc,
        "sha": row.sha,
        "decoder": {"name": name, "digest": digest or None},
        "rules": rules,
    }
    for key, value in row.attrs:
        out[key] = True if value == "true" else value
    return out


def cmd_register(args) -> int:
    """`fux register [--json]` — read-only, offline, no index write."""
    import json
    import sys

    from ..config import find_root

    root = find_root()
    if root is None:
        raise FuxError("not inside a fux repository (no fux.toml or .git found up the tree)")
    rows, rules = from_index(root)
    try:
        if getattr(args, "json", False):
            for row in sorted(rows, key=lambda r: r.loc):
                sys.stdout.write(json.dumps(as_json(row, rules=rules), ensure_ascii=False) + "\n")
        else:
            sys.stdout.write(render(rows, rules=rules))
        sys.stdout.flush()
    except BrokenPipeError:
        # `fux register | head` is a documented use: a reader that closed early
        # is not an error. Point stdout at nowhere so the interpreter's exit
        # flush cannot raise it a second time.
        import os

        os.dup2(os.open(os.devnull, os.O_WRONLY), sys.stdout.fileno())
    return 0
