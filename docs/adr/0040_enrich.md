---
type: ADR
name: ADR-ENRICH
title: "ADR-ENRICH (0040) — enrichment as an agent skill, not an API call"
description: "`fux enrich` plans and validates; a coding agent generates. Fux never calls a model, so L1, L4 and the $0 law are held rather than bracketed — and partial coverage is designed for, because sha-keying makes it the steady state."
status: proposed
timestamp: 2026-08-23T00:00:00Z
---

# ADR-ENRICH: enrichment as an agent skill

- **Name:** `ADR-ENRICH` — cite this everywhere; never cite the number
- **Status:** proposed
- **Date:** 2026-08-23
- **Feature:** document enrichment — W-76 Phase 8
- **Owns:** `src/fux/enrich.py`, `src/fux/templates/agents/ENRICH-SKILL.md`
- **Laws:** **L1 and L4 HELD** (see decision 1); L3 restated with a wider input

> **Supersedes the shape of [ADR-ENRICHED](0017_enriched-mode.md)'s
> generation path.** That record ratified the *contract* — pinned output,
> separate command, graded below deterministic signal — and explicitly did not
> authorise a build. What changes here is **who runs the model**.

> ## Pointer added 2026-08-25 — who may author an enrichment, when it is being MEASURED
>
> **This record governs how enrichment is generated and pinned, and it stays
> silent on who may have read the evaluation set. That silence is deliberate
> and now has an address.** `fux enrich` cannot enforce authorship — fux never
> calls a model, so the author is outside the program — which makes it a
> **measurement-protocol** rule, and it lives in
> [ADR-RS](0036_predictions.md) decisions 11-15 (ruled by Arpit 2026-08-25,
> **W-78** (closed 2026-08-25, retired to `archive/open/`; named, not cited)
> ruling 2).
>
> **What it means for anyone writing enrichment.** Nothing changes about
> *generating* it. What changes is that a **run which measures** it declares
> whether the enrichment's author could reach the evaluation queries — `blind`
> or `informed` — and an informed run never supplies a delta. This is not a
> restriction on enrichment; it is a restriction on what a number about
> enrichment may claim.

## 1 · Examples

```console
$ fux enrich --plan
scope docs/adr (enrich=true)
  docs/adr/0012_ranking.md      sha 3f8a1c2d9b04   9 chunks   MISSING
  docs/adr/0031_maintenance.md  sha 9b2e04f1a733   6 chunks   STALE (was 7c1d4e02b918)

-> 2 documents, 15 chunks
   write each to .fux/enrich/<sha>.md
   invoke the `fux-enrich` skill in your coding agent to generate them

$ fux enrich --check
enrichment: 1 scope(s) declared
  docs/adr                     41/41  ok
```

**The mechanism, demonstrated on the fixture repo (2026-08-23):** a query for
*"idempotency circuit breaker"* — words appearing **only in the enrichment**,
nowhere in the document — returns the document. Edit the document by one line
and the same query returns nothing, because the enrichment no longer matches
its sha.

## 2 · Context

Arpit's ruling, 2026-08-23:

> *"Enrich should work like a skill in the chat — that way we don't need to
> integrate the API in the code and AI coding agents can be used."*

### Decision

**1. Fux does not call a model. L1 and L4 are HELD, not bracketed.**

This is [ADR-FETCHER](0019_fetcher.md)'s pattern applied to a second boundary:

| fux refuses to own | consumer owns it as |
|---|---|
| network I/O | `.fux/fetchers/http.py` — their code, loaded by path, never rewritten |
| **model calls** | **`.claude/skills/fux-enrich/SKILL.md` — their agent, invoked by them** |

Nothing in `src/fux/enrich.py` imports an SDK, opens a socket or holds a key.
Fux's networked paths stay exactly two (`add <URL>`, `update`). **The `$0` law
survives**: the developer's existing agent subscription pays.

**2. There is no `--model` flag**, because there is no networked path to
fence. `--plan` and `--check` are the whole verb.

**3. Fux VERIFIES `source_sha` and merely RECORDS `model`.**

A sha mismatch means stale, computed and checked. `model:` is a **claim** an
agent is asked to stamp and that nothing here can confirm. That asymmetry is
the honest cost of decision 1, and it is stated rather than implied: provenance
downgrades from *measured* to *declared*, mitigated by shape validation and by
the fact that enrichment lands as a reviewable diff.

**4. Scope is DECLARED — `enrich=true` on a `.fux/sources/dirs` line.**

The same closed-attribute grammar as `archived`, for the same reason
([ADR-DIR-LIST](0022_dir-list.md) decision 10): a path heuristic is exact for
the repo that invented it and a silent convention for everyone else.
Enrichment costs money and changes ranking, so which directories get it is a
human decision written in a diffable line.

**5. Partial coverage is the STEADY STATE, not a degraded mode.**

