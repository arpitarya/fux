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
**Does not start until [W-106](../../archive/open/W-106-vector-gate.md) files PASS** and the
compare doc (*vectors* vs *doc2query*) has Arpit's verdict.

🔴 **W-106 closed 2026-09-12 WITHOUT a PASS, and it cannot produce one.** Its
retrieval half never tested DENSE-CHUNK's frozen bar — the playground's index
was unreadable in 2026-09-05, and the golden ladder's questions carry **no rank
contract**, by design, because their key is sealed. **A corpus that can carry
that bar does not exist**, so *"until W-106 files PASS"* is not a wait, it is a
dependency on a new instrument.

✅ **What W-106 did settle, and it shrinks this item's determinism problem.**
The two-architecture arm found **zero** divergence — one embedder build on
arm64 and on x86-64, cosine 1.000000, 119/119 and 124/124 int8 vectors
byte-identical, 0/124 orderings discordant
([the run](../regression/2026-09-12-vector-gate-crossarch/report.md)). Against
2026-09-05's two-**implementation** result (0 of 125 identical, 41/50
discordant), **the variable is the implementation, not the machine**:

- **The determinism claim this item has to make is *"same embedder build"***,
  not *"same clone + same build + same CPU"*.
- ⚠ **It is still a strong claim.** A committed vector remains an artefact of
  one build, and this item proposes committing one.
- ⚠ **Native x86-64 is unmeasured** — the x86 arm ran under Rosetta, where the
  kernels see no AVX-512. Do not quote 0/124 for a Linux/x86 CI runner.

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
      code; declared **committed** in SR-DOTFUX's table; `fux doctor` names
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
- [ ] SR-VECTORS (new), SR-DOTFUX, SR-INGEST, SR-ASK, SR-PROVENANCE
      amended; ownership twin; CHANGELOG; `IMPLEMENTATION.md`; this file to
      `archive/open/`.

## Blockers

- **W-106 PASS** — hard.
- W-109 (`fuse.py`, SR-EXPAND).
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

## From OPEN-WORK (moved 2026-09-11)

*Moved here verbatim when OPEN-WORK became one-to-two-line rows (Arpit, 2026-09-11). Links are rewritten for this directory.*

*This is what the queue said at the move. Re-derive it before believing it (OPEN-WORK rule 4).*

- 🟠 **Search v3 — what is left of it: W-107 Phases 1–4, then W-112.** ·
  *(spec: [`proposals/search-v3.md`](../proposals/search-v3.md) §8 · one detail
  file each under [`open/`](README.md))* · **Opus** executes, in Arpit's
  ratified order: **W-107 Phases 1–4** → **W-112**. `ratified: 2026-09-05`
  - **[W-112](W-112-vector-plane.md)** · `arpit` · *(**SR-VECTORS** new · SR-DOTFUX · SR-INGEST · SR-ASK · SR-PROVENANCE)* · the vector plane — `fux embed`, pinned `.fux/vectors/`, `--qvec`, rank-space fusion; fux never computes a vector. 🔴 **Blocked on three things:** a corpus — **under [SR-WORK-ENVIRONMENTS](../../records/0052_WORK-environments.md) the golden ladder in fux-lab (W-136)**, a re-run gate, and a compare doc Arpit rules on **once it is written** (not yet — nothing to decide today). ⚠ **The determinism claim the design can actually make is *"same clone + same embedder build"*, never *"same model"*** — W-106's `0 of 125` is why. `filed: 2026-09-04`
