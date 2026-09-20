"""The committed register — one sorted line per document in the index.

**Arpit, 2026-09-20 (W-199 D4):** *"A log file should be generated of every
document that is indexed, and because we are maintaining the index we should
maintain that log file as well — today there is nowhere we document what files
and URLs were ingested."*

`.fux/index/REGISTER`, committed beside the index it describes.

## Why it may be committed when W-200's ledger may not

| | `.fux/runtime/ingest-log.jsonl` ([`ingestlog`](ingestlog.py)) | `.fux/index/REGISTER` (this) |
|---|---|---|
| committed? | **no** — gitignored, derived | **yes** |
| scope | **one run**, what that run consumed | **the corpus**, what the index holds |
| bound by | nothing durable | [L3](../../../records/0005_LAW-3-deterministic.md) byte-identity |
| answers | *"what did this ingest do?"* | *"what is in here, and what read it?"* |

🔴 **[L3](../../../records/0005_LAW-3-deterministic.md) is what makes it
committable at all.** No wall clock, no run id, no ordering that depends on how
the walk was scheduled — sorted by `loc`, byte-identical across runs from the
same sources. It is derived from the same inputs as the index beside it, so it
moves exactly when the index moves.

🔴 **[L2](../../../records/0004_LAW-2-content-never-durable.md):** paths and
hashes, never content. A `sha` is not content and a `loc` is not a quote.

🔴 **NOT [L8](../../../records/0010_LAW-8-use-record.md), and that is the whole
reason this file may sit on a committed path.** L8 governs *the record of who
went looking*; this records **what the corpus is**. A register line names a
document that exists whether or not anybody ever queried it. ⚠ **It must never
grow a field naming a question, a query or a reader** — the moment it does it
becomes an L8 artifact on a committed path, which is the one thing L8 forbids.

## ⚠ The ruling named a fifth column and it could not survive L3

D4's words are `loc · sha · decoder@version · fetcher · outcome`. **`outcome`
is a fact about a RUN, not about the index**: the first ingest of a corpus
writes `indexed` for every document and the second writes `reused` for every
one, from identical sources — so the column alone would break the byte-identity
the same decision requires, and the test asserting *two ingests write it once*
would fail on a file that was otherwise correct.

**`kind` (`file` / `url`) replaced it**: stable across runs, already in the
data, and it answers the half of *"what files and URLs were ingested"* that the
`loc` does not. **The run-shaped `outcome` — indexed, reused, skipped and why —
is exactly what W-200's ledger already carries**, per-run, where it belongs.
Recorded in [SR-INGEST](../../../records/0106_ingest.md) decision 22.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

#: The file, under the committed index plane it describes.
NAME = "REGISTER"

#: One tab-separated header line, so a reader knows the columns without this
#: module. ⚠ **Part of the bytes**, therefore part of the L3 claim.
HEADER = "# loc\tkind\tsha\tdecoder\tfetcher"

#: What a URL row carries when no fetcher was recorded for it — a carried
#: record from before the field existed. **Absent and unknown are different**,
#: and this says which.
UNKNOWN = "-"


@dataclass(frozen=True)
class Row:
    loc: str
    kind: str
    sha: str
    decoder: str
    fetcher: str | None = None

    def rendered(self) -> str:
        return "\t".join((self.loc, self.kind, self.sha, self.decoder, self.fetcher or UNKNOWN))


def path_for(root: Path) -> Path:
    return root / ".fux" / "index" / NAME


def render(rows: list[Row]) -> str:
    """The file's bytes. **Sorted by `loc`, with a trailing newline.**

    ⚠ **Sorted here rather than by the caller**, so no caller can forget and
    produce a register that is correct in content and unstable in bytes — which
    is the failure the L3 claim is about, and the one a reviewer cannot see.
    """
    body = "\n".join(row.rendered() for row in sorted(rows, key=lambda r: (r.loc, r.kind)))
    return f"{HEADER}\n{body}\n" if body else f"{HEADER}\n"


def write(root: Path, rows: list[Row]) -> None:
    """Replace the register atomically. **Never raises.**

    ⚠ **Best-effort, like the ledger.** A register that can fail an ingest is
    worse than a register that is occasionally a run behind — `fux doctor`'s
    `register` row is what reports the second case, and there is no way for it
    to report the first.
    """
    try:
        from ..store import fuxdir

        path = path_for(root)
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(render(rows), encoding="utf-8")
        tmp.replace(path)
        _ = fuxdir
    except OSError:
        return


def read(root: Path) -> dict[str, Row]:
    """`{loc: Row}` from the committed register, or `{}`. **Never raises.**

    A truncated or hand-edited file reads as *no register* rather than as a
    failure, for the reason `write` is best-effort: this describes the index, it
    does not gate it.
    """
    try:
        text = path_for(root).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return {}
    out: dict[str, Row] = {}
    for line in text.splitlines():
        if not line or line.startswith("#"):
            continue
        parts = line.split("\t")
        if len(parts) != 5:
            continue
        loc, kind, sha, decoder, fetcher = parts
        out[loc] = Row(
            loc=loc, kind=kind, sha=sha, decoder=decoder,
            fetcher=None if fetcher == UNKNOWN else fetcher,
        )
    return out


def rows_from(records: list[dict], provenance: dict[str, tuple[str, str | None]]) -> list[Row]:
    """The register's rows for one index.

    `provenance` is `{id: (decoder, fetcher)}` — the same map the ledger builds,
    so the committed register and the per-run ledger can never disagree about
    which decoder produced a record.

    ⚠ **Every record in the index gets a row and nothing else does.** A skip is
    not in the index, and a register that listed skips would change bytes when a
    transient fetch failed — the L3 break this module's docstring is about,
    arriving through a different column.
    """
    out: list[Row] = []
    for record in records:
        doc_id = record.get("id", "")
        decoder, fetcher = provenance.get(doc_id, ("prose", None))
        out.append(
            Row(
                loc=record.get("loc", ""),
                kind="url" if record.get("src") == "url" else "file",
                sha=record.get("sha", ""),
                decoder=decoder,
                fetcher=fetcher,
            )
        )
    return out
