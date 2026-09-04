---
type: OpenItem
id: W-112
title: "W-112 — the vector plane: fux embed, .fux/vectors/, --qvec, rank-space fusion — only on W-106 PASS"
description: "The agent runs a consumer-owned embedder; the int8 chunk vectors are pinned and committed like enrichment; fux ingest folds them into runtime only; fux ask --qvec takes the caller's query vector and fuses with BM25F by RRF. Fux never computes a vector. Blocked on W-106's verdict and on W-109's RRF."
status: open
lane: agent
timestamp: 2026-09-04T00:00:00Z
---

# W-112 — the vector plane

**Model: Opus.** New committed plane, new laws surface (L2/L5), new receipt
fields, and a gate.

## The spec this implements

[`../proposals/search-v3.md`](../proposals/search-v3.md) §5 and §8 (W-112).
**Does not start until [W-106](W-106-vector-gate.md) files PASS** and the
compare doc (*vectors* vs *doc2query*) has Arpit's verdict.

## Definition of done

- [ ] `fux setup --embedder local-py|local-js` writes
      `.fux/embedders/<name>.{py,js}` once (templates in
      `src/fux/templates/`); contract: stdin chunk lines → stdout
      `{chunk, scale, v}`; `--identify`. Node template uses
      `@huggingface/transformers`, pinned repo/revision/dtype.
- [ ] `fux embed --plan [TARGET]` / `--check [TARGET]`, mirroring
      `enrich.py` (sha-keyed, scope by `embed=true` on a dirs/urls line,
      orphan detection, `filtered` count, exact `TARGET`). `--check`
      refuses: missing keys, sha mismatch, `chunks` ≠ `refer/_chunk`, mixed
      models in a scope, `dim` mismatch, values outside `[-128, 127]`.
- [ ] `.fux/vectors/<sha>.jsonl`, `fux.vectors.v1`, schema file beside the
      code; declared **committed** in ADR-DOTFUX's table; `fux doctor` names
      orphans and the hashed-meta rule.
- [ ] `fux ingest` folds vectors into `.fux/runtime/vectors/` (derived;
      manifest + schema bump); **`.fux/index/` byte-identical with or
      without vectors** — asserted by a test.
- [ ] `fux ask|find|answer --qvec <file>` and MCP `qvec`: int8 dot with
      int32 accumulator, max-sim per document, RRF with the BM25F ranking via
      W-109's `fuse.py`; absent `--qvec` ⇒ today's bytes (test).
- [ ] Receipt: embedder `--identify` + query-vector sha; `fux verify`
      returns `unverifiable` on embedder mismatch.
- [ ] `EMBED-SKILL.md` mirroring `fux-enrich`'s discipline (plan yourself;
      ask before bulk; re-plan before write; never add `embed=true`).
- [ ] Node reader (W-107) gains the lane in the same release or the
      version policy says it does not.
- [ ] Gate: W-106's bar re-run on the shipped path; differential law with
      and without `--qvec`; two-ISA discordant count for query vectors.
- [ ] ADR-VECTORS (new), ADR-DOTFUX, ADR-INGEST, ADR-ASK, ADR-PROVENANCE
      amended; ownership twin; CHANGELOG; `IMPLEMENTATION.md`; this file to
      `archive/open/`.

## Blockers

- **W-106 PASS** — hard.
- W-109 (`fuse.py`, ADR-EXPAND).
- `arpit`: the compare-doc verdict; the hashed-meta default.

## Hazards

- 🔴 L2/L5: embedding inversion is a *demonstrated* risk on hashed records
  (CHANGELOG 0.34.0, P5). Hashed sources get no vectors unless the line
  says `embed=true` — and the record says why.
- 🔴 Committed size: 23 % index growth was measured when the old lane's
  vectors were committed. Opt-in per scope; report the size in `--check`.
- Determinism is *reuse of committed bytes*; the query vector differs per
  machine — the receipt carries the embedder identity for that reason.
- Never import anything in `src/fux/` for this; the embedder is consumer
  code and stays outside the import fence.

## Out of scope

Fux computing any vector. A bundled model. Score-space fusion.
