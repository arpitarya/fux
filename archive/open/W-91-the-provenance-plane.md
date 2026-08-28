---
type: Handoff
name: W-91
title: W-91 — the provenance plane
description: "How the returned output got generated: a derivation on `ask --why`, a re-runnable receipt on `answer --receipt`, and `fux verify`'s four-state verdict. Built 2026-08-27; L8 was reverted to allow it."
status: open
date: 2026-08-27
timestamp: 2026-08-27T00:00:00Z
---

> ## ✅ ALL FIVE FORKS RULED — 2026-08-27 (Arpit, Cowork)
>
> | fork | ruling |
> |---|---|
> | **A · journalling** | a **`[answer] journal`** key in `.fux/output.toml`, **not** an ADR-TUNE key. ⚠ That **widened `output.toml`'s boundary from *printed* to *emitted***, done in the open rather than left as one key that quietly does not fit |
> | **B · signing** | **adopt the in-toto Statement shape, sign NOTHING.** `hmac` refused for lacking **non-repudiation**; keyless signing is right and costs L1, L4 and `$0` |
> | **C · may `verify` fetch** | **no.** One verb, one question, the same answer on every machine. Veto 3 fires if `verify` ever opens a socket |
> | **D · receipt scope** | **keep it whole.** A receipt is an account of one run; a config knob would make one artifact two shapes |
> | **E · the MCP surface** | **gate the descriptions, add no tools.** Three stays a deliberate surface |
>
> ⚠ **Fork E found a live defect that had shipped an hour earlier:**
> `fux_search` advertised a hand-written `"default": 5` for `k`, and
> `[mcp] top` made the engine use whatever the repo configured — **the schema
> kept saying five and nothing failed.** W-84's class, in the one surface whose
> reader is always a machine. `k` is now computed from
> `output_config.BUILT_IN`.
>
> ⚠ **`_type` collided with fux's own convention.** A leading underscore means
> *metadata* in every fux schema file, and `test_schemas.py` stripped
> `_`-prefixed keys before validating — deleting in-toto's **required** `_type`.
> The strip is a named set now.
>
> **Measured: 1 073 passed** in the cloud container on Python 3.11.15.
> ⚠ `tests_e2e/` and `test_adr_freshness.py` still unrun.

# W-91 — the provenance plane

**Model: Opus.** The build is done. What remains is **judgment**: one law
reversal to sanity-check, one record to ratify, five forks Arpit owes, and a
suite run on a real 3.11 install. None of that is Sonnet work — the law change
is the sharpest thing in this item and it touches the non-negotiable
constraints.

## Why this exists

Arpit, 2026-08-27, in Cowork: *"Is there a way to build an audit trail for how
the returned output got generated? do some research and propose something."*
Then, having read the proposal: *"Create a proposal, a work document, and then
implement it. then close it out."*

Three surfaces described an answer and **none explained it** — the citation says
*which bytes*, [ADR-CONFIDENCE](../../docs/adr/0045_confidence.md) says *how
much we believe it*, `--explain` says *which code path ran*. Nothing said which
term matched which field, what a tune edit moved, or which document was
retrieved and cut.

## ⚠ A LAW WAS REVERTED IN THIS ITEM. Read this first.

**L8 was written on the morning of 2026-08-27 (W-89) and reverted by Arpit the
same afternoon**, inside this item.

- **As written**, L8 required every durable use record to be *hashed, bounded,
  confined to gitignored runtime state, and never on a committed byte, stdout,
  or the network*. It made a per-answer receipt on stdout illegal.
- **Arpit's ruling, verbatim:** *"revert that law we should be able to keep logs
  of the questions as well as answer. it should never be maintained it git so
  having it in git ignore is fine."*
- **As it now stands**, L8 keeps confinement and drops the rest: plaintext
  question *and* answer are legal, a size bound is a design default rather than
  a law, and stdout is permitted. Committed paths and the network stay forbidden.

The change landed in **`CLAUDE.md` §Non-negotiable constraints and
[ADR-LAWS](../../docs/adr/0001_laws.md) decision 8, in the same change**, per
ADR-LAWS decision 4. Its veto check 3 was rewritten — the old one asserted the
hashing and the `MAX_QUESTIONS` bound and would now pass on a repo that had
broken the surviving half.

⚠ **The AOL-2006 grounding is recorded as OVERRIDDEN, NOT REFUTED.** Nothing
about that case became untrue; Arpit weighed it against a readable local log and
chose the log. **A future session may not cite the reversal as evidence the risk
was disproved.** If `.fux/runtime/` ever becomes shareable by any route — a
support bundle, a `doctor --json` dump, a CI artefact — that is the reversal's
blast radius arriving, and it reopens ADR-LAWS decision 8.

## What is built (2026-08-27)

Decisions live in [ADR-PROVENANCE](../../docs/adr/0046_provenance.md); this file
is the state, not a second copy of the record.

