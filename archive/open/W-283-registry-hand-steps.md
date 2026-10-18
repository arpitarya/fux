---
type: Handoff
name: W-283
description: "Filed 2026-10-18 by Claude Code from W-282 Step 0's standing instruction: the three registry steps only Arpit's accounts can take before the first four-package release (PyPI trusted publishers for fux-core / fux-reader / fux-writer; the @fux-engine npm org; the first @fux-engine/reader publish), and his go for the release itself."
item: W-283
filed: 2026-10-18
filed_by: "Claude Code (Opus 5.5)"
updated: 2026-10-18
updated_by: "Claude Code (Opus 5.5)"
ball: agent
---

# W-283 — the registry steps before the four-package release

## At a glance

| step | what Arpit does | what it unblocks | state |
|---|---|---|---|
| 1 | On pypi.org, add a **pending trusted publisher** for each of `fux-core`, `fux-reader`, `fux-writer` | the release workflow can create and upload the three new packages | ✅ done |
| 2 | On npmjs.com, **create the free `@fux-engine` organization** | the scope `@fux-engine/reader` publishes under | ✅ done |
| 3 | **Publish `@fux-engine/reader` once by hand**, then add its trusted publisher | every later release publishes it automatically | ✅ done |
| 4 | Say **"release 4.0.0"** | an agent cuts it | ✅ ruled and cut 2026-10-18 — `v4.0.0` released; see *State after the release* |
| 5 | Re-run the failed publish jobs once 1–3 are done | the three role packages, then fux-engine 4.0.0, reach PyPI; the scoped package reaches npm | ✅ done — and 4.0.1 published all six names from the workflow |

**Why each is his hand and no agent's:** each is an action in his PyPI or npm
account, and step 4 publishes to two public registries, which cannot be undone.
**Filed by W-282's own rule** (Step 0, DoD 1): *"if it is not there when Step 3
is next, file it as its own 🔴 `arpit` item then."* Steps 1–2 of W-282 are
built and committed; this is all that stands between them and PyPI.

**Model:** NONE for steps 1–3 (his accounts); **Sonnet** for step 4 once he
says go — it follows [SR-WORK-RELEASE](../../records/0063_WORK-release.md)
mechanically.

## State after the release (2026-10-18, Claude Code)

