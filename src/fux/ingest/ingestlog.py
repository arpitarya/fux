"""One runtime line per document naming the decoder and fetcher that made it.

🔴 **W-200's spec named this `ingest/provenance.py`, writing
`.fux/runtime/provenance.jsonl`. BOTH were already taken, and the second one
was a defect rather than a confusion.**

`fux.query.provenance` is SR-PROVENANCE's **answer receipts** — how an *answer*
was produced, a thing [L8](../../../records/0010_LAW-8-use-record.md) governs
because it records what somebody **asked** — and its journal is written to
`.fux/runtime/provenance.jsonl` **only under explicit consent** (W-147: the flag
*and* the output-TOML key, ruled by Arpit 2026-09-13, *"I need the flag as well
as output TOML configuration"*).

**Writing this ledger there would have made every `fux ingest` create a file
that is supposed to require consent** — and `tests_e2e/test_verbs.py::
test_both_journal_consent_surfaces_write_and_neither_alone_is_removable` caught
it, with the message *"a journal appeared with no consent of any kind"*. **L8
outranks a work item**, so the path moved; the module moved with it, because
leaving two modules named `provenance` writing differently-named files is the
same trap one layer up.

**This file records what INGEST did** — never what anyone asked — which is why
L8 does not reach it, and why **it must never grow a query field.**

**Arpit, 2026-09-18 (W-200):** *"Create a log file of the files that are being
consumed as well as the URLs that are being consumed, with what decoders were
used, what version they were used, and just some kind of information."*

## The gap this closes, and the one it does not

[W-166](../../../archive/open/W-166-carry-forward-invalidation.md) put the decoder into the
**reuse key**, so `.fux/runtime/decoder-digests.json` answers *"has the `.pdf`
decoder moved since the last run?"* — **per extension**. `docs.jsonl` answers
*"what documents are in the index?"* — id, loc, title, lengths, mtime.
`url-state.json` answers *"is this URL healthy?"*

**Nothing answered: which decoder, at which version, produced THIS record, from
which bytes, fetched by what.** That is one join away from three files and
nobody could make it. This file makes it.

⚠ **It answers nothing about a QUERY.** No field here records what was asked,
who asked, or what came back — it records what *ingest did*, so
[L8](../../../records/0010_LAW-8-use-record.md) does not reach it, and **it must
never grow a query field.** A row about a document is not a use record; the
moment one of these lines names a question, it becomes one.

## The shape, and why each part of it

    .fux/runtime/ingest-log.jsonl

One JSON object per document the run consumed, **keys sorted, one line each,
sorted by `id`** — so two machines ingesting the same tree write the same bytes,
and a diff between two runs is readable.

| field | on | why |
|---|---|---|
| `id` · `kind` · `loc` | every row | the join key, and the thing a human recognises |
| `decoder` | every row | the string `decoderdigest` already mints — `xlsx@v1` for a built-in, `xlsxdoc@sha:…` for a consumer file, `prose` for Markdown and text, which no decoder claims |
| `fetcher` | `url` rows | `<stem>@sha:<file sha>`. **Fetchers have no `VERSION`** — a consumer owns the file, so its sha *is* its version, the same rule a consumer decoder already follows |
| `raw_sha` · `raw_bytes` · `wlen` | where known | numbers and hashes. **No content, no title, no excerpt** ([L2](../../../records/0004_LAW-2-content-never-durable.md)) |
| `outcome` | every row | `indexed` · `reused` · `skipped:<reason>` · `refused:<rule>` · `queued` |
| `run_seq` | every row | the counter `url-state.json` already owns. **No wall clock** (L3) |

`loc` is already in `docs.jsonl`, so it leaks nothing new.

## Five decisions, each with a cost

1. **Runtime, never committed.** A consumer decoder's sha differs between two
   machines; a committed field would state a fact true on one of them — the
   argument that kept the blob sha off the record
   ([SR-ACQUIRED](../../../records/0145_acquired-plane.md)). Gitignored, it is
   advisory and reversible: **delete the file and nothing is lost.** The cost is
   that it does not travel with a clone, so a teammate sees nothing until they
   ingest.
2. **Clock-free.** `run_seq`, never `time.time()`, so nothing that reads this
   can pick up non-determinism (L3). The cost is that *"when"* is answerable
   only as *"how many networked runs ago"*.
3. **Best-effort, written once, atomically, at the end of ingest.** The
   `_record_refusals` / `_record_stale_redaction` precedent: **a ledger that can
   fail a run is worse than no ledger.** An `OSError` is one stderr note and the
   ingest succeeds.
4. **A separate file, not columns on `docs.jsonl`.** That file is the query hot
   path and is read on every `ask`; this one is read by `doctor` and by humans.
5. **`reused` carries the decoder that produced the REUSED record**, not the
   tree's current one — otherwise the stale-decoder finding could never fire,
   because every row would agree with the tree by construction. Read from the
   prior row; `unknown` when there is no prior row (a first run after this
   feature lands, or a deleted file).

## Size

~200 B x 10 000 documents = **2 MB**. No cap and no rotation, deliberately: a
rotation policy is a second thing to be wrong about, and the file is one
`rm` from gone.
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path

#: Under `.fux/runtime/`, which `.gitignore` already covers.
INGEST_LOG_FILE = "ingest-log.jsonl"

#: The decoder string for a document no decoder claims — Markdown and plain
#: text, read by `extract.py` rather than by a `decode/` module. `decoderdigest`
#: mints nothing for these because they have no binding, so the name is minted
#: here, once, rather than left as `null` for every reader to interpret.
PROSE = "prose"

#: A `reused` row whose prior row is missing. **Not `null`**: absent and
#: unknown are different, and only one of them means *"this ran before the
#: ledger existed"*.
UNKNOWN = "unknown"


@dataclass(frozen=True)
class Row:
    """One document's provenance. Every field is a number, a hash or a name."""

    id: str
    kind: str  # "file" | "url"
    loc: str
    outcome: str
    run_seq: int
    decoder: str = PROSE
    #: URL rows only. `None` is omitted from the written line, so a file row
    #: does not carry a key that can only ever be null for it.
    fetcher: str | None = None
    raw_sha: str | None = None
    raw_bytes: int | None = None
    wlen: int | None = None

    def as_json(self) -> dict:
        """The written object — `None` fields dropped, keys sorted by the writer."""
        return {k: v for k, v in asdict(self).items() if v is not None}


