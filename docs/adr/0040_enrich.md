---
type: ADR
name: ADR-ENRICH
title: "ADR-ENRICH (0040) — enrichment as an agent skill, not an API call"
description: "`fux enrich` plans and validates; a coding agent generates. Fux never calls a model, so L1, L4 and the $0 law are held rather than bracketed — and partial coverage is designed for, because sha-keying makes it the steady state. SUPERSEDES ADR-ENRICHED (2026-08-27, W-82 ruling 6): the `enriched` mode taxonomy, its L3 fence, provenance pinning and below-deterministic grading are folded in verbatim, and that mode is still NOT authorized to be built."
status: accepted
date: 2026-08-23
feature: document enrichment — the deterministic halves fux owns, and the generation it refuses to own
owns: [src/fux/enrich.py, src/fux/templates/agents/ENRICH-SKILL.md]
laws: [L1, L2, L3, L4]
supersedes: ADR-ENRICHED
timestamp: 2026-08-23T00:00:00Z
---

# ADR-ENRICH — enrichment as an agent skill

> **This record decides how enrichment is generated and pinned.**
> **ADR-ENRICHED** ratified the *contract* — pinned output, separate command,
> graded below deterministic signal — and explicitly did not authorise a build.
> It was **superseded by this record on 2026-08-27** (W-82 ruling 6) after that
> contract was folded in here verbatim; the archived copy at
> [`archive/adr/0017_enriched-mode.md`](../../archive/adr/0017_enriched-mode.md)
> may be named, never cited. **What this decides is who runs the model**, and the answer
> is: not fux.

## §1 — For humans

Enrichment adds vocabulary a document never literally uses, so a query for
*"idempotency circuit breaker"* reaches a document that discusses the idea
without those words. **Fux plans it and validates it; a coding agent writes it.**

**Diagram — Mermaid and its ASCII twin. Update both, always, together.**

```mermaid
flowchart LR
    D["a declared scope<br/>enrich=true on a dirs line"] --> P["fux enrich --plan<br/>what is MISSING or STALE"]
    P --> A["the fux-enrich SKILL<br/>in YOUR coding agent"]
    A --> F[".fux/enrich/&lt;source sha&gt;.md<br/>committed, pinned"]
    F --> I["fux ingest<br/>body becomes ctx vocabulary"]
    P -.->|"fux never calls a model"| A
    F --> C["fux enrich --check<br/>coverage inside a scope"]
```

<details>
<summary><b>ASCII twin</b> — the same diagram, for terminals, diffs, and any reader without a Mermaid renderer</summary>

```text
  a declared scope (enrich=true on a .fux/sources/dirs line)
        |
        v
  fux enrich --plan      what is MISSING or STALE, per document, by source sha
        |
        |  ... fux stops here. It never calls a model. ...
        v
  the `fux-enrich` SKILL, in YOUR coding agent
        |
        v
  .fux/enrich/<source sha>.md      committed, pinned, reviewable
        |
        +--> fux ingest       the BODY becomes ctx vocabulary
        +--> fux enrich --check   coverage inside a declared scope
```

</details>

### Examples

```console
$ fux enrich --plan
scope docs/adr (enrich=true)
  docs/adr/0012_ranking.md      sha 3f8a1c2d9b04…   9 chunks   MISSING
  docs/adr/0031_maintenance.md  sha 9b2e04f1a733…   6 chunks   STALE (was 7c1d4e02b918…)

-> 2 documents, 15 chunks
   write each to .fux/enrich/<sha>.md
   invoke the `fux-enrich` skill in your coding agent to generate them

$ fux enrich --check
enrichment: 1 scope(s) declared
  docs/adr                     41/41  ok
```

**The mechanism, demonstrated on the fixture repo:** a query for *"idempotency
circuit breaker"* — words appearing **only in the enrichment**, nowhere in the
document — returns the document. **Edit the document by one line and the same
query returns nothing**, because the enrichment no longer matches its sha.

