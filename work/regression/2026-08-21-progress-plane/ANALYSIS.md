---
type: Analysis
name: progress-plane-analysis
description: What the W-64 capture showed, including two phases that report a bookend rather than a live count and one that correctly painted nothing.
status: complete
timestamp: 2026-08-21T00:00:00Z
---

# What the capture showed

**This run is a surface capture, not a measurement.** It grounds
[ADR-CLI](../../../docs/adr/0002_cli-surface.md) decision 9 in real output. No
threshold was pre-registered and none is adjudicated here.

## The invariant held, and it is now a test

stdout was byte-identical with the bar on and off, for both write verbs. That
is asserted per-verb in
[`tests_e2e/test_progress_surface.py`](../../../tests_e2e/test_progress_surface.py), so it is a
property rather than an observation.

## Three findings worth recording

**1. Three phases report a bookend, not a live count — say so rather than
interpolate.** `write` (`store.write_index`), `codes` (`dense.build_codes`) and
`graph` (`graph_plane.build_plane`) are single calls with no per-item hook, so
their bar jumps 0 → total when the call returns. The alternative — inventing
intermediate positions from a timer — is exactly the wall-clock decoration the
"counts, not clocks" rule refuses. **Improvement, if it ever matters:** give
`write_index` an optional per-shard callback; it already loops `by_shard`.
Not done here because the capture shows those three phases are fast relative
to `extract`, which is the one profiled at 92 % of a full ingest.

```bash
# repro: watch which phases step and which jump
sh evidence/fixture.sh /tmp/progress-demo && cd /tmp/progress-demo
python -m fux.cli ingest --progress 2>&1 >/dev/null | tr '\r' '\n' | grep -c '^  write'
```

**2. `graph` painted nothing, and that is the threshold working.** The fixture's
documents link to nothing, so the phase total was 0 — under the ~200 count
threshold. A corpus with real cross-links will paint it. **This is a gap in the
fixture, not in the feature**, and it is named here rather than left for a
reader to notice the missing row: the capture does not exercise that phase's
painting path. `tests/test_progress.py` covers the threshold behaviour
directly.

**3. A phase whose total is not documents must name its unit — found and
fixed in this run.** The first capture read `write [████] 252/252` directly
under `edges [████] 1203/1203`, and a 4× drop between adjacent lines reads as
loss rather than as a change of unit. `phase()` now takes a `unit`, and the
three affected phases pass one: `write`/`read` count `shards` (capped at 256
by the shard addressing, not by the corpus) and `postings` counts `terms`.
Re-captured; `evidence/` holds the second run.

**4. A wrapped line is an un-erasable line — found after the capture, fixed
before close.** `\r` returns to the start of the *terminal* line, not of what
was written, so any painted line wider than the terminal leaves a tail that no
subsequent `\r` can take back — and the `extract` phase appends a document
path, which is unbounded. The DoD's "Ctrl-C leaves no partial line" was
therefore true only for short paths. Lines are now capped at **80 columns**,
with the detail truncated **from the left** (the tail names the document; the
leading directories do not) and marked with a leading `…`. Non-printable
characters are stripped from the detail in the same pass: a `\n` or `\x1b` in
a filename is legal on POSIX and would have split one repaint into several.
The capture's widest line measures **60 columns**.

```bash
# repro: the guarantee, at a path length that used to break it
python -m pytest tests/test_progress.py -k 'wrap or truncation or control' -q
```

**5. The invariant test was itself nearly vacuous when W-63 arrived — caught
on the way in, 2026-08-21.** W-63 added `add`/`remove`/`update` to the
progress plane, and the parametrized stdout check still named only `ingest`
and `build`. Extending it exposed two ways the extension could have passed
while testing nothing:

- **`remove docs` empties the corpus**, so every phase total falls under the
  threshold and *neither* arm paints. Comparing two silent runs passes and
  proves nothing. `remove` now takes a single document, leaving 1 202 — a real
  bar to compare.
- **The mutating verbs are not each other's inverse.** `add` refuses to
  un-exclude by design (`!` subtracts and nothing adds back), so an
  `add`-as-reset for `remove` fails, and a second `add docs` reports
  `unchanged` and skips the ingest. Each arm now rewrites
  `.fux/sources/dirs` directly to a known state instead.

Two guards were added rather than just the fix: `test_every_progress_verb_is_
covered` asserts the parametrize list equals `cli.py`'s `_PROGRESS_COMMANDS`,
so a sixth write verb cannot skip the invariant by being forgotten; and each
arm now asserts the bar **actually painted**, so a verb that silently stops
inheriting the plane fails instead of passing quietly. **This is the same
defect class the W-63 capture found four of** — a check that does something
defensible and reports something false.

## Unresolved

**Nothing about behaviour under a real 100 000-document commit-path run.** R5
measured 44.4 s of silence at that size
([R5-HOOK](../2026-08-20-r5-hook-latency/VERDICT.md)), which is what motivated
this feature — but this capture is at 1 203 documents and says nothing about
whether repaint cost is material at 100k. The repaint is one `write` + one
`flush` per document, which is not free.
[W-26](../../open/W-26-m6-scale-t2.md) is the item that runs at that scale and
is where it should be checked, not asserted here.