Enrichment is keyed by the source content sha, so editing a document
un-enriches it automatically. One commit after a full pass and a 411-document
corpus is at 408. **Any design that only works at 100 % coverage is broken on
day two.** So:

- **partial across the corpus** = intended, declared, not a defect;
- **partial inside a declared scope** = a defect, and what `--check` reports.

**6. The tilt is real, and it is why (5) matters.** An enriched document can
match queries an un-enriched one cannot, so a half-enriched scope tilts ranking
toward whichever half was finished. Arpit ruled `ctx` a weighted field
(`w_ctx`, a tune key) *conditional on the tilt being small* — see W-76 veto 3,
which is a measurement, not an opinion.

**7. Orphaned enrichment is never auto-deleted.** A reverted document recovers
its enrichment for free, because the old sha comes back and the file is still
there. `prune()` exists and is explicit.

**8. Frontmatter is stripped before indexing.** Only the body becomes `ctx`
vocabulary. Indexing the block would put a model name and a date into the
document's searchable terms and let it match a query for its own metadata.

**9. A malformed enrichment is IGNORED, not indexed.** The failure mode of
trusting it is silent: whatever text is in the file becomes searchable
vocabulary attributed to that document.

**10. `fux-enrich` is claude-only and INVOKED, never ambient.**

Two of the three shipped renderings are ambient (`applyTo: "**"`,
`inclusion: always`) and enter every request for every developer.
**An ambient skill that writes into a committed directory and changes ranking
is a different risk class.** It ships only in the format with an
explicit-invocation model, and its description names trigger phrases rather
than a topic.

**11. `--plan` prints the FULL sha. Amended 2026-08-24.**

As shipped, `--plan` printed `item.sha[:12]` while `enrich_path()` and
`validate()` used the whole thing. Decision 3 makes `source_sha` the one field
fux *verifies*, and the skill instructs an agent to copy the plan's value into
it — so **every enrichment written by correctly following the skill came back
`STALE`**, and the line saying so rendered as

```
docs/adr-0007-helix-mesh.md  sha c84a92145ee9  7 chunks  STALE (was c84a92145ee9)
```

— the one line whose job is to show a difference, showing two identical
strings. Found 2026-08-24 by generating enrichment for the playground corpus
as the skill describes. The rule this leaves behind is general: **never
abbreviate a value in the message that exists to explain why two values
disagree**, and never print a shortened form of an identifier the reader is
being told to copy.

## 3 · Consequences

- **L3 is restated, not weakened:** the index is a deterministic function of
  **(sources ∪ pinned enrichment)**. Same property, wider input. Every clone
  has the same enrichment files, so every clone builds the same index.
- **Generation is not reproducible and the record says so.** Two developers
  running the skill on one document get different prose; first to commit wins.
- **No batch loop.** One agent session grinding thousands of chunks drifts and
  half-finishes, which is why the skill works scope by scope and `--plan` is
  resumable.
- **`ENRICH-SKILL.md` is exempted from the policy-agreement check**
  (`tests/test_agent_policy_agreement.py::NOT_A_POLICY_RENDERING`). It is a
  procedure, not a rendering of the archived-results policy. The exemption set
  is pinned by its own test so the check cannot be quietly widened.

## 4 · Alternatives considered

- **An SDK call inside `fux enrich` (doc 04's original shape).** Rejected by
  Arpit's ruling. It would break L1 and L4, put a key and a bill inside fux,
  and pin a vendor.
- **Deriving scope from the filesystem.** Rejected under decision 4.
- **Auto-pruning orphans.** Rejected under decision 7.
- **Shipping the skill to all three vendors.** Rejected under decision 10.

## 5 · Reference (required)

- Arpit's ruling and the full argument —
  `work/proposals/ideal/07-rulings.amendment.md` (archived 2026-08-25)
- W-76 Phase 8 — the outcome of record is [`work/IMPLEMENTATION.md`](../../work/IMPLEMENTATION.md)'s W-76 row.
  The closed detail file is `archive/open/W-76-amended-architecture.md` — **named, never cited**
- The contract this inherits — [ADR-ENRICHED](0017_enriched-mode.md)
- Tests — [`tests/test_enrich.py`](../../tests/test_enrich.py)

## 6 · Veto condition

**Veto 1: a network call or a model SDK appears under `src/fux/`.** Decision 1
is the whole record.

```bash
grep -nE '^(import|from) (anthropic|openai|httpx|requests)' -r src/fux/
# expect: nothing
grep -n 'model' src/fux/enrich.py
# expect: only the frontmatter KEY, never a call
```

**Veto 2: `fux enrich` grows a `--model` flag.** Decision 2.

**Veto 3: `fux-enrich` ships in an ambient rendering.** Decision 10 — checked
the way ADR-AGENT-POLICY veto 5 checks the ambient files.

**Veto 4: a malformed or sha-mismatched enrichment reaches `terms`.**
Decision 9. `tests/test_enrich.py` asserts both are ignored.