---

## §2 — For agents

### Context

The ruling that shaped this:

> *"Enrich should work like a skill in the chat — that way we don't need to
> integrate the API in the code and AI coding agents can be used."*

### Decision

**1. Fux does not call a model. L1 and L4 are HELD, not bracketed.** This is
[ADR-FETCHER](0019_fetcher.md)'s pattern applied to a second boundary:

| fux refuses to own | the consumer owns it as |
|---|---|
| network I/O | `.fux/fetchers/http.py` — their code, loaded by path, never rewritten |
| **model calls** | **`.claude/skills/fux-enrich/SKILL.md` — their agent, invoked by them** |

Nothing in `src/fux/enrich.py` imports an SDK, opens a socket or holds a key.
Fux's networked paths stay exactly two. **The `$0` law survives**: the
developer's existing agent subscription pays.

**2. There is no `--model` flag**, because there is no networked path to fence.
`--plan` and `--check` are the whole verb.

**3. Fux VERIFIES `source_sha` and merely RECORDS `model`.** A sha mismatch
means stale, computed and checked. `model:` is a **claim** an agent is asked to
stamp and that nothing here can confirm. ⚠ **That asymmetry is the honest cost
of decision 1**: provenance downgrades from *measured* to *declared*, mitigated
by shape validation and by the fact that enrichment lands as a reviewable diff.

**4. Scope is DECLARED — `enrich=true` on a `.fux/sources/dirs` line.** The same
closed-attribute grammar as `archived`, for the same reason: **a path heuristic
is exact for the repo that invented it and a silent convention for everyone
else.** Enrichment costs money and changes ranking, so which directories get it
is a human decision written in a diffable line.

**5. Partial coverage is the STEADY STATE, not a degraded mode.** Enrichment is
keyed by the source content sha, so **editing a document un-enriches it
automatically.** One commit after a full pass and a 411-document corpus is at
408. **Any design that only works at 100 % coverage is broken on day two.** So:

- **partial across the corpus** = intended, declared, not a defect;
- **partial inside a declared scope** = a defect, and what `--check` reports.

**6. The tilt is real, and it is why decision 5 matters.** An enriched document
can match queries an un-enriched one cannot, **so a half-enriched scope tilts
ranking toward whichever half was finished.** `ctx` is a weighted field with its
own tune key *conditional on the tilt being small* — which is a measurement, not
an opinion.

**7. Orphaned enrichment is never auto-deleted.** A reverted document recovers
its enrichment for free, because the old sha comes back and the file is still
there. `prune()` exists and is explicit.

**8. Frontmatter is stripped before indexing.** Only the body becomes `ctx`
vocabulary. Indexing the block would put a model name and a date into the
document's searchable terms **and let it match a query for its own metadata.**

**9. A malformed enrichment is IGNORED, not indexed.** ⚠ **The failure mode of
trusting it is silent**: whatever text is in the file becomes searchable
vocabulary attributed to that document.

**10. `fux-enrich` is INVOKED, never ambient.** **An ambient skill that writes
into a committed directory and changes ranking is a different risk class**, so
it ships only where invocation is explicit, and its description names trigger
phrases rather than a topic.

⚠ **It ships to Claude alone today, and the reasoning that admits a Kiro skill
elsewhere would admit one here.** [ADR-AGENT-POLICY](0035_agent-policy.md)
decision 9a establishes that **a Kiro *skill* is progressive-disclosure and only
Kiro *steering* is ambient** — which is why the decoder skill ships to both
skill surfaces. **This one has not been extended, and the gap is stated rather
than left to be discovered as an inconsistency.**

**11. `--plan` prints the FULL sha.** ⚠ It once printed a 12-character prefix
while the validator used the whole thing — and since decision 3 makes
`source_sha` the one field fux *verifies*, and the skill instructs an agent to
copy the plan's value into it, **every enrichment written by correctly following
the skill came back `STALE`**, rendering as:

