---
type: Handoff
name: W-264
description: "Arpit's ruling 2026-10-04 (W-260 line 2, option B): a redaction cache so an unchanged file skips `redact` on a delta ingest — keyed on the file's content sha AND the pii.toml rules digest AND the redactor's version, so a rule change re-redacts everything. Target: the ~6 s redact share of a 10.4 s no-change ingest at rung-10000."
item: W-264
filed: 2026-10-04
ball: agent
---

# W-264 — unchanged files skip redaction (a redaction cache)

**Status: ratified 2026-10-04, not built.**

**Arpit, 2026-10-04 (Cowork), on [W-260](../../archive/open/W-260-w256-results-to-rule.md) line 2:**
*"for line 2 go with option B — build a cache so unchanged files skip
redaction."* He chose (b) over the recommended (a) *explain the 6 s first*.

**Why:** at rung-10000 a delta ingest with **zero changes** costs a median
**10.39 s** (full: 15.11 s), and `redact` carries **~57 % (5.9–6.0 s)** of it
([run](../regression/2026-10-04-ingest-split/VERDICT.md)).

**Model:** Claude Code, **Opus** — a cache over PII redaction fails *open* if
its key is short: a stale entry would index text the current rules redact.

## 🔴 The key — every member, or it is a privacy defect

A cached redaction is valid only if **all** of these are unchanged:

1. the file's **raw content sha** (pre-redaction bytes);
2. a **digest of the effective `pii.toml` rules** (patterns, groups, `validate`
   set, order) — a rule added or edited must re-redact every file;
3. the **redactor's version** (code + analyzer), so an engine upgrade
   re-redacts;
4. anything else `redact()` reads ([`ingest/pii.py`](../../src/fux/ingest/pii.py)
   `redact(rules, text)`) — enumerate it from the code, do not assume.

SR-CACHE d2's lesson applies verbatim: *a cache is safe only when its key proves
the hit is identical.*

## Definition of done

1. **Explain the 6 s first, inside this item** (it is the input the cache is
   sized against): W-239 measured `redact` at **0.97 s** on the same rung. Find
   which number is the real one (the run guessed at a `pii.toml` that
   `doctor --fix` wrote into the copy). Record the answer in the run's
   ANALYSIS. If the 6 s is a setup artefact, say so to Arpit before building —
   the cache may then save ~1 s, not ~6 s.
2. **Pre-register** the gain before building: delta ingest at rung-10000,
   unchanged corpus, cache warm vs cold, interleaved repeats; bar named in
   advance.
3. Build: where the cache lives (`.fux/runtime/`, gitignored, rebuildable,
   L9/SR-LOCKS), its key (above), eviction, and that a cold or missing cache
   gives **byte-identical** index output (L4).
4. **Tests that fail open if the key is short:** change one `pii.toml` rule →
   every affected file re-redacts; change the redactor version → all re-redact;
   corrupt a cache entry → re-redact, never trust it.
5. Records: SR-INGEST / SR-MAINTENANCE 1a-3, SR-CACHE (a new cached plane),
   the `fux-pii` skill if user-visible; B-002 closes or repoints with the
   measured number. Node needs nothing (it never ingests) unless T2's
   `fux build` touches redaction — check.
