# Renumber + law records + L1 amendment — what landed, what's left

**2026-09-06.** Nothing is committed to git. All changes are working-tree writes.

---

## 1. What is on disk now

**`docs/adr/` is live again — 63 files, verified zero broken links.**

| range | what |
|---|---|
| `0001` | **ADR-LAWS** — now the *router*: the numbering, the no-restatement rule, and a link to each law's record |
| `0002`–`0009` | **ADR-L1 … ADR-L8** — one record per law, newly authored |
| `0010`–`0060` | every existing record, previous order preserved |

**Renumber, done mechanically and verified:** 996 path links, 52 register rows, 51 `title:` numbers, 6 `archive/adr/` → `archive/adr-old/` paths. **Zero unresolvable links across all 63 files.**

**Seven bare `ADR-NNNN` strings were deliberately NOT rewritten** — two are sample ranking *output* in ADR-RERANK (document ids in a corpus, not citations), two are the register quoting `"ADR-0004"` as an example of the defect, one is append-only history in `RULE-SINCE`. All correct as they stand.

**L1 amended** in `CLAUDE.md` (normative text + §Litmus), `README.md` (Laws line + a clause on the wheel-size number), `pyproject.toml` (comment only — **`dependencies` is still `[]`**).

---

## 2. Run this next — the repo-wide link sweep

Everything outside `docs/adr/` still points at old numbers. `relink-repo.py` fixes it. From the repo root:

```bash
python3 relink-repo.py            # dry run — read the report
python3 relink-repo.py --apply    # write
uv run pytest -q tests
uv run pytest -q tests_e2e
```

Put `relink_map.json` beside it. It ends with a verification pass that reports any ADR reference that does not resolve on disk; **that number must be 0 before you commit.**

**It deliberately skips four things — do not "fix" them:**

| skipped | why |
|---|---|
| `work/WORKLOG.md` | append-only, 810 KB. Its old numbers are historical ordinals and may not be rewritten |
| `work/regression/` | frozen measured evidence; a report is never edited |
| `archive/` | retired by definition |
| `docs/adr/` | already rewritten and verified |

---

## 3. ⚠ Three things you need to decide, and one you need to check

### (a) The pin clause — I did NOT add it

L1 now permits dependencies. **Byte-identity across machines becomes a function of dependency resolution on the ingest path**, and the differential harness cannot catch it — it compares scan against accelerator *on one machine*. The failure is two developers, same commit, different root hash, weeks later.

I put the *shape* of the rule in `pyproject.toml`'s comment and in ADR-L1's veto condition, but **the normative L1 text does not require pinning.** Say the word and I'll add it — `==` for anything ingest touches.

### (b) `dependencies = []` is unchanged

The amendment changes what is *permitted*, not what is *installed*. **The first actual dependency is a separate change with its own ADR** — which is ADR-L1 decision 3, and it is also the only way a dependency test has anything to check.

### (c) W-82 ruling 7 is now overridden

*"A vacated ordinal is burned and never reused"* — the renumber closed both burned holes (`0017`, `0025`). The register's "number line" section is rewritten to record the override honestly, including what it cost and what could not be corrected. **This is your call recorded, not mine assumed.**

### (d) Another session was live in this repo

`NOW.md` read *"✓ W-115 chunking (183 green) · → Arpit: real suite + commit"*, and `WORKLOG`/`DOC-REGISTRY`/`OPEN-WORK`/`IMPLEMENTATION` were touched minutes before I started. **Ten ADRs had edits from it**, which I picked up by re-staging — but check `git status` before committing in case that session has more in flight.

---

## 4. Still owed — I could not do these from here

`device_bash` failed five consecutive times, so I could not run git, the test suite, or a repo-wide grep.

1. **The link sweep** — §2 above.
2. **`tests/test_l1_dependencies.py`** — the first test L1 has ever had. Draft in ADR-L1's veto condition; needs writing against your `pyproject()` helper.
3. **`work/DOC-REGISTRY.md`** — 63 rows to add or renumber. The sweep script fixes the *paths*; the row set still needs a human pass.
4. **`work/OPEN-WORK.md`** — a row for the dependency test and one for the pin decision.
5. **`work/INTERVIEW.md`** — the standing-constraints section still describes stdlib-only.
6. **`work/WORKLOG.md`** — entry below, to paste at the top.
7. **`tests/test_adr_ownership.py` / `adr_lib.py`** — check whether either hardcodes a number.

---

## 5. WORKLOG entry — paste at the top

```markdown
## 2026-09-06 — L1 amended; one ADR per law; the register renumbered

**Asked.** Remove the `$0`/stdlib-only law; then a record per law numbered from
`0002`; then, after Arpit moved `docs/adr/` to `archive/adr/` himself,
recreate the register.

**Done.**
- **L1 amended** (Arpit, two rulings). `$0` hardened into explicit
  free-and-open-source-only — no paid library, service, API or model, ever.
  `stdlib-only runtime` **removed**; dependencies ship packaged with no extras
  tier; numpy/pandas/scipy legal in harnesses. **The zero-dependency guarantee
  is withdrawn.** `CLAUDE.md` §Non-negotiable constraints + §Litmus, `README.md`,
  `pyproject.toml` comment. `dependencies` is still `[]`.
- **Eight law records authored**, `0002`–`0009`, ADR-L1…ADR-L8. **Rationale
  only** — `CLAUDE.md` remains the sole normative home and ADR-LAWS decision 3
  binds them like every other record.
- **ADR-LAWS keeps `0001` and became the router**; nothing was deleted from it.
- **Register renumbered** `0010`–`0060`. 996 path links, 52 register rows, 51
  title numbers, 6 archive paths, rewritten mechanically and verified: zero
  unresolvable links across 63 files.

**Decided.**
- **W-82 ruling 7 is OVERRIDDEN.** Both burned ordinals (`0017`, `0025`) are
  closed. The cost the ruling named was real and was paid; it was affordable
  only because the pass was scripted and verified.
- **WORKLOG and `work/regression/` are NOT relinked.** Append-only and frozen.
  Every bare number in them older than today names a different record now.
- **Law records carry rationale, not law.** The conservative reading of an
  ambiguous instruction, flagged for reversal if Arpit meant the other one.

**Open.**
- The **pin clause** — unpinned deps on the ingest path can break L3 silently
  and the differential harness cannot see it. Arpit's call.
- The repo-wide link sweep (`relink-repo.py`), DOC-REGISTRY, INTERVIEW,
  OPEN-WORK, and `tests/test_l1_dependencies.py`.
- **Nothing was tested.** `device_bash` failed five times; no suite was run.

**Next.** Arpit runs `relink-repo.py --apply`, then both suites.
```
