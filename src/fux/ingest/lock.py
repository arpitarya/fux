"""`fux.lock` — the committed sources ledger (handoff 0004 §B).

One machine-written, human-diffable file at the repo root that answers: *what is
in the corpus, when was it taken, and is it stale?* Sorted JSONL with canonical
separators, so two identical ingests are byte-identical and a git diff is one
line per changed source.

The lock **replaces `.fux/manifest.jsonl` as the committed artifact**; the
manifest survives as an operational, gitignored copy under `.fux/index/` that
carries the fields only the runtime needs (cache path, line offset, title).
That split is the point: git carries the recipe, never the generated state.

Staleness is structural per source kind, because the two kinds admit different
evidence:

- ``kind: file`` — live sha vs the lock's sha (plus new/missing).
- ``kind: url`` — age against ``max_age_days``; you cannot sha a page you have
  not re-fetched, so a `--web` re-crawl is what turns age into sha truth.

`--check` reads only this file, so it works on a fresh clone before any ingest.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

from .. import debug
from ..config import Config

LOCK_NAME = "fux.lock"

# Lock fields per kind, in the order the format documents them. Projection is
# explicit (not "copy everything") so operational churn never touches the lock.
_FILE_FIELDS = ("sha256", "bytes", "converted_at", "fidelity", "converter")
_URL_FIELDS = (
    "url", "sha256", "bytes", "fetched_at", "max_age_days", "depth", "parent",
    "fidelity", "converter",
)


def lock_path(root: Path) -> Path:
    return root / LOCK_NAME


def web_doc_id(url: str) -> str:
    """Stable logical id for a fetched page: ``web:<host>/<path>``.

    Mirrors :func:`fux.ingest.web.cache_rel_for_url` so an id and its cache file
    always agree, and stays POSIX/lowercase-host so Windows and Linux ingests of
    the same crawl produce the same lock.
    """
    parts = urlsplit(url)
    host = parts.netloc.replace(":", "_").lower()
    path = parts.path.strip("/") or "index"
    if parts.query:
        import hashlib

        path += "-" + hashlib.sha256(parts.query.encode()).hexdigest()[:8]
    return f"web:{host}/{path}"


def read(root: Path) -> dict[str, dict]:
    path = lock_path(root)
    if not path.is_file():
        return {}
    records: dict[str, dict] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            record = json.loads(line)
        except ValueError:
            continue  # permissive: a hand-mangled line loses only itself
        if isinstance(record, dict) and "id" in record:
            records[record["id"]] = record
    return records


def write(root: Path, records: list[dict]) -> None:
    path = lock_path(root)
    lines = [
        json.dumps(r, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
        for r in sorted(records, key=lambda r: r["id"])
    ]
    text = "\n".join(lines) + ("\n" if lines else "")
    if not path.is_file() or path.read_text(encoding="utf-8") != text:
        path.write_text(text, encoding="utf-8")
        debug.dbg("lock", "info", "lock written", records=len(records))
    else:
        debug.dbg("lock", "debug", "lock unchanged", records=len(records))


def records_from_entries(entries: list[dict], *, max_age_days: int = 30) -> list[dict]:
    """Project operational manifest entries onto the lock's committed shape."""
    records = []
    for entry in entries:
        if entry.get("origin") in ("url", "attachment"):
            record = {"id": web_doc_id(entry["source"]), "kind": "url"}
            source = {**entry, "max_age_days": entry.get("max_age_days", max_age_days)}
            fields = _URL_FIELDS
        else:
            record = {"id": entry["source"], "kind": "file"}
            source = entry
            fields = _FILE_FIELDS
        for name in fields:
            value = source.get("bytes", source.get("size")) if name == "bytes" else source.get(name)
            if value is not None:
                record[name] = value
        records.append(record)
    return records


# -- three-way check: state ↔ lock ↔ sources -------------------------------


@dataclass
class Status:
    """Result of `fux ingest --check`, one bucket per failure mode."""

    drift: list[tuple[str, str]] = field(default_factory=list)
    stale: list[tuple[str, str]] = field(default_factory=list)
    desync: list[tuple[str, str]] = field(default_factory=list)
    tracked: int = 0

    @property
    def clean(self) -> bool:
        return not (self.drift or self.stale or self.desync)

    @property
    def count(self) -> int:
        return len(self.drift) + len(self.stale) + len(self.desync)


def check(config: Config) -> Status:
    """Compare committed state ↔ fux.lock ↔ the sources on disk.

    Reads the lock only — never the index or the cache — so a fresh clone can
    run this before anything has been built.
    """
    from .convert import skip_reason
    from .manifest import sha256_bytes
    from .walk import walk

    records = read(config.root)
    status = Status(tracked=len(records))
    files = {i: r for i, r in records.items() if r.get("kind") != "url"}

    walked = {sf.rel: sf for sf in walk(config).files}
    for rel, sf in sorted(walked.items()):
        record = files.get(rel)
        data = sf.abspath.read_bytes()
        if record is None:
            if skip_reason(sf, data) is None:  # skipped files are not drift
                status.drift.append((rel, "new — not in fux.lock"))
        elif sha256_bytes(data) != record.get("sha256"):
            status.drift.append((rel, "sha mismatch — re-ingest"))
    for rel in sorted(set(files) - set(walked)):
        status.drift.append((rel, "missing — source deleted; cache orphan"))

    now = _now()
    for doc_id, record in sorted(records.items()):
        if record.get("kind") != "url":
            continue
        age = _age_days(record.get("fetched_at"), now)
        max_age = record.get("max_age_days", config.web.max_age_days)
        if age is not None and age > max_age:
            status.stale.append(
                (doc_id, f"fetched {age}d ago, max {max_age}d — re-run `fux ingest --web`")
            )

    status.desync.extend(_state_desync(config, records))
    debug.dbg(
        "lock", "info", "check complete",
        tracked=status.tracked, drift=len(status.drift),
        stale=len(status.stale), desync=len(status.desync),
    )
    return status


def _state_desync(config: Config, records: dict[str, dict]) -> list[tuple[str, str]]:
    """Committed `.fux/state/` vs the lock. No state plane yet → nothing to say."""
    from ..state import desync_against_lock

    return desync_against_lock(config.root, records)


def _now() -> float:
    """Wall clock, deliberately — and only here.

    Age is a *question asked at check time*, never a value written to an
    artifact, so this cannot break the byte-identical re-ingest guarantee
    (ADR 0002). SOURCE_DATE_EPOCH still wins so tests can pin "today".
    """
    epoch = os.environ.get("SOURCE_DATE_EPOCH", "")
    return float(int(epoch)) if epoch.isdigit() else time.time()


def _age_days(fetched_at: str | None, now: float) -> int | None:
    if not isinstance(fetched_at, str):
        return None
    try:
        when = datetime.strptime(fetched_at, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except ValueError:
        return None
    return max(0, int((now - when.timestamp()) // 86400))
