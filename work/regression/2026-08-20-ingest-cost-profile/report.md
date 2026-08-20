# 2026-08-20 — where a full ingest spends its time

**A cost measurement, not a gate.** It pre-registers no threshold and rules on
no prediction. Its purpose is narrow and was written down in advance: it is the
evidence [ADR-INGEST](../../../docs/adr/0007_ingest.md)'s own veto condition
demanded before decision 1 could be reopened — *"full re-extraction becomes the
measured bottleneck at scale"*.

> **It is explicitly not R5.** R5 is *a 20-document commit re-indexes in under
> a second via the hook*, and prediction runs are held pending Arpit's word
> (2026-08-20, [W-61](../../open/W-61-maintenance-measurement.md)). Nothing
> here is a pass/fail call on R5, and the numbers below are ingest wall-times,
> not hook-path commit times.

- **Version:** `fux` from source at `0.33.0`, this working tree, Python 3.11,
  macOS 25.3 (local device — [`../../MACHINE.md`](../../MACHINE.md)).
- **Corpora:** synthetic, 1 000 and 5 000 documents. Each document is
  frontmatter + a heading + 40 distinct terms + one outbound link, so edge
  resolution has real work to do and vocabulary does not degenerate.
- **Reproduce:** `evidence/profile.sh /tmp/fux-cost /path/to/fux` — offline, no
  lab, about two minutes. Raw output: [`evidence/profile.txt`](evidence/profile.txt).

---

## 1 · The profile

`cProfile`, cumulative, over one **full** ingest.

| corpus | total | `extract_fields` | `_fuxvec_code` | share in the embedding |
|---|---|---|---|---|
| 1 000 docs | 4.38 s | 4.03 s | 3.996 s | **91.2 %** |
| 5 000 docs | 23.30 s | 21.58 s | 21.41 s | **91.9 %** |

Everything else together is under 9 %: `write_index` is 0.17 s at 1 000 docs
and 0.82 s at 5 000, and parse plus edge resolution do not reach the top twelve
frames at either size.

**The cost is one function.** `_fuxvec_code` calls the FuxVec model's `embed`,
and `embed` plus its tokenizer is the whole of it. That matters for the fix:
the expensive step is a **pure function of one document's own bytes**, which is
the property that makes it safe to carry forward.

## 2 · Full versus delta, and byte-identity

| corpus | full | delta | speedup | documents carried forward | identical bytes |
|---|---|---|---|---|---|
| 1 000 docs | 2.879 s | 0.127 s | **22.7×** | 1 000 | **yes** |
| 5 000 docs | 15.733 s | 0.596 s | **26.4×** | 5 000 | **yes** |

The full-run column is faster than the profiled column because `cProfile` adds
its own overhead; compare within a row, never across the two tables.

**Byte-identity is the claim that matters**, and it is asserted here on the
shard digests, not inferred. The unit suite asserts the same property after an
edit, an addition and a deletion, each against the full run's own output
([`tests/ingest/test_delta.py`](../../../tests/ingest/test_delta.py)).

## 3 · What this does not say

- **Nothing about the hook path.** These are library calls. The hook also runs
  the derived build, and git's own commit work sits around both.
- **Nothing about a real corpus.** Synthetic documents with 40 distinct terms
  each are uniform in a way real documentation is not; the *share* attributable
  to the embedding is the robust finding, the absolute seconds are not.
- **Nothing about corpora above 5 000 documents.** The residual O(corpus) half
  — walk, parse, edges, write — is what will dominate eventually, and it has
  not been measured where it does.