def path_for(root: Path) -> Path:
    """`<root>/.fux/runtime/ingest-log.jsonl`."""
    from ..store import fuxdir

    return fuxdir.fux_dir(root) / "runtime" / INGEST_LOG_FILE


def read(root: Path) -> dict[str, Row]:
    """`{id: Row}` from the last run, or `{}`.

    **Never raises.** A truncated or hand-edited file reads as *no prior run*
    rather than as a failure: this ledger is advisory, and a reader that can
    break an ingest is worse than one that occasionally knows nothing.
    """
    try:
        text = path_for(root).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return {}
    out: dict[str, Row] = {}
    for line in text.splitlines():
        if not line.strip():
            continue
        try:
            obj = json.loads(line)
            out[obj["id"]] = Row(
                id=obj["id"],
                kind=obj.get("kind", "file"),
                loc=obj.get("loc", ""),
                outcome=obj.get("outcome", ""),
                run_seq=int(obj.get("run_seq", 0)),
                decoder=obj.get("decoder", PROSE),
                fetcher=obj.get("fetcher"),
                raw_sha=obj.get("raw_sha"),
                raw_bytes=obj.get("raw_bytes"),
                wlen=obj.get("wlen"),
            )
        except (ValueError, TypeError, KeyError):
            continue  # one bad line loses one row, never the file
    return out


def write(root: Path, rows: list[Row]) -> None:
    """Replace the ledger with `rows`, sorted by id, atomically. **Never raises.**

    Sorted by `id` and with sorted keys so the same tree gives the same bytes on
    two machines (L3) — the file is gitignored, but a ledger that differs
    run-to-run for no reason is one nobody diffs.

    An `OSError` is swallowed by the caller's `try`: see the module docstring,
    decision 3. This function does its own, so a caller cannot forget.
    """
    try:
        from ..store import fuxdir

        fuxdir.derived_dir(root, "runtime")
        target = path_for(root)
        payload = "".join(
            json.dumps(row.as_json(), sort_keys=True, ensure_ascii=False) + "\n"
            for row in sorted(rows, key=lambda r: r.id)
        )
        tmp = target.with_suffix(target.suffix + ".tmp")
        tmp.write_text(payload, encoding="utf-8")
        os.replace(tmp, target)
    except OSError:
        pass


def fetcher_digest(fetcher_path: str | Path) -> str:
    """`<stem>@sha:<16 hex>` for a consumer-owned fetcher file.

    **The file's sha IS its version**, exactly as a `.fux/decoders/` module's is
    ([SR-DECODE](../../../records/0139_decode.md) decision 11a): fux can require
    nothing of a consumer's file and hold nothing about it, so a `VERSION`
    constant there would be a promise nobody keeps.

    An unreadable file gives `<stem>@sha:unreadable` rather than raising — the
    same choice `decoderdigest.of` makes, and for the same reason: a digest that
    cannot be computed must never read as *unchanged*.
    """
    import hashlib

    p = Path(fetcher_path)
    try:
        raw = p.read_bytes()
    except OSError:
        return f"{p.stem}@sha:unreadable"
    return f"{p.stem}@sha:{hashlib.sha256(raw).hexdigest()[:16]}"


def stale_decoder_count(root: Path, current: dict[str, str]) -> int:
    """How many rows name a decoder whose digest differs from the tree's.

    `current` is `decoderdigest.binding_digests()` — `{extension: digest}`. A
    row is stale when its decoder string names the same decoder at a different
    version, which is exactly the case `fux ingest --full` fixes and a plain
    `fux ingest` does not (the reuse key catches a *moved* binding, not a record
    written before the binding existed).

    ⚠ **A row whose decoder is `prose` or `unknown` is never stale**: no binding
    claims Markdown, and `unknown` means the ledger predates the row rather than
    that the decoder moved. Counting either would report a number that no
    command can bring down.
    """
    by_name = {digest.split("@", 1)[0]: digest for digest in current.values()}
    stale = 0
    for row in read(root).values():
        if row.decoder in (PROSE, UNKNOWN):
            continue
        name = row.decoder.split("@", 1)[0]
        live = by_name.get(name)
        if live is not None and live != row.decoder:
            stale += 1
    return stale
