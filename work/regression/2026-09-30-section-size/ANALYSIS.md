---
type: Analysis
description: "Why section records roughly double the committed index, why the ratio falls towards about 2x as the ladder grows, what the ladder does not exercise (jsonl, pdf, pptx, csv), and why U3 is not a way to avoid the size cost."
run: 2026-09-30-section-size
item: W-236
---

# Analysis: section-size

## 1 · Why the index about doubles

- **Each body or heading term in a split document is written once in the
  document record and again in every section that uses it.** A term spread
  across four sections is one posting in the doc record and four in the section
  plane. So the section plane is at least as large as the doc plane's body and
  heading postings, and larger when terms repeat across sections.
- **The doc plane holds more than postings:** `title`, `phrases`, `edges`,
  `sha`, `loc`, and the title and path fields. The section plane holds none of
  them (SR-SECTIONS decision 3). The two effects roughly cancel, which is why
  the ratio lands near 1×.
- **The ratio falls as the ladder grows** (+124 % at seed, +98 % at 10 000).
  The seed documents are the long ones (6.3 sections each), and the generated
  extension documents average about 4.

To reproduce one rung: `.venv/bin/python tools/section-size/measure.py --ladder ~/my_programs/fux-lab/corpora/golden --rungs rung-10000 --out /tmp/x.json`.

## 2 · What the ladder does not exercise

- **The ladder has no `.jsonl`, `.pdf`, `.pptx`, `.csv` or `.xlsx` files.**
  Those decoders emit one sibling heading per record, page or slide, and each
  sibling becomes a section. A 5 000-line `.jsonl` would write 5 000 section
  records. **This is not measured. What is known is the structural bound:**
  section records scale with headings, never with table rows (SR-SECTIONS
  decision 2), so a `.csv` stays one section.
- **The ladder has no `url:` sources.** SR-SECTIONS decision 7 covers them.

## 3 · Would U3 be smaller?

- U3 puts per-section tf maps inside the document record. It saves the section
  id (about 45 B per section with a `file:ext/…` parent) and the header line of
  each section shard, and it still pays for the same postings.
- **At rung-10000 that saves about 2 MB of the 25 MB added** (39 417 ids ×
  ~45 B). So U3 does not avoid U2's size cost. It gives up the separate plane,
  which is what keeps the default path byte-identical (SR-SECTIONS decision 4),
  in exchange for a few percent.
- **Not resolved:** git's delta compression over real history is not measured.
  zlib per shard (+79.6 %) is only a stand-in for a pack.

## 4 · Totality

**0 misses on every rung.** For every split document, the section records'
body and heading token counts add up exactly to what `extract.py` counts for
the whole document. SR-SECTIONS decision 3's invariant holds on this corpus,
so a `fux build` check of it (decision 6) would not fire on the ladder.