```
docs/adr-0007-helix-mesh.md  sha c84a92145ee9  7 chunks  STALE (was c84a92145ee9)
```

**— the one line whose job is to show a difference, showing two identical
strings.** The rule this leaves behind is general: **never abbreviate a value in
the message that exists to explain why two values disagree**, and never print a
shortened form of an identifier the reader is being told to copy.

**12. The enrichment body is inside the redaction boundary, on both of the
surfaces it reaches** (W-102, 2026-09-01). An enrichment body is committed
**and** indexed, so a value written into one travels twice, and
[ADR-PII](0053_pii.md) decision 1 covers both. The two halves are handled
differently on purpose:

- **`run.py` redacts the body before it becomes `ctx`.** ⚠ **This was the real
  defect and it was not the one anybody had written down.** The redact phase
  walks `parsed`, which holds document *bodies*; `_enrichment_for()` reads the
  enrichment file further down and handed its text straight to
  `extract_fields`. An email address in enrichment prose therefore became a
  **committed index term**, on a document whose own body had been redacted, one
  screen below a comment stating that everything downstream was built from
  redacted text. Redaction now happens in `_enrichment_for`, and the phase
  comment says why it cannot be in the phase named after it.
- **`fux enrich --check` refuses and never rewrites.** The file is prose a
  human reviews in a diff; a silent rewrite would make that diff lie. Same
  discipline as `fux doctor` reporting a lock it will not clear
  ([ADR-MAINTENANCE](0032_hooks.md) veto 7), and stronger here for that reason.
  🔴 **Redaction is also the wrong remedy at this surface**: a redacted
  enrichment body indexes `[PII:email]` as vocabulary, which is worse than
  useless. The refusal names the rule that fired, per
  [ADR-PII](0053_pii.md) decision 7, and says to rewrite the sentence instead.
- **The frontmatter is deliberately excluded.** It is stripped before indexing
  (decision 8), so nothing in it reaches a committed term; running rules over a
  `model:` value would refuse a file for text the index never sees.
- ⚠ **No sha is recomputed.** The enrichment file's name and `source_sha:` are
  the *source document's* sha over raw bytes, and ADR-PII decision 3's ordering
  hazard applies here verbatim — a sha over redacted text would report every
  enriched document `stale` against its own unchanged source.
- **Landing this re-ingests any repo with both enrichment and a firing rule**,
  and `runtime/pii-digest` does not cover it: the ruleset did not move, its
  *reach* did. That is a one-off cost of the fix, not a new invalidation rule.

**13. `--plan` and `--check` take an optional `TARGET`, and the skill runs them
itself** (W-104, Arpit 2026-09-01). One `loc` or one URL, matched **exactly** —
not a prefix and not a glob, because a selector that silently matches two
documents turns a one-document request into a bulk run.

