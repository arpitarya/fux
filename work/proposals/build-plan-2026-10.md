---
type: Proposal
title: The build plan, October 2026 — the `unbuilt` and `ungated` rows that have a ruled approach and no builder yet
description: "The 2026-10-04 ruling pass over the backlog (W-251 §4) left three decided-but-unbuilt rows whose approach is now settled and whose build nobody is about to start: B-031 (a `--json` shape for the write verbs — declared, waiting for a caller), B-041 (fence-aware grammars for `.rst`/`.adoc`/`.org`), B-259 (display width is not `len()`). This file holds each approach — key files, definition of done, size, model, the law it must respect — so the row graduates into a `W-nn` by copying a section. Three further rows graduated straight into items on the same day and are named here so the map is whole."
status: proposed
timestamp: 2026-10-04T00:00:00Z
---

# The build plan, October 2026

**Graduation trigger — per section, not for the file:** a section graduates
into a `W-nn` when its own trigger fires (each names one) **or** a session is
about to build it. Nothing here is a commitment; each row stays in
[`BACKLOG.md`](../BACKLOG.md) under its class and points here.

**Why a plan and not three items.** SR-WORK-BACKLOG's own argument against
filing an unbuilt decision as a proposal is that it *reopens a ruling*. This
file reopens nothing: **the decision is the record's and is not restated; what
is written here is the build approach**, which the record never carried and
which was the thing a builder had to re-derive each time. The queue's length
stays a signal (SR-WORK-OPEN-QUEUE rule 3); three 🟢 rows that nobody is about
to pick would not be.

**Ruled the same day, straight into items** (named so the map is whole):
B-100 + B-146 + B-151 → W-253 ·
B-150 → W-254 ·
B-260 → W-255 ([compare](../compare/pii-regex-bound.compare.md)) ·
B-002/B-098, B-113/B-261 gate 2, B-103 → W-256.

**Every section inherits:** L2 (no new dependency without a record naming it),
L4 (pure functions of the bytes), L5 (offline), L10 (Node ships one bundle),
L12 (no value in engine code — tunables in consumer TOML, fixed values in
`constants.toml`).

---

## 1 · B-031 — a `--json` shape for the write verbs (`unbuilt`)

**The record.** [SR-CLI](../../records/0101_cli-surface.md) Consequences:
*"The write verbs have no `--json`, deliberately. `--json` is the read surface.
A machine-readable `add` … would need a shape for 'recorded, fetched, ingested,
and here is what left the index' — so it waits for a caller who needs it."*
Ruled 2026-10-04 (W-251 §4): **the shape is declared now, in SR-CLI, as
*declared, not shipped*; the build still waits for the caller.** A declared
shape is what stops the first caller inventing one.

**Today.** `fux add` prints `"{action:9s} {line}"` / `"  was …"` / `"  in
<list>"`, then stderr `fetching <url>`, then on a failed announced fetch
*"the line is written; the fetch failed: <reason>"* (exit 1); `remove` prints
dropped document and edge counts (`sources.py:971–1166`). `IngestReport`
(`ingest/run.py:104–140`) already carries `doc_count, changed_count,
reused_count, deleted_count, skipped[], warnings[], written_shards`. `correct
--json` exists but only on `--list`, a read path — the record's sentence holds.
**No caller exists:** `fux mcp` exposes `fux_search`, `fux_passage`,
`fux_related` only; `fux.api` excludes *"anything that writes"*; no agent
template parses `add` output.

**The declared shape** (SR-CLI, via W-245):

```json
{"entry": "<normalized>", "list": ".fux/sources/urls", "kind": "url|dir|file|types",
 "recorded": {"action": "added|updated|unchanged|excluded", "line": "...", "was": "..."|null},
 "fetched":  {"attempted": true, "ok": true, "reason": null}|null,
 "ingested": {"documents": n, "changed": n, "carried": n, "deleted": n, "shards_written": n,
              "skipped": [{"path": "...", "reason": "...", "class": "policy|unreadable"}]}|null}
```

Exit codes unchanged. `remove --json` reuses `recorded` + `ingested.deleted` +
`dropped_edges`.

