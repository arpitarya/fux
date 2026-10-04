---
type: Handoff
name: W-253
description: "Three 3.0 contract cleanups ruled by delegation on 2026-10-04 (W-251 §4 #4, #10): the bare-`str` fetcher ramp is removed; `--under` and `Weighting.priority_for` apply a component boundary on both CLIs; `find --json` writes `confidence` before `fused`. One Sonnet session, one CHANGELOG pass. Ratified, NOT built."
item: W-253
filed: 2026-10-04
ball: agent
---

# W-253 — the 3.0 contract cleanups ruled by W-251

**Model:** Claude Code, **Sonnet** — every change is against a written sentence
and is parity-testable by the existing differential arm; nothing here needs a
diagnosis. **Ratified 2026-10-04 by delegation ([W-251](W-251-backlog-audit-rulings.md)
§4 rows #4 and #10), not built.**

**Why one item.** All three are breaking-in-letter changes that are free inside
the already-breaking 3.0 (`fetch=` mandatory, `fux update` deleted, Python
3.12 / Node 22 floors, L12's hard errors — SR-WORK-RELEASE). Each would need a
deprecation cycle in 3.1. One session lands them under one *Changed / Removed*
block in `CHANGELOG.md`, and the differential arm reads the result once.

## The three rulings

1. **The bare-`str` fetcher return ramp is removed** (B-100). `fetch` returns
   `tuple[bytes, str]`; a fetcher returning a `str`, or a `str` inside the
   tuple, is refused with a `FuxError` that names the fetcher and the contract —
   **a named skip of that URL, never a crash** (SR-FETCHER d2's *"may raise …
   never a crash"* still governs). *Why it is safe:* the ramp protected
   fetchers written before 2026-08-26 from a contract they had not read;
   3.0.0-alpha.2 (SR-URL-LIST d16/d17, Arpit's breaking change) already made
   every such repository rewrite its URL lines, so the ramp protects nothing
   the major has not broken. SR-FETCHER 17d already names it as in tension with
   the pipe ruling.
2. **`--under` is a component boundary on both CLIs, and `Weighting.priority_for`
   gains the same boundary** (B-146). `--under docs/a` keeps `docs/a` and
   `docs/a/**`, never `docs/ab.md` — the semantics `fux.api.find(under=)`
   already has (SR-API d6). *Why:* Node's `priorityFor` (`node/src/query/rank.mjs:65`)
   **already** applies the boundary while Python's `priority_for`
   (`src/fux/query/rank.py:235`) is a bare prefix — a cross-runtime divergence
   the arm cannot see until a `[priority]` key collides with a sibling; and
   SR-TUNE d8 + SR-DIR-LIST 2e make a `[priority]` key a *directory entry as it
   appears in `dirs`*, so a bare prefix on `docs` scaling `docs-old/…` is a
   defect, not a taste. SR-FIND d7's argument (*"would disagree with the
   resolver"*) inverts the moment the resolver moves.
3. **`find --json` writes `confidence` before `fused`** (B-151), as `ask` and
   `fux.api` already do; the order becomes documented in SR-CLI and tested.
   SR-FIND's own words: *"not a decision anybody took, it is one line in
   whichever verb moves."*

**Refused, not built — recorded here so nobody picks it up:** promoting the
`changed_since` stderr line to a `--json` field (B-148). Its value depends on
the previous run's gitignored `.fux/runtime/last-cited.json`, so `answer --json`
would differ between two machines on identical bytes — the byte-stability class
SR-CLI veto 5 forbids. The sentence lands via [W-245](W-245-record-sentences-stale.md)
(SR-ANSWER d10).

**Left for Arpit, not in this item:** the graph verbs' `--json` shape (B-147,
W-251 §3 #4).

## Definition of done

1. `src/fux/ingest/urlsrc.py::_unpack` — both `str` branches gone; a `str`
   return raises a `FuxError` naming the fetcher, caught at the per-URL skip
   boundary (the skip is reported like any other fetch failure, with its
   reason); module docstring updated.
2. `src/fux/query/rank.py::priority_for` — exact match or `/`-boundary match;
   `src/fux/query/__init__.py` (the `find` `--under` filter) and
   `node/src/verbs/find.mjs` — the same boundary. Python and Node CLIs move in
   **one change** or the ranking lane of the arm goes red.
3. `find --json` key order in `src/fux/query/__init__.py` and
   `node/src/verbs/find.mjs`: `confidence`, then `fused`.
4. Tests: a fake fetcher returning `str` yields a named skip (convert the ~5
   fixtures in `tests/test_url_update_policy.py`, `tests/test_source_verbs.py`,
   `tests/test_doctor_fetcher_bindings.py` to tuples); `tests/test_tune_boundary.py`
   gains a `docs` vs `docs-old` case for `priority_for`; a `--under docs/a` vs
   `docs/ab.md` case for both CLIs; a byte-order test for `find --json`.
5. Records, same change, `sr-hash.py --write` each: SR-FETCHER d2 (the ramp
   paragraph → *removed in 3.0, W-253*) and 17d (*"Not removed"* → *removed*);
   SR-FIND d7 and Consequences (the key-order bullet); SR-TUNE d8a (the
   boundary sentence); SR-API d6 (*"changing it is Arpit's call"* → *closed:
   the CLI adopted the boundary; the library did not move*); SR-CLI's `--json`
   contract paragraph (key order documented). The exact sentences are in W-245's
   table, marked *W-253 writes this one*.
6. `CHANGELOG.md` `[Unreleased]` → *Removed (BREAKING):* the ramp; *Changed
   (BREAKING):* `--under` / `[priority]` boundary, `find --json` key order.
7. Both suites whole, `node --test node/test/*.test.mjs`, and the differential
   arm's repo pass; a WORKLOG entry.

## Out of scope

- The graph verbs' payload shape (B-147) — Arpit's.
- `changed_since` as a field — refused above.
- [W-247](W-247-api-renderer-split.md)'s renderer split; it does not need to
  land first (none of these lines are the ones it moves).

## Hazards

- ⚠ A consumer on 2.x upgrading straight to 3.0 final meets two fetcher breaks
  at once (lines + return type). Acceptable — same release, and the error names
  the fix.
- ⚠ A `[priority] "docs"` key that relied on scaling `docs-old/` loses it. No
  such consumer is known; unmeasurable; the CHANGELOG line is the notice.
- ⚠ Changing Python's `find` key order without Node's reddens the arm; change
  both in one commit.