Arpit ruled *"push publish everything and release a new major version 4.0.0"*.
`c54a5d81` passed CI (38/38, verdict saved) and **`v4.0.0` was released**;
[publish run 39115990157](https://github.com/arpitarya/fux/actions/runs/39115990157):

| registry | outcome | why |
|---|---|---|
| npm `fux-engine` | ✅ **4.0.0 published**, `latest` | unchanged path |
| PyPI `fux-core`, `fux-reader`, `fux-writer` | ❌ 400 *"Non-user identities cannot create new projects"* | the token came from fux-engine's publisher; a NEW project needs a pending publisher of its own — step 1 |
| PyPI `fux-engine` | ⏸ **skipped, by design** | it waits for the three above, so PyPI's latest stays 3.0.1, intact — never an engine pinned to packages PyPI lacks |
| npm `@fux-engine/reader` | ❌ 404 | no `@fux-engine` org — steps 2–3 |

**To finish, after steps 1–3:** `gh run rerun 39115990157 --failed`.
`skip-existing` makes it safe: the roles upload, then fux-engine 4.0.0, then the
scoped package. Then check `https://pypi.org/pypi/fux-engine/json` reads 4.0.0.

## Progress 2026-10-18, 16:10 (Cowork, in Arpit's signed-in Chrome)

- ✅ **PyPI pending publisher for `fux-core`** added (arpitarya/fux, `publish.yml`, env `pypi`).
- ❌ **`fux-reader` refused by PyPI:** *"A pending trusted publisher matching this
  configuration has already been registered for a different project name."*
  PyPI allows **one pending publisher per identical configuration**, so the
  three new projects cannot all be pending at once with one workflow and one
  environment. **Way through, no code change:** re-run the
  `publish-pypi-roles` job → it creates `fux-core` (the pending publisher turns
  ordinary, `fux_reader` then fails and stops the upload) → add the
  `fux-reader` pending publisher → re-run → add `fux-writer` → re-run; the
  `fux-engine` job follows on the last green run. The alternative — one
  GitHub environment per package — is a `publish.yml` change and a new tag.
- ⏳ **npm `@fux-engine` org:** Arpit clicks *Create* on `npmjs.com/org/create`
  himself (name `fux-engine`, free plan); an agent may not create it.
- **16:48:** ✅ `fux-core` 4.0.0 is live on PyPI (first re-run). ✅ npm org
  `fux-engine` exists (Arpit). ✅ PyPI pending publisher for **`fux-reader`**
  added. ⏳ next: re-run the roles job (creates fux-reader) → add the
  `fux-writer` pending publisher → re-run (fux-writer, then fux-engine 4.0.0) →
  first hand publish of `@fux-engine/reader` + its npm trusted publisher.

## Closed 2026-10-18 (Claude Code) — every step done

| | 4.0.0 | 4.0.1 |
|---|---|---|
| PyPI `fux-core` · `fux-reader` · `fux-writer` | ✅ re-runs of run 39115990157, one new project per pending publisher | ✅ run 39127620476 |
| PyPI `fux-engine` | ✅ attempt 6, after its publisher was re-added with environment `pypi` | ✅ run 39127620476 |
| npm `fux-engine` | ✅ | ✅ |
| npm `@fux-engine/reader` | ✅ Arpit's hand publish | ✅ run 39127620476, attempt 2, after the trusted publisher was saved |

**What it took, for the next new distribution:**

- **PyPI keeps one pending publisher per identical configuration**, so new
  projects sharing one workflow and one environment are created one re-run at a
  time.
- **While a pending publisher exists, the token PyPI mints is scoped to that
  pending project only** — so re-run with no other new project in the upload,
  and expect the others to be skipped as existing.
- **`fux-engine`'s original publisher did not carry environment `pypi`**: once
  the role packages' identical publishers existed, PyPI chose theirs and the
  token was *"not valid for project 'fux-engine'"* (403). Re-adding the
  publisher to `fux-engine` with exactly `arpitarya / fux / publish.yml / pypi`
  fixed it.
- **npm 404s an unauthenticated or untrusted `PUT`** — an expired `~/.npmrc`
  token on the hand publish, a missing trusted publisher on the workflow's —
  and caches a new package's *not found* for minutes after it exists.
- **The publish ordering held**: no `fux-engine` ever reached PyPI pinned to a
  role package PyPI lacked.

**Verified:** `pip install fux-reader==4.0.1` in a clean venv → `fux-core`
4.0.1 + `fux-reader` 4.0.1, `fux ask --help` runs, `fux ingest` refused naming
fux-writer. `pip install fux-engine==4.0.1` → all four at 4.0.1, both scripts,
all 25 verbs.

## Goal

The first release that publishes `fux-core`, `fux-reader`, `fux-writer` and
`fux-engine` to PyPI, and `fux-engine` and `@fux-engine/reader` to npm, on one
version, from `publish.yml` — with no upload failing for want of a publisher.

## Definition of done

1. **PyPI** — a pending publisher for each new project, with exactly these
   values (the same as `fux-engine`'s existing one):
   - owner `arpitarya`, repository `fux`, workflow **`publish.yml`**,
     environment **`pypi`**;
   - project names `fux-core`, `fux-reader`, `fux-writer`. A pending publisher
     also reserves the name until the first upload.
2. **npm** — `npmjs.com/org/create`, name **`fux-engine`**, free plan (public
   packages). `@fux` is another person's account, ruled out (W-282 F4).
3. **First publish by hand** — npm binds a trusted publisher to a package that
   exists, so the very first upload cannot come from the workflow:

   ```bash
   PYTHONPATH=src python -m fux.store.nodebundle node node/dist
   python scripts/npm-scoped.py node/dist node/dist-scoped
   cd node/dist-scoped && npm publish --access public --tag latest
   ```

   then on the package's settings page add a trusted publisher: GitHub Actions,
   `arpitarya/fux`, workflow **`publish.yml`**, environment **`npm`**, and tick
   *Allow npm publish* (the same three settings `fux-engine` has).
   ⚠ This publishes 3.0.1's bundle under the new name — harmless (same bytes
   as `fux-engine@3.0.1`), and the next release supersedes it.
4. **His go**, in his words, for the release. The agent then follows
   SR-WORK-RELEASE: bump `src/fux/__init__.py` and every parity site
   (`python scripts/check-version-parity.py` lists them — seven since W-282),
   a `## [4.0.0]` changelog section from `[Unreleased]`, the gated PR, and
   `gh release create v4.0.0` once CI's FULL verdict is green.
5. **Verified after publish:** `pip install fux-reader==4.0.0` in a clean venv
   runs `fux ask` and refuses `fux ingest` by name; `npm view @fux-engine/reader
   version` says 4.0.0.

## Blockers

Steps 1–3 are his accounts; step 4 is his word. W-282 Step 3 waits on all four.

## Record affected

[SR-WORK-RELEASE](../../records/0063_WORK-release.md) decision 15 already
states the four distributions and these three hand steps; the release changes
no record.

## Hazards

- **A missing publisher fails only its own upload.** PyPI's action uploads every
  file in `dist/`; a project with no trusted publisher is refused while the
  others land — a release half-published by design, which this item exists to
  prevent.
- **`skip-existing: true`** means a re-run after fixing a publisher uploads only
  what is missing — safe to re-run the publish job.

## Reference

- [W-282](W-282-reader-writer-packages.md) — the split, Steps 1–2 built.
- [`.github/workflows/publish.yml`](../../.github/workflows/publish.yml) — the
  four builds, `publish-pypi`, `publish-npm`, `publish-npm-scoped`.
- PyPI pending publishers: <https://docs.pypi.org/trusted-publishers/creating-a-project-through-oidc/>