- 🔴 **It filters the report; it never widens scope.** A document no
  `enrich=true` line reaches is not in the plan, and naming it says which of
  two things is wrong — *not declared* (a human's edit to a source list) or
  *not indexed* (`fux ingest`) — rather than enriching it. Decision 4 is
  untouched: which directories are enriched stays a declaration.
- **`n/total` stays the whole scope under a selector.** A single-target run
  must never render as `n/n`; that is the line the skill reads to decide a
  scope is finished.
- **Single-target runs are legitimate because of decision 5.** Partial coverage
  is the steady state, so leaving a scope at `40/41` on purpose is a requested
  outcome rather than the tilt decision 6 warns about — and the skill says
  which of the two it is doing each time.
- **The skill plans internally, and asks before bulk.** Step 1 was written as a
  command a human had already run. It is now the agent's first action, and a
  plan of more than one document that was not explicitly asked for as a scope
  is a **question the skill stops on** — safe only because the skill is invoked
  and never ambient (decision 10).
- **It re-plans immediately before writing.** Between reading a document and
  saving an enrichment there is a window in which the document can move, and an
  enrichment written under a superseded sha is **invisible rather than wrong**:
  fux does not find it and nothing reports an error. ⚠ **This is the whole of
  the gap** — no second hash, no `doc_hash` field, no sidecar digest. Decision
  3's sha-keying is the staleness mechanism, and a second one could only drift
  against it.

### The `enriched` mode — folded verbatim from ADR-ENRICHED, 2026-08-27

⚠ **This section is ADR-ENRICHED's ratified content, moved here UNCHANGED**
under W-82 ruling 6 (*"ENRICH supersedes ENRICHED"*). It was folded **before**
that record was archived, deliberately: archiving first would have made every
sentence below uncitable, and §1's calls rest on them. Its numbering is the
numbering it had there, so a citation of *"ADR-ENRICHED decision 4"* still
resolves to the same words.

⚠ **`enriched` and `fux enrich` are two different things and this is the trap.**
`fux enrich` — the rest of this record — pins text a coding agent wrote, and the
committed record stays `"mode": "extracted"`, **correctly**: a pinned file is
bytes fux read, not something fux inferred. The `enriched` MODE below is a
second value of a record's `mode` property and **is still not authorized to be
built.** The name similarity is the trap; **the `mode` value on disk is the
truth.**

⚠ **[ADR-EXTRACTED](0016_extracted-mode.md) lost its counterpart record**, so
the two-mode taxonomy now lives here and ADR-EXTRACTED's citations resolve to
this section.

**1. The model-assisted ingest mode is named `enriched`**, ratified together
with [ADR-EXTRACTED](0016_extracted-mode.md); the pair was one call.

**2. Enrichment never runs inside the maintenance path.** It is a separate
command or agent skill, invoked deliberately. `fux ingest` gains no model call,
no network path, and no `--enrich` flag — not as a convenience, not behind a
default-off toggle. **L3 is preserved by construction, not by discipline.**

**3. Output is pinned, then ingested like any other committed content.** The
enrichment step writes a committed artifact with provenance — what produced it,
from which document at which `sha`, when. Ingest reads that artifact
deterministically. **Nothing is regenerated on a query path, ever.**

**4. Enriched signal is graded below deterministic signal** wherever the two
compete, reusing the ported `EXTRACTED` > `INFERRED` edge-grade ordering rather
than inventing a second scale.

**5. Enriched output stays statistic-shaped.** Terms, phrases, edges, flags —
the things the index already holds. **Prose summaries are excluded**: a
paragraph of model-written prose in the committed index is durable content in
every sense that matters to L2, whatever the technicality. If summaries are ever
wanted, they go through the existing per-source snapshot policy as an explicit,
visible exception — never silently as a side effect of enrichment.

**6. Accepting this record does not authorize the work.** It ratifies the name,
the boundary and the shape — nothing more. **The gate is one ADR plus Arpit's
sign-off; the ADR half is this record, and the sign-off half has not been
given.**

### The candidate enrichments, and why each needs a model

Recorded so a build designs against a list rather than a mood. **None is
approved.**

| candidate | what deterministic extraction cannot do | risk |
|---|---|---|
| **semantic term expansion** | the analyzer sees only literal page vocabulary — a query for "OOM" never reaches a doc that says "memory exhaustion" | dilutes `df`; needs a graded, separable term set or it contaminates the statistics every document is scored against |
| **inferred edges** | links two documents mean to have but never wrote — "this design implements that decision", with no hyperlink | must carry `INFERRED`; **a wrong edge is worse than a missing one because it is invisible** |
| **retirement / supersession flags** | nothing in the bytes distinguishes a live document from a retired one | if it reorders rather than annotates, it violates the ruling [ADR-ARCHIVED-CONTENT](0037_archived-content.md) already reached |
| **richer embeddings** | fux computes no vectors at all ([ADR-ASK](0004_ask.md) decision 9) | **L1 collision** — a larger or API-served model may be *called once and pinned*, never imported into the runtime |

### The candidate enrichments, and why each needs a model

Recorded so a build designs against a list rather than a mood. **None is
approved.**

| candidate | what deterministic extraction cannot do | risk |
|---|---|---|
| **semantic term expansion** | the analyzer sees only literal page vocabulary — a query for "OOM" never reaches a doc that says "memory exhaustion" | dilutes `df`; needs a graded, separable term set or it contaminates the statistics every document is scored against |
| **inferred edges** | links two documents mean to have but never wrote — "this design implements that decision", with no hyperlink | must carry `INFERRED`; **a wrong edge is worse than a missing one because it is invisible** |
| **retirement / supersession flags** | nothing in the bytes distinguishes a live document from a retired one | if it reorders rather than annotates, it violates the ruling [ADR-ARCHIVED-CONTENT](0037_archived-content.md) already reached |
| **richer embeddings** | fux computes no vectors at all ([ADR-ASK](0004_ask.md) decision 9) | **L1 collision** — a larger or API-served model may be *called once and pinned*, never imported into the runtime |

⚠ **Import path moved 2026-08-27, behaviour unchanged.** ``src/fux/enrich.py`` now imports
`chunk` from **`fux.refer._chunk`**: the module was made private because
`fux.refer` re-exported the `chunk` *function* over its own submodule of that
name, a shape that had already cost four defects and silently narrowed L4's
network import fence. The function, its signature and its output are untouched —
see [ADR-REFER](0030_refer-plane.md) decision 18 and
[`tests/test_no_shadowed_submodules.py`](../../tests/test_no_shadowed_submodules.py).

**11. A `url:` document is enrichable, under one synthetic scope**
([ADR-PII](0053_pii.md), 2026-09-01). `enrich=` joins the URL list's attribute
set and resolves through the same three layers as `keep` and `ttl`; every URL
that opts in reports under a single scope named `.fux/sources/urls`.

- **One scope, not one per host.** A `dirs` scope is a path prefix, which is a
  grouping a human actually chose. A URL list has no such structure — its lines
  share nothing but being URLs — so per-host scopes would report coverage
  against a grouping nobody declared. Decision 4's *declared, never derived*
  applied to the scope itself.
- ⚠ **This could not exist before `.fux/acquired/`.** Planning needs the
  document's text, and for a URL that meant a network fetch **inside
  `fux enrich --plan`** — an offline, read-only command (L4). The retained
  bytes are what make the text local, so `_document_text` reads the blob and
  decodes it with ingest's own `_decode_fetched` rather than fetching anything.
- **`keep=true` is the default, so this works unconfigured.** A line that opted
  out with `keep=false` has nothing to read: it reports **zero chunks**, and
  `--plan` names that rather than hiding it — the same treatment an unreadable
  `file:` document gets.

**A URL's enrichment is committed and indexed like any other**, so decision 12
covers it unchanged: the body is redacted before it becomes `ctx`, and
`fux enrich --check` refuses a file whose body matches a `.fux/pii.toml` rule.
There is nothing URL-specific about that boundary and this section states none.

### Consequences

- **L3 is restated, not weakened:** the index is a deterministic function of
  **(sources ∪ pinned enrichment)**. Same property, wider input. **Every clone
  has the same enrichment files, so every clone builds the same index.**
- **Generation is not reproducible and the record says so.** Two developers
  running the skill on one document get different prose; first to commit wins.
- **No batch loop.** One agent session grinding thousands of chunks drifts and
  half-finishes, which is why the skill works scope by scope and `--plan` is
  resumable.
- **`ENRICH-SKILL.md` is exempt from the policy-agreement check.** It is a
  **procedure**, not a rendering of the archived-results policy, and the
  exemption set is pinned by its own test so the check cannot be quietly
  widened ([ADR-AGENT-POLICY](0035_agent-policy.md) decision 2a).
- ⚠ **Who may *author* an enrichment, when it is being MEASURED, is not this
  record's rule.** `fux enrich` cannot enforce authorship — **fux never calls a
  model, so the author is outside the program** — which makes it a
  **measurement-protocol** rule, living in [ADR-RS](0036_predictions.md)
  decisions 11–15. Nothing changes about *generating* enrichment; what changes
  is that **a run which measures it declares whether the author could reach the
  evaluation queries**, and an informed run never supplies a delta. **That is a
  restriction on what a number may claim, not on the enrichment.**

### Alternatives considered

- **An SDK call inside `fux enrich`.** Rejected: it would break L1 and L4, put a
  key and a bill inside fux, and pin a vendor.
- **Deriving scope from the filesystem.** Rejected under decision 4.
- **Auto-pruning orphans.** Rejected under decision 7.
- **Trusting a malformed enrichment and indexing what is there.** Rejected under
  decision 9 — the failure is silent and attributes invented vocabulary to a
  real document.
- **Shipping the skill to an ambient surface.** Rejected under decision 10.

### Reference (required)

- The deterministic halves — [`src/fux/enrich.py`](../../src/fux/enrich.py);
  the generation half —
  [`src/fux/templates/agents/ENRICH-SKILL.md`](../../src/fux/templates/agents/ENRICH-SKILL.md);
  the tests — [`tests/test_enrich.py`](../../tests/test_enrich.py).
- The contract this inherits — [ADR-ENRICHED](../../archive/adr/0017_enriched-mode.md); the scope
  grammar — [ADR-DIR-LIST](0022_dir-list.md); the field it feeds —
  [ADR-RANKING](0012_ranking.md) decision 1.
- The authorship rule that governs *measuring* enrichment —
  [ADR-RS](0036_predictions.md) decisions 11–15.

### Veto condition

**Reopen this decision if any of these becomes true:**

1. **A network call or a model SDK appears under `src/fux/`.** Decision 1 is the
   whole record.
2. **`fux enrich` grows a `--model` flag.** Decision 2.
3. **`fux-enrich` ships in an ambient rendering.** Decision 10.
4. **A malformed or sha-mismatched enrichment reaches `terms`.** Decision 9.

**How to check them:**

```bash
# 1 — no SDK, no socket, no key
grep -nE '^(import|from) (anthropic|openai|httpx|requests)' -r src/fux/
# expect: nothing
grep -n 'model' src/fux/enrich.py
# expect: only the frontmatter KEY, never a call

# 3 — the skill ships to skill surfaces only
grep -n 'ENRICH-SKILL' src/fux/setup.py
# expect: under `.claude/skills/` (and `.kiro/skills/` if decision 10's gap closes)

# 2, 4 — the flag that must not exist, and the two ignore paths
pytest -q tests/test_enrich.py
```

---

## References

*Every source this record cites, gathered in one place. §2's **Reference
(required)** names the grounding; this is the complete list. An archived
document is never listed here — the body may name one, but archive is not
evidence.*

**Records** — [ADR-LAWS](0001_laws.md) · [ADR-RANKING](0012_ranking.md) ·
[ADR-ENRICHED](../../archive/adr/0017_enriched-mode.md) · [ADR-FETCHER](0019_fetcher.md) ·
[ADR-DIR-LIST](0022_dir-list.md) · [ADR-AGENT-POLICY](0035_agent-policy.md) ·
[ADR-RS](0036_predictions.md) · [ADR-TUNE](0038_tuning.md)

**Code**

- [`src/fux/enrich.py`](../../src/fux/enrich.py)
- [`src/fux/setup.py`](../../src/fux/setup.py)
- [`src/fux/templates/agents/ENRICH-SKILL.md`](../../src/fux/templates/agents/ENRICH-SKILL.md)
- [`tests/test_enrich.py`](../../tests/test_enrich.py)

**Project docs**

- [`work/IMPLEMENTATION.md`](../../work/IMPLEMENTATION.md)
