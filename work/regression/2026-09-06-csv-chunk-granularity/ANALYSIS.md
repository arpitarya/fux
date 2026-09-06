# ANALYSIS — what this run actually establishes, and what it does not

## What it establishes

**Per-row citation beats banded citation on ambiguous queries, and the margin
is large** — `hit@1` 0.875 against 0.229 and 0.292. The effect is not an
artifact of passage length: the control holds candidate size constant and the
correct row still wins 42/48.

**Bytes returned fall 6.4×** (6 094 → 946) for a better answer, which matters
more than the ratio suggests — that is context an agent does not have to read.

## What it does NOT establish

- **It supplies no delta.** `informed` run: one author wrote the generator and
  the queries. Under RUN-CLASSIFICATION that is reclassified, never banned, and
  never a delta.
- **One corpus, and a synthetic one.** Generated ops-flavoured rows, not a real
  spreadsheet. "Never ship a ranking change off a single synthetic corpus" is
  the standing rule, and this change was shipped on a **ruling**, not on this
  evidence clearing a bar. ADR-TABULAR's veto condition says so.
- **It says nothing about prose.** Only tables changed.
- **Latency is one surface.** §2.

## Three harness defects, and how each was caught

TEST-PLAN §3 says to hand-verify one known-good hit before believing a
surprising number. It earned its place three times here.

1. **`hit@1 = 0.000` on every arm.** The matcher compared a raw CSV line
   against the Markdown table row the decoder emits. Looked exactly like "chunk
   size does not matter".
2. **Five silently broken pairs.** Two queries could plant into the same row of
   the same file; the later overwrote the earlier. Would have quietly depressed
   every arm equally.
3. **Five more unfindable — and this one was not a harness bug.**
   `csv.MAX_ROWS = 500` had dropped them. That became the second half of
   ADR-TABULAR, and it is the finding with the longest reach: it was true of
   every CSV and XLSX in every corpus since the decoders shipped.

**The pattern worth keeping:** two of the three presented as a *quality*
result. A harness bug and a real finding are indistinguishable from the number
alone.

## The one that nearly got away

Query set A — a unique token in the target row — is the experiment anyone would
write first, and every arm scores 1.000 on it. The finding only exists because
a second, harder set was written. When a chunking change shows no effect, the
first thing to check is whether the queries can even see one.
