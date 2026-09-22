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
- **2026-09-22** — 🔴 **the same class, past the gate built for it.** W-205 part
  2 family (a) stepped `ANALYZER_VERSION` **v2 → v3**; `SCHEMA_ID` stayed v4,
  correctly, because no property appeared. This file checked `_format` **and
  nothing else**, so it stayed green while `fux ask` on this repository answered
  *"written by analyzer 'v2', this reader is 'v3'"*. **A gate built against one
  field of a header is a gate against one bug.**

⚠ **So the check reads every field the reader refuses on**, derived from the
header the engine writes rather than listed by hand — a fourth field added to
`HEADER` is covered the day it is added, without anybody remembering this file.

**What makes this invisible to the fast suite is the shape of the bug.** Every
unit and e2e test builds its own index in a `tmp_path`, so they exercise the
writer and the reader against each other and never against the artefact this
repository actually commits. The one index that no test reads is the one in
this tree.

The check is the **first line** of the header shard and nothing deeper,
deliberately: reading further would be re-implementing the reader, and the
reader's own refusal is the thing being anticipated here — just early, and in
the suite everybody runs.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from fux.store.format import HEADER

ROOT = Path(__file__).resolve().parents[1]
HEADER_SHARD = ROOT / ".fux" / "index" / "00.jsonl"

FIX = (
    "The engine moved and this repository's own index did not — run "
    "`fux ingest --full` then `fux build`, and commit `.fux/index/`. "
    "Do NOT delete `.fux/index/` by hand: `url:` records are the one thing "
    "in it that no re-extraction can rebuild."
)


def _committed_header() -> dict:
    assert HEADER_SHARD.is_file(), f"{HEADER_SHARD} is missing — this repo indexes itself"
    with HEADER_SHARD.open(encoding="utf-8") as fh:
        return json.loads(fh.readline())


@pytest.mark.parametrize("field", sorted(HEADER))
def test_the_committed_index_declares_what_this_engine_writes(field):
    """Every field of `HEADER`, because the reader refuses on every one of them.

    🔴 **Parametrised over `HEADER` rather than over a list written here.** The
    list written here was `["_format"]`, and on 2026-09-22 that is exactly what
    let an `ANALYZER_VERSION` bump walk past the gate built to stop this class.
    """
    found = _committed_header().get(field)
    assert found == HEADER[field], (
        f".fux/index/ declares {field}={found!r} and this engine writes "
        f"{HEADER[field]!r}. " + FIX
    )
