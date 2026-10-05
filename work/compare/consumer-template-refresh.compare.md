---
type: Compare Doc
title: "Consumer-side template refresh — how an engine fix reaches a consumer's `.fux/decoders/`, `.fux/fetchers/` and `pii.toml`"
description: "Backlog B-013 and B-014 (B-073 and B-221 adjacent) as one fork. Today a copy written once into a consumer's `.fux/` is frozen forever; four real decoder defects would each have needed every consumer to refresh by hand. Options: a template sha stamp with engine-owned refresh of unedited copies, doctor-names-the-gap only, or keep the freeze. Recommended: the stamp — but SR-DECODE d10 DECLINED it, so reopening is Arpit's."
status: ruled 2026-10-04 (Arpit, W-251 §3 #2) — option B; A refused. Built 2026-10-05 (W-262)
timestamp: 2026-10-03T00:00:00Z
filed: 2026-10-03
---

# Consumer-side template refresh

> ✅ **RULED 2026-10-04 (Arpit, Cowork): option B** — *"go with the
> recommendation."* Seeded copies carry a template stamp; `fux doctor` names an
> unedited copy whose template changed; **fux never rewrites a consumer's
> file.** Option A (engine-owned refresh of unedited copies) is refused: it
> crossed SR-DOTFUX d6, SR-FETCHER d12 and L10. Build:
> [W-262](../open/W-262-land-arpit-w251-rulings.md) §1. The text below is the
> argument as it was put.
>
> ✅ **BUILT 2026-10-05 (W-262).** `fux setup` writes every decoder and fetcher
> copy with a first line `# fux-template: <sha256>` (prefix:
> `constants.toml [templates] stamp_prefix`; digest over LF-normalised bytes);
> below it the bytes are the template exactly. `fux doctor`'s new
> `seeded copies current` row (warn) names an **unedited** copy — body still
> hashes to its stamp — whose template has changed, with the lever *re-seed it
> yourself* (delete, `fux setup`); an edited copy is not compared, an unstamped
> one is counted and never judged. Nothing writes the file; a test holds
> `doctor`, `doctor --fix`'s writer and `fux setup` to that. Records: SR-DECODE
> d10, SR-FETCHER d12, SR-DOTFUX 6a, SR-DOCTOR's register. `pii.toml` and
> `refusals.toml` are not stamped — the adjacent seam this doc left undecided.
> B-013 and B-014 deleted.

> **Verdict: PROPOSED — option A, the template stamp; option B if he will not
> reopen a rewrite.** Every file the engine writes into a consumer's `.fux/`
> carries `# fux-template: <sha>` (TOML: a `template_sha` key). **A:** a copy
> whose stamp matches **any** shipped version is engine-owned and refreshed on
> upgrade exactly as SR-DOTFUX 6a refreshes `node/`; an edited copy is frozen
> and `doctor` names the version gap. **B:** the stamp, and `doctor` names the
> gap for every copy — never writes. **Confidence: medium.**
> ⚠ **Re-read 2026-10-04 (W-251 §4 research), two corrections.** (i) Option A
> is **not** the variant Arpit declined on 2026-08-26 (W-86 P7, WORKLOG
> 6641–6647): that one was *copy inert, built-in runs until edited*; A keeps
> *the copy is what runs* (SR-DECODE d8/d10) and adds *an unedited copy is
> refreshed on upgrade*. SR-DOTFUX's rejection reason — *"a consumer reading
> `.fux/decoders/pdf.py` and finding it is not the code that ran"* — does not
> apply to A. (ii) A still crosses **three fences in his name**: SR-DOTFUX d6
> (*"If a change must reach existing repos, the mechanism is a loader refusal
> or a `doctor` check — never a rewrite"*), SR-FETCHER d12 (his, 2026-08-28,
> restating d6), and L10's *"seeded once, then the consumer owns it"*. **B
> crosses none** and is the d6-conformant mechanism. **So this fork is his
> alone (W-251 §3 #2) and nothing here was ratified by delegation** — half the
> mechanism already exists (`decoderdigest.py` hashes a copy; `doctor._provenance`
> reports a digest mismatch), so B is S and A is M.
> **Reopen-trigger:** the fifth engine-side defect in a shipped template that a
> consumer could not receive, or a consumer reporting an edited copy silently
> overwritten.

**Model: Opus** for the build if ruled — the ownership test (*edited or not?*)
decides whether a consumer's code is overwritten.

## Context

Three records describe the same seam from three sides:

- [SR-DECODE](../../records/0139_decode.md) decision 10 — *"engine upgrades do
  not reach a consumer's `.fux/decoders/` … four real defects would each have
  needed every consumer to refresh their copy"*; a hash stamp was proposed and
  **declined**, the freeze accepted as a cost.
- [SR-FETCHER](../../records/0117_fetcher.md) decision 12 — the optional-functions
  gap (`validate()`, `is_rate_limited()`) *"is made visible, not closed"*; a
  consumer still copies them in.
- [SR-DOTFUX](../../records/0102_fux-directory.md) decision 6a — `node/` **is**
  refreshed on upgrade (write-if-missing became engine-owned-and-pruned), and the
  record's own Consequences now say of the decoders: *"The evidence is in this
  repository, and it already cost something … Same mechanism, worse outcome."*

So the record that declined the stamp and the record that built the refresh for
a neighbouring plane disagree about the same evidence. That is why this is a
fork and not a cleanup.

Adjacent, same seam, not decided here: `.fux/pii.toml` is outside the
template-drift gate (B-073 → a subset-by-id test in W-246);
a frozen `formats.toml` type list stops tracking new built-in decoders (B-221,
`cost`).

## Options

- **A — template stamp, engine-owned unless edited** (recommended). Stamp at
  write; on upgrade, a copy whose stamp matches a shipped version is rewritten
  and re-stamped; an edited copy is left and `doctor` reports *forked from
  template v<n>, <k> fixes since*. The same shape as `node/`'s refresh (6a),
  extended with the one test 6a does not need: *was it edited?*
- **B — doctor names the gap, never writes.** Stamp at write; `doctor` reports
  the version gap for every copy; the consumer refreshes by hand (`fux setup
  --refresh decoders`). Visible, not closed — the SR-FETCHER d12 posture,
  mechanised.
- **C — keep the freeze.** The accepted cost stands; the SR-DOTFUX sentence is
  softened to match SR-DECODE d10. Nothing is built.

## Matrix

| | A stamp + refresh | B stamp + report | C freeze |
|---|---|---|---|
| a shipped fix reaches an unedited consumer copy | **yes, on upgrade** | when the consumer acts | never |
| an edited consumer copy is ever overwritten | **no** (stamp mismatch) | no | no |
| the consumer learns their copy is behind | yes (`doctor`) | yes (`doctor`) | no |
| consistent with SR-DOTFUX 6a (`node/`) | yes | partly | **contradicts its Consequences** |
| reopens a declined decision | **yes** (SR-DECODE d10) | yes, half | no |
| L10 (consumer is served build output; extension points are source) | compatible — a template IS the consumer's source; the stamp marks the engine's copy of it | compatible | compatible |
| size | S–M | S | 0 |

## Consequences of A

- `fux setup` / `doctor --fix` write the stamp; `fux` on upgrade walks
  `.fux/decoders/`, `.fux/fetchers/` (and `pii.toml` by key) once per version
  difference — the prune that already runs for `node/`.
- A consumer who **wants** the engine's copy edits nothing; one who wants their
  own edits one byte and owns it from then on. That is the whole contract, and
  it is one sentence in the `fux-decoder` / `fux-fetcher` skills.
- SR-DECODE d10 is amended (the declined alternative becomes the decision, with
  the four-defect evidence that moved it); SR-FETCHER d12 and SR-DOTFUX 6a
  gain a sentence each; B-013 and B-014 leave the backlog.
- ⚠ A stamp matching *any shipped version* needs the shipped versions'
  hashes in `constants.toml` (L12) — one list per template, appended per
  release.

## References

- SR-DECODE d10, d17 · SR-FETCHER d12 · SR-DOTFUX 6a, 8, Consequences ·
  SR-PII d17 · [L10](../../records/0012_LAW-10-bundled-output.md).
- W-251 §3 #2.

## Reopen-trigger

A fifth engine-side defect in a shipped template that a consumer could not
receive; or a consumer reports an edited copy overwritten (A's one failure
mode, which the stamp exists to prevent).
