---
type: Handoff
name: W-254
description: "A leading YAML frontmatter block becomes its own passage unit in the refer chunker — never folded into the first section, line ranges exact, still quotable, still indexed at document level. Closes SR-ANSWER's 'stripping it is chunk.py's call' and backlog B-150. Ruled by delegation 2026-10-04 (W-251 §4). Ratified, NOT built."
item: W-254
filed: 2026-10-04
ball: agent
---

# W-254 — the frontmatter block is its own passage

**✅ CLOSED 2026-10-04 — built as ruled** (Claude Code; Sonnet built, Opus 5.5 reviewed):
- `refer/_chunk.chunk()` takes a required `frontmatter: bool`; when true and `fux.frontmatter.parse` finds a block, it is passage 0 (heading `""`, level 0, `L1-Ln`) and never reaches `_fold`; the body is chunked alone and shifted, so its passages equal the no-frontmatter case. Callers: `refer()` passes it for an undecoded `file:` document only; `rerank.boost` (raw file text) always; `inspect` facts/xray when not generated and not `url:`; `enrich._chunk_count` never (committed enrichment unit counts unchanged — a judgement call). Node twin in `node/src/refer/chunk.mjs`, `answer.mjs`, `rerank.mjs`.
- Tests: six chunker tests (unit, ranges, no fold, body equality, totality, decoded `---` not split, unclosed fence) and rerank veto 2 (membership unchanged).
- **Parity, checked by hand** because the differential arm never compares `answer` passages: on a 42-document frontmattered corpus, Python and Node `answer --json` agree on 11 of 12 queries, and the twelfth differs only deep in the passage tail. HEAD shows the same 11 of 12, a pre-existing float-ULP tie order (`…473` vs `…472`), not this change.
- Live successors: [SR-CHUNKING](../../records/0151_chunking.md) d7, [SR-ANSWER](../../records/0105_answer.md) Consequences, [SR-REFER](../../records/0127_refer-plane.md) d23.

**Model:** Claude Code, **Sonnet** — a small change to a pure function with a
totality invariant already tested, plus its Node twin. **Ratified 2026-10-04 by
delegation ([W-251](../../work/open/W-251-backlog-audit-rulings.md) §4, row B-150), not built.**

## The ruling

SR-ANSWER's Consequences say the quoted passage *"is a genuine verbatim span,
frontmatter included — but it is a real readability cost … Stripping it is
`chunk.py`'s call, not this record's."* Backlog B-150 carried that for three
weeks. The ruling, for SR-CHUNKING (a new decision):

> **A leading frontmatter block is a UNIT.** It is its own passage with heading
> `""` and **never folds forward** into the first section. It is detected with
> `frontmatter.parse` — shared with ingest, never reimplemented — and **only on
> the undecoded path**, because decoded Markdown may legitimately begin with
> `---` (an HTML `<hr>`; `ingest/parse.py:30–35` says so for ingest). The body's
> first section starts at the line `frontmatter.parse` reports; line ranges stay
> exact; **every byte still lands in exactly one passage**; the block stays
> quotable (it is a passage) and stays indexed at document level (W-205's
> `title`/`ctx` from meta is ingest-side and untouched).

**Why *unit* and not *strip*.** The chunker's own rule (`refer/_chunk.py:119–122`):
*"a preamble is content, and dropping it silently is how the one sentence that
answers the question disappears"* — a `status: retired` line in frontmatter is
exactly that sentence. Stripping also breaks totality. Today `_fold`
(`_chunk.py:245+`) rides the short preamble forward into the deeper `# Title`
section, so d16's rescoring hands the first passage extra `tf` from `title:` and
`description:` words — the readability cost SR-ANSWER names is also a scoring
tilt. Making the block its own unit removes both without inventing anything.

**Laws.** L3: a passage is derived at query time and never written — nothing
committed moves. L4: a pure function of the bytes. L12: no new value.

## Definition of done

1. `src/fux/refer/_chunk.py`: a leading frontmatter block (via
   `fux.frontmatter.parse`) is passage 0 with heading `""`, level 0, exact
   `L1-Ln`; `_fold` never folds it forward; totality (`every byte in exactly one
   passage`) still holds and its test still passes.
2. The flag that says *undecoded path* reaches the chunker from
   `refer/__init__.py` (the decode seam, SR-REFER d23): decoded documents are
   chunked exactly as today.
3. Node twin in the refer chunker under `node/src/` so the arm's `answer` lane
   stays byte-equal; `tests/test_node_twins.py` green.
4. Callers audited: `inspect/facts.py`, `inspect/xray.py` and `query/rerank.py`
   call `chunk()`. **Rerank veto 2 (document membership unchanged) must hold** —
   one more passage per frontmattered document changes passage counts, never
   membership; add the test that says so.
5. Tests: a frontmattered Markdown fixture → passage 0 is the block, passage 1
   starts at the body's first line, line ranges exact; an identical body
   without frontmatter → identical passages after the first; a decoded
   document beginning with `---` is **not** split.
6. Records, same change, `sr-hash.py --write`: SR-CHUNKING (the new decision,
   numbered next); SR-ANSWER Consequences (the *"`chunk.py`'s call"* sentence →
   *ruled by SR-CHUNKING d<n>, W-254*); SR-REFER d23 gains one clause if the
   seam carries the flag.
7. Both suites whole; a WORKLOG entry; `CHANGELOG.md` *Changed*.

## Out of scope

- Any change to what ingest indexes from frontmatter (W-205, closed).
- Stripping, hiding or re-ranking the block.

## Hazards

- ⚠ One extra, usually unhelpful passage per frontmattered document. d16's
  rescoring could seat a frontmatter passage for an identifier query — which is
  arguably correct (W-205 wanted identifiers reachable) and is the one thing to
  watch in the first graded run after this lands.
- ⚠ Detect on the undecoded path only. Splitting a decoded document on a
  leading `---` is the defect `ingest/parse.py` already refuses.
