---
type: Pre-Registration
description: "W-236 Part A step 2: how many section records SR-SECTIONS would add to the committed index, and how many bytes, on the golden ladder up to rung-10000. The bar is stated before any number exists: SR-WORK-SCALE and SR-INDEX-LIFECYCLE set no size number, so only two external commit limits can fail it, and the growth ratio is reported for Arpit, not graded."
run: 2026-09-30-section-size
item: W-236
status: frozen
filed: 2026-09-30
---

# PRE-REGISTRATION — W-236 section records, the size measurement

🔴 **FROZEN. Written before the tool ran on any rung**
([SR-RS](../../../records/0133_predictions.md) decision 10b). Nothing is built.
The measurement only projects what [SR-SECTIONS](../../../records/0161_sections.md)
would write.

## 1 · What is measured

For each rung of `~/my_programs/fux-lab/corpora/golden/` (seed, 100, 200, 500,
1 000, 2 000, 5 000, 10 000), with [`tools/section-size/measure.py`](../../../tools/section-size/measure.py):

- **documents**: the records in the rung's committed index;
- **multi-section documents**: documents SR-SECTIONS decision 2's rule splits
  into two or more index sections. Only these get section records;
- **section records**: their total, and sections per multi-section document
  (mean, p50, p90, max);
- **section-plane bytes**: the canonical encoding of every section record, plus
  one header line per non-empty section shard, sharded by the parent's id
  (decision 4), and the added `nsec` property on each multi-section document;
- **doc-plane bytes**: the rung's committed `.fux/index/??.jsonl`, summed exactly
  (not `du`);
- **the largest single file** in either plane;
- **zlib level 6 bytes** of both planes, as a stand-in for git's pack cost
  (descriptive only);
- **totality**: documents whose section token counts do not sum to the
  document's own body + heading token counts (decision 3's invariant).

It reads the rung's files, its committed index and the chunker's grammar. It
writes nothing except its own JSON under `evidence/`.

## 2 · The bar

**Neither record the item names sets a size number.** SR-WORK-SCALE decision 1
says a feature *holds up at 10 000 documents or it does not*, and decision 12
says to judge that by reasoning. SR-INDEX-LIFECYCLE says *committed index size
is measured, never gated*, and that a size promise comes back only as a new
prediction with a new id. **An agent inventing a growth-ratio threshold here
would be a threshold no record authorises**, so none is set.

What CAN fail, at `rung-10000`, is whether the index can still be committed to
an ordinary git host. These are GitHub's published limits
(<https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-large-files-on-github>):

| gate | FAIL if, at rung-10000 |
|---|---|
| **H1** — a single file | any projected committed file (doc shard or section shard) is larger than **50 MiB**, where Git starts warning (GitHub blocks at 100 MiB) |
| **H2** — the whole index | doc plane + section plane is larger than **1 GB**, GitHub's *"ideally less than 1 GB"* |

- **FAIL on either**: SR-SECTIONS does not hold up at 10 000, W-236 stops, and
  U3 goes to Arpit (the compare doc's reopen-trigger).
- **PASS on both**: the growth ratio (section plane ÷ doc plane) and the
  sections-per-document distribution are **reported, not graded**. Whether a
  given ratio is too much is Arpit's call, and it is put to him as that.
- ⚠ Rungs below 10 000 are reported for the curve and gate nothing.

## 3 · Classification

`blind`. The tool reads documents and the committed index. No question, no key,
no score and no per-query row is involved.
