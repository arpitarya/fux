---
type: Analysis
title: "2026-08-19 — W-54 analysis: what the fixture found, and what it still cannot see"
description: "Four defects closed and verified offline; three findings the capture surfaced that are not W-54's, each with a repro command; two unresolved causes stated as unresolved."
timestamp: 2026-08-19T00:00:00Z
---

# 2026-08-19 — W-54 analysis

**Method.** [`evidence/fixture.sh`](evidence/fixture.sh) builds a repo from
nothing, with `fux setup` and no hand-written fetcher, then runs the whole URL
path offline. The capture is in [`report.md`](report.md).

**The headline is not a number.** It is that `fux ingest --refresh-urls`
followed by `fux build` exits 0 on the documented, L5-mandated default — which
it did not before this change, in any repo, ever.

---

## What closed

| defect | how the capture shows it closed | repro |
|---|---|---|
| **W-47** hashed meta wrote an index no build accepts | `fux build` exit 0, manifest present, `analyzer` still `v1` | `fixture.sh && fux ingest --refresh-urls && fux build` |
| **W-49** a URL fragment was silently truncated | `url:…/handbook#oncall` is in the index as itself | `fux url` then grep the shard for `#oncall` |
| **W-49** two fragment-differing URLs collapsed into one | both `#oncall` and `#deploys` are records, with different `wlen` | report §5 |
| **W-51** `DEFAULT_FETCHER` named a file that did not exist | `fux setup` writes both, from wheel package data | `fux setup` in an empty git repo |
| **W-53** `dirs` shape diverged from `urls` | both lists parse through one reader; the fixture writes both | `fux ingest` with only `.fux/sources/dirs` |

**The differential harness has now seen a hashed record**, both in the unit
suite (`tests/derive/test_differential.py::test_a_corpus_holding_a_hashed_record_builds_and_agrees`)
and here across five queries at `top=20`. That gap is the whole reason W-47
survived: the law was enforced, and never over the corpus that broke it.

---

## Findings this capture surfaced that are **not** W-54's

### 1. `fux doctor` does not check the source lists — and now obviously should

Doctor validates the `.fux/` layout and the accelerator. It says nothing about
whether an entry in `.fux/sources/dirs` exists on disk, or whether a URL line
was written by fux. Both checks are named in accepted records
([ADR-DIR-LIST](../../../docs/adr/0022_dir-list.md) §Consequences,
[ADR-URL-LIST](../../../docs/adr/0018_url-list.md) decision 13) and neither is
built. `fux url` reports the completeness check; `fux doctor` is where it
belongs, because that is the command a person runs without being asked.

```bash
# repro: a dirs entry naming a directory that is not there
printf 'docs\nnope\n' > .fux/sources/dirs
fux doctor      # today: all [OK]
fux ingest      # error: configured source not found: 'nope'
```

**Proposed:** two `warn`-level doctor checks. Small, and it fits the verb's
existing shape. **Not filed as an item yet** — it should ride with W-44, which
already touches the dirs list's semantics.

### 2. The `.fux/README.md` a fresh repo gets does not mention `dirs`

`ensure_layout` writes the README before `fux setup` runs, and the table
describes `sources/` correctly, but the prose section is about fetchers only.
A consumer's first read of their own `.fux/` does not tell them where the
corpus is declared. Cosmetic, and it is the first file a new user opens.

```bash
# repro
mkdir /tmp/r && cd /tmp/r && git init -q . && fux setup && grep -c "sources/dirs" .fux/README.md
# expect today: 0
```

**Proposed:** one row's worth of prose in `_readme()`. Trivial, deferred to
avoid mixing it into W-54's commits.

### 3. Two fetchers means one HTML→markdown pass duplicated in two files

`http.py` and `cdp.py` each carry the full converter, and a test asserts they
produce identical output. That test is the mechanism keeping them honest, and
it only fires when someone runs the suite after editing a *template* — it
cannot see a consumer's edited copy, by design.

This is **accepted, not a defect**: a fetcher that imports another fetcher is a
chain, and ADR-FETCHER decision 4 refuses chains. The cost is stated so nobody
later "fixes" it by factoring the converter into `src/fux/` — which would put
HTML parsing inside the engine and breach the adapter cap through the back
door, exactly the way `[sources.url.config]` exists to prevent for tunables.

---

## Unresolved

- **Nothing here exercises real HTTP.** `http.py`'s `fetch` — `urllib`,
  redirects, charset decoding, the `MAX_BYTES` guard — is covered only by
  reading it. The unit tests exercise the pure parts (the converter, the
  `configure` hook) because a test that opens a socket is a test that fails in
  CI for reasons unrelated to fux. **Stated as unresolved rather than papered
  over**: the first consumer to point `fetch=http` at a real server is the
  first real exercise of that function.
- **The `archived=` declaration is parsed and unread**, so this run says
  nothing about whether declaring a directory archived produces the right
  behaviour — there is no behaviour yet. That is
  [ADR-DIR-LIST](../../../docs/adr/0022_dir-list.md) decision 10 working as
  intended, and W-44 owns the instrument that will close it.
- **The two-fetcher grouping is verified for correctness, not for cost.** Five
  URLs across two fetchers imports two modules and brackets two sessions. At
  10⁵ URLs across two fetchers that is still two imports — but nobody has run
  it at that scale, and the `connect`/`close` cost of a real CDP session per
  group is not measured anywhere.

---

## What changed in the instrument itself

The 2026-08-18 fixture reproduces the pre-W-54 surface and was **not edited**.
Rewriting a filed run's evidence so it no longer reproduces that run's numbers
falsifies the run — a filed measurement is superseded by a newer measurement,
never by an edit. The live citations in ADR-URL-LIST and ADR-DOTFUX are
repointed at this run's fixture in the same change.
