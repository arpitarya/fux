"""This repository's OWN committed index must be readable by this engine.

**Two strikes, so a gate** — [SR-WORK-SESSION](../records/0060_WORK-session.md)
decision 13. The failure class is *the engine moved and the committed index did
not, and nothing said so*:

- **2026-09-11** — `types.toml` became `formats.toml`, the corpus changed with
  it, and the WORKLOG records that *"the committed index had to move and nobody
  had said so"*. Sixty shards were re-ingested by hand, after the fact.
- **2026-09-21** — `meta = "hashed"` was deleted, `SCHEMA_ID` stepped
  **v3 → v4**, and the repo's own `.fux/index/` stayed at v3 through 47
  commits. 🔴 **Both suites were green the whole time.** What went red was
  `node-arm`, on a `fux build` — a workflow nobody runs locally — and only on
  the push that finally reached CI.

**What makes this invisible to the fast suite is the shape of the bug.** Every
unit and e2e test builds its own index in a `tmp_path`, so they exercise the
writer and the reader against each other and never against the artefact this
repository actually commits. The one index that no test reads is the one in
this tree.

The check is a single line of the header shard, deliberately: reading further
would be re-implementing the reader, and the reader's own refusal is the thing
being anticipated here — just early, and in the suite everybody runs.
"""

from __future__ import annotations

import json
from pathlib import Path

from fux.store.format import SCHEMA_ID

ROOT = Path(__file__).resolve().parents[1]
HEADER_SHARD = ROOT / ".fux" / "index" / "00.jsonl"


def test_the_committed_index_declares_the_format_this_engine_writes():
    assert HEADER_SHARD.is_file(), f"{HEADER_SHARD} is missing — this repo indexes itself"
    with HEADER_SHARD.open(encoding="utf-8") as fh:
        header = json.loads(fh.readline())
    found = header.get("_format")
    assert found == SCHEMA_ID, (
        f".fux/index/ declares {found!r} and this engine writes {SCHEMA_ID!r}. "
        "The format moved and this repository's own index did not — run "
        "`fux ingest --full` then `fux build`, and commit `.fux/index/`. "
        "Do NOT delete `.fux/index/` by hand: `url:` records are the one thing "
        "in it that no re-extraction can rebuild."
    )
