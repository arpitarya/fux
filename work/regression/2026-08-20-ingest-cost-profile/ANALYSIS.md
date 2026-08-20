# ANALYSIS — 2026-08-20, the ingest cost profile

## The diagnosis

**One function is 92 % of a full ingest**, at both corpus sizes, and it is the
one step in the pipeline that cannot depend on anything but the document in
front of it. That combination is what makes the fix small.

`_fuxvec_code` → `embed` is a pure function of `(title, body)`. The committed
record's `sha` pins those bytes. So a record whose `sha` is unchanged already
contains the correct answer, and recomputing it is work with a known result.

Edges are the opposite: corpus-wide, and a new document can resolve a link that
dangled yesterday. ADR-INGEST was right to refuse to skip them, and the original
decision's error was only that it bundled the two together.

## Changes made, in the same change as this run

**1. Decision 1b in [ADR-INGEST](../../../docs/adr/0007_ingest.md) — carry
extraction forward, re-resolve edges always.** Gated on three conditions
together: the content `sha` matches, the record is `file:` with `meta: plain`,
and the shard header still equals `store.HEADER`.

Repro:

```bash
fux ingest --full >/dev/null && sha1sum .fux/index/*.jsonl > /tmp/f
fux ingest        >/dev/null && sha1sum .fux/index/*.jsonl > /tmp/d
diff /tmp/f /tmp/d && echo IDENTICAL
```

**2. `fux ingest --full`** — re-extract regardless. It exists because two of
this change's consequences need an escape hatch, not because anyone should
routinely pass it.

**3. The summary line now reports what was carried forward**, so a delta run is
visible rather than inferred:

```console
$ fux ingest
ingested 3 docs (1 changed, 2 carried forward), 2 skipped, 1 shards written
```

## What this costs — stated, not buried

**Term-hash collision detection is now complete only on a full run.** The
tracker sees the raw terms of documents it extracted; a carried-forward document
contributes hashes it cannot un-hash. A collision between a changed document's
term and an unchanged document's term is therefore undetected until `--full`
runs. This narrows archived ADR-0008's "fails loudly" guarantee, and it is
recorded in ADR-INGEST's consequences rather than left to be discovered.

Repro of the complete check:

```bash
fux ingest --full    # the only run that hashes every term in the corpus
```

**A newly available embedding bundle does not retro-fit `code`.** An index
built without the FuxVec data file keeps `code`-less records for every document
that has not changed since, even after the bundle arrives. `--full` is again
the fix.

## Unresolved

- **The residual O(corpus) half is unmeasured where it matters.** Walk, parse,
  edges and write are now the whole cost of an unchanged corpus, and at 5 000
  documents that is 0.60 s. Whether it stays acceptable at 10⁵–10⁶ is exactly
  M6's question ([W-26](../../open/W-26-m6-scale-t2.md)) and is not answered
  here.
- **The hook path is unmeasured, deliberately.** That is R5, and prediction
  runs are held ([W-61](../../open/W-61-maintenance-measurement.md)). This run
  makes R5 *reachable* at corpus sizes where it previously could not have been;
  it does not call it.
- **Synthetic corpora only.** The 92 % share should be re-checked on the RFC
  corpus before anyone treats the absolute seconds as representative.