**Trigger:** a `fux_add` MCP tool or an `api.add` is proposed in a record. Then:
**S–M, Sonnet** — `cli.py` (`--json` on `add`/`remove`), `sources.py::cmd_add/
cmd_remove`, `output_config.CLI_VERBS` rows, the `[cli.json.add]` resolution
(SR-OUTPUT d10's `default=None` trap at `cli.py:329–333`), an e2e test, and
SR-CLI's *three shapes* paragraph becomes four. L12: indent from `[json]
indent`.

## 2 · B-041 — fence-aware grammars for `.rst`, `.adoc`, `.org` (`unbuilt`)

**The record.** [SR-DECODE](../../records/0139_decode.md) d14 ⚠: *"`.rst`,
`.adoc` and `.org` keep their own regexes in `extract.py` and get no fence
handling. Their heading syntax is not Markdown's and neither is their
code-block convention. No decoder emits them."* The defect d14 fixed for
Markdown: a `# …` inside a fence was mined as a heading, published as a `§`
phrase, removed from the body, and opened a passage.

**Today.** `ingest/extract.py:90–119` — `_RST_RE` (underline adornment),
`_ADOC_RE` (`={1,6} `), `_ORG_RE` (`\*{1,6}[ \t]`), applied with
`finditer`/`sub` and **no fence state**. Markdown goes through
`decode/_markdown.py::headings/strip_headings` (CommonMark fences). **The refer
chunker uses the Markdown grammar for everything** (`refer/_chunk.py:50,181`),
so the three formats have no passage boundaries at all today. They are
`prose_types` (`constants.toml:108`): they reach no decoder and keep
frontmatter parsing. Node mirrors the prose set and **declines to `answer`
anything that is not prose** (`node/src/decode/registry.mjs:48`).

**Approach ruled (W-251 §4) — (a), one module both consumers import.** A line
walker per format beside `_markdown.py` (or a `decode/_prose.py`): rst literal
blocks and `code-block::` indented bodies; adoc `----` / `....` / `====`
delimited blocks; org `#+BEGIN_SRC` / `#+BEGIN_EXAMPLE … #+END_*`.
`extract.py::_headings_and_body` and `refer/_chunk.py` dispatch on extension;
a Node twin in `node/src/decode/markdown.mjs` keeps refer parity. **Rejected:
(b) decode the three to Markdown via built-in decoders** — they would leave
`prose_types`, so **Node would stop citing them**, frontmatter would stop being
parsed (`parse.py:30–36`), and a converter is (a)'s grammar plus a Markdown
re-serialisation; no L2 help exists either (docutils covers rst only; asciidoc
needs Ruby or a GPL port; org has nothing).

**Trigger:** the first corpus or golden seed document in one of the three
formats — SR-WORK-TESTDATA says the feature's input must exist in the data
before the feature is measured. Then: **M, Sonnet** (the rst indentation rule
is the only hard part). **DoD:** per-format fixture with a heading-shaped line
inside a code block that must *not* become a heading, phrase or passage start;
byte-identical index on this repository's `.md` corpus; Python and Node chunk
each fixture identically (`test_node_twins`); d14's ⚠ rewritten; the three
regexes deleted from `extract.py`.

## 3 · B-259 — display width is not `len()` (`ungated`)

**The record.** [SR-CLI](../../records/0101_cli-surface.md) d12 ⚠: *"Still
unguarded: display width ≠ `len()`. A path holding a CJK character or an emoji
counts as one per character and renders as two columns, so it can still wrap.
No corpus here has hit it and no test covers it."*

**Today.** `progress.py:134–157 _paint`: `room = self._width - len(line) - 2`,
truncation `clean[-(room-1):]`, `line = line[:self._width]`, `pad = " " *
max(0, self._last_len - len(line))` — four `len()`/slice sites.
`tests/test_progress.py:133–156, 215` assert `len(frame) <= 80`.

**Approach ruled (W-251 §4) — stdlib, no dependency.** `wcwidth` is MIT and
would pass L2, but it needs a record and is overkill:

```python
import unicodedata

def _cols(s: str) -> int:
    n = 0
    for ch in s:
        if unicodedata.combining(ch) or ch in ZERO_WIDTH:   # fixed set, constants.toml [progress]
            continue
        n += 2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1
    return n

def _tail(s: str, cols: int) -> str:
    """Longest suffix of `s` fitting `cols` columns, never splitting a cluster."""
    out, used = [], 0
    for ch in reversed(s):
        w = 0 if unicodedata.combining(ch) else (2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1)
        if used + w > cols:
            break
        out.append(ch); used += w
    return "".join(reversed(out))
```

Then `room = self._width - _cols(line) - 2`; `"…" + _tail(clean, room - 1)`; a
`_head` twin for `line[:self._width]`; `pad = " " * max(0, self._last_cols -
_cols(line))`. Emoji are mostly `W`; a ZWJ sequence counts each base as 2 —
over-counting only shortens, the safe direction.

**Trigger:** any session touching `progress.py`, or a corpus path with a
wide character. **S, Sonnet.** **Tests:** `detail = "docs/" + "日本語の文書"*20 +
"/x.md"` → every frame `_cols(frame) <= 80` and a plain-ASCII frame still
`len <= 80`; a `"🍕"*50` path; a combining-mark path (`"é"*50` decomposed) is
not over-shortened. SR-CLI's ⚠ paragraph rewritten. L4 is not in play (stderr,
TTY-gated — the record says so); L12 — the zero-width set is a fixed value.

## Rows that stay where they are, and why

- **B-055** (`ungated`) — the weak rule is ruled and gated via
  W-246; the strong rule (*a `component`
  record must own something*) is Arpit's (W-251 §3 #16).
- **B-262** (`unmeasured`) — cascade's gate needs golden tables and
  row-precise questions, and **no SR-WORK-TESTDATA row names tabular
  documents**; a T15 is the prerequisite (W-251 §4 #12).
- **B-006, B-013/B-014, B-099, B-147, B-162, B-154** — his (W-251 §3).