| piece | where | state |
|---|---|---|
| the module — derivation, receipt, journal, `verify` | `src/fux/query/provenance.py` | built |
| `ask --why` + `_declare_derivation` (stderr) | `query/__init__.py` | built |
| `answer --audit` / `--receipt` / `--journal` | `query/__init__.py`, `cli.py` | built |
| `fux verify <receipt> [--rerun]` | `query/__init__.py::cmd_verify`, `cli.py` | built |
| `trace_out` on `run_query` — the pre-truncation window | `query/__init__.py` | built |
| `stats` handed back beside the confidence block | `query/__init__.py::_fill_confidence` | built |
| three declared shapes | `query/output.schema.json` | built |
| the law reversal | `CLAUDE.md`, `docs/adr/0001_laws.md` | built |
| records amended | ADR-CLI (9b), ADR-ASK (11, 12), ADR-LAWS (8) | built |
| register + ownership row | `docs/adr/README.md` | built |
| tests | `tests/query/test_provenance.py` (29), `tests/test_cli.py` (verb twin) | **green** |

## Two defects this change found in existing code

**1. `fux answer --json` was NOT validated on two of its three branches.**
`query/output.schema.json`'s own comment claims *"`fux answer --json` is
validated against this before it is printed, so fux cannot emit JSON that
violates its own contract."* Only the no-match branch went through `_emit`; the
`refer` and `index` branches printed raw. **This is W-84's finding in a
different file** — a promise in a machine-facing declaration that no gate read.
Both branches now route through `_emit`, and
`test_every_answer_branch_validates_against_the_output_contract` gates it.

**2. The receipt disagreed with its own answer about freshness, for one run.**
`_print_refer_answer` upgrades the confidence block to the refer plane's real
verdict before printing; the receipt was built from the **pre-upgrade** block,
so it read `verified: unverified` beside its own `verdicts` saying `current`.
**One answer, two disagreeing statements about it — precisely what a provenance
plane exists to make impossible.** Caught by running the command, not by a test.
Fixed with a shared `_upgraded()` used by both callers, and gated by
`test_the_receipt_agrees_with_the_answer_about_freshness` under CLAUDE.md's
two-strikes rule.

## How to check it

```bash
uv run pytest -q tests/query/test_provenance.py tests/test_cli.py

# the end-to-end loop, in a scratch repo with an index
fux ask "<a query>" --why
fux answer "<a query>" --receipt --json | jq .receipt > /tmp/r.json
fux verify /tmp/r.json            # -> unverifiable: inputs match, not re-run
fux verify /tmp/r.json --rerun    # -> reproduced
echo x >> <a cited file>
fux verify /tmp/r.json --rerun    # -> drifted:corpus, with both shas
```

## ⚠ What is NOT verified, and why

- **The full suite was not run on this machine.** The Cowork bridge's
  `device_bash` failed on every attempt this session (5/5), so the work was done
  in the cloud container against a **staged subset of the tree** — `src/fux/`
  complete, but only `tests/query`, `tests/maintain`, `tests/test_cli.py`,
  `tests/test_schemas.py`, and the two ADR-ownership tests. **114 passed on that
  subset, plus 29 new.** `tests_e2e/` was not staged and has not run.
- **`tests/test_adr_freshness.py` and `test_doc_links.py` were not staged** and
  are the two most likely to have something to say about a change this
  document-heavy. Run them first.
- **No regression run was filed.** Nothing here is a measurement — this change
  ships no threshold, no bound and no gate — so `work/regression/` is
  deliberately untouched. If a later session wants to claim `--why` costs
  nothing, **that is a measurement and needs a pre-registration.**
- **Concurrent-session hazard.** `work/BLOCKED.json` still records the W-86
  session holding files uncommitted. `docs/adr/README.md` was edited here
  anyway, because the ownership row is not optional — **re-check it before
  committing.**

## Open — what is owed

1. **Sanity-check the law reversal.** It is the most consequential edit in this
   change and it was made from a one-sentence ruling. Read `CLAUDE.md`'s L8 and
   ADR-LAWS decision 8 together and confirm they say what you meant.
2. **ADR-PROVENANCE is `proposed`.** Built is not ratified.
3. **Five forks, none of which a session may default** — listed in
   [the proposal](../../archive/proposals/answer-provenance.md):
   always-on journalling (an ADR-TUNE key); receipt scope (returned set vs the
   whole window); whether `verify` may fetch; signing (hash vs HMAC vs a real
   signature, which L1 forbids); and the MCP surface.
   ⚠ **Fork 1 is the one a later session will be tempted to default.** *"We
   should be able to keep logs"* is a capability, not a default, and the flag
   already satisfies it.
4. **`fux_search`, `fux_passage`, `fux_related` carry no derivation**, and W-84's
   warning stands: **MCP tool descriptions are documentation no gate reads.**
   Anything added there must be checked against what the handlers actually
   return, in the same change.
5. ⚠ **`0046` IS NOT IN THE PENDING RENUMBER.**
   [`scripts/renumber-adrs.sh`](../../scripts/renumber-adrs.sh) closes `0025`'s
   hole by taking `0026`–`0045` down by one, ending the line contiguous at
   `0044`. It was written before this record existed. **Extend it to carry
   `0046` → `0045` before running it**, or it leaves a hole at `0045` and a
   record sitting above the end of the line — and `tests/test_adr_ownership.py`
   will not catch that, because a gap is legal and only a *duplicate* is not.

6. **The CI check the 2026-07-21 proposal wanted still does not exist** —
   re-run recorded Q→A pairs and fail on drift. `fux verify` is the primitive
   that makes it possible; nobody has built the loop.
