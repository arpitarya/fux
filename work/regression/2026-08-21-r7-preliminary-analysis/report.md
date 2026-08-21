# 2026-08-21 — R7: a preliminary read, not a pre-registered measurement

**This is not a VERDICT.** No pre-registration was written or committed for
R7, and the run PRIORITY.md's P3 item describes (a real 100 000-document
corpus built fresh in `fux-lab`, 30 re-ingest cycles) never happened. What
follows is Arpit's call, made on the strength of a smaller, honest analysis,
to close R7 out now rather than spend the ~1–2 hours a full pre-registered
run would cost. The reasoning is filed here so the call is auditable, exactly
as if it had been a measurement — it is just explicitly labelled as what it
is: **post-hoc analysis**, per CLAUDE.md's rule that post-hoc reasoning stays
out of a verdict's clothing.

## The question R7 was meant to answer

`work/OPEN-WORK.md:63` / `work/open/W-26-m6-scale-t2.md:43`: **committed index
density at 100 000 documents ≤ 250 MB, git-packed.** (R7's second half, "tier-
auto correct," cannot be measured at all yet — no T2 tier exists; that half is
[W-26](../../open/W-26-m6-scale-t2.md)'s own build, not this analysis's
concern.)

## What was actually done

Two measurements, both against **this repo's own already-committed
`.fux/index/`** — 345 real documents, real prose and code docs, not a
synthetic corpus — because it was available for free and required no new
environment:

1. **Per-field byte composition**, to find out what's actually driving size
   before guessing —
   [`evidence/byte_breakdown.py`](evidence/byte_breakdown.py) /
   [`evidence/byte_breakdown.out`](evidence/byte_breakdown.out).
2. **Real git-pack compression**, not an assumed ratio — copy `.fux/index/`
   into an isolated scratch repo (so the number is about the index alone, not
   the source corpus it indexes), commit, `git gc --aggressive`, measure the
   actual pack file —
   [`evidence/pack_compression.sh`](evidence/pack_compression.sh) /
   [`evidence/pack_compression.out`](evidence/pack_compression.out).

## The numbers

| quantity | value |
|---|---|
| documents measured | 345 |
| raw bytes (working tree) | 4 123 667 |
| raw bytes/doc | 11 953 |
| `terms` (postings) share of raw bytes | **91.3 %** (10 874 B/doc) |
| `code` (dense vector) share of raw bytes | 0.4 % (45 B/doc) |
| measured git-pack compression | **2.429×** |
| packed bytes/doc (raw ÷ ratio) | 4 922 |
| **budget per doc at 100k for 250 MB** | 2 500 |
| **compression ratio needed to hit budget** | 4.781× |
| **shortfall** (needed ÷ achieved) | **1.968×** |
| **linear projection @ 100 000 docs, packed** | **≈ 470 MB** |

## The finding that changes the question

The 250 MB threshold comes from `work/paper/the-fux-index-paper.md`'s §5 size
model, which assumes **BIC-encoded postings, a minimal-perfect-hash
dictionary, and front-coding** — the format `ADR-POSTINGS`
(`docs/adr/0013_postings.md`) specifies and whose status is **⏳ proposed —
not built**. What is actually committed today is **plain JSON**: each
posting is a literal `"<16-hex-char hash>": [freq, freq]` pair inside a dict,
compressed only by git's generic delta+zlib packing. The measured 2.429× is
what git's general-purpose compressor does to that plain format; it is not a
measurement of the paper's designed encoding, because that encoding does not
exist in the tree yet.

Two honest readings follow, and only one closes R7 today:

- **Testing today's plain-JSON format** — which is what any run against the
  current tree would measure — misses budget by ~2× on real data, extrapolated
  linearly to 100k docs.
- **Testing the paper's designed BIC/MPH encoding** — the thing the threshold
  was actually written for — cannot be measured at all without building it
  first, which is implementation work, not a benchmark run.
