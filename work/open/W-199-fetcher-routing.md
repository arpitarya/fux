---
type: OpenItem
id: W-199
title: "W-199 — fetcher routing: a URL resolves to a fetcher the way a file resolves to a decoder"
description: "Arpit's ask 2026-09-18 — build fetchers the way decoders are built: a module claim (`ROUTES`), a committed binding (`[sources.url.routes]`), a per-line pin (`fetch=`), one resolver, `fux doctor` findings. Key is the URL host. Pattern in work/proposals/fetcher-routing.md. Three decisions are Arpit's before it is buildable. RATIFIED IN SHAPE, NOT BUILT."
status: open
lane: agent
timestamp: 2026-09-18T00:00:00Z
filed: 2026-09-18
ball: arpit
---

# W-199 — fetcher routing

**Model: Opus** — it changes a list-grammar default that every generated line
carries, adds a config key, adds a resolver with a specificity order, adds two
doctor checks, and amends four records. The wrong default silently pins every
existing repo.

⚠ **RATIFIED IN SHAPE, NOT BUILT.** The pattern is
[`work/proposals/fetcher-routing.md`](../proposals/fetcher-routing.md); this
file is the spec and the state. No `src/`, `node/` or `tests/` line has changed.
🔴 **Three decisions below are Arpit's, and D1 changes what the build writes
into every URL list — do not start before it is ruled.**

## The ask

> **Arpit, 2026-09-18:** *"Similar to how we have formats for TOML, we have
> decoders and they are mapped to extensions. I want to build fetchers in a
> similar way. Create an architectural pattern and then create a work document
> for it. … Take care of the edge cases."*

## The shape, in one table

| layer | decoders (today) | fetchers (this item) | wins over |
|---|---|---|---|
| pin | — | URL line `fetch=<name>` | everything |
| binding | `.fux/formats.toml [decoders]` | `fux.toml [sources.url.routes]` | claim, default |
| claim | `EXTENSIONS` in the module, read by import | `ROUTES` in the module, **read from source with `ast`, never imported** | default |
| default | — | `[sources.url] fetcher` | — |

Key = the URL's **host**, in three pattern shapes: `host`, `*.host`,
`host:port`. Most specific match wins; an identical pattern in two places is a
hard error. Full grammar, normalisation and the twenty edge cases are in the
proposal §2–§3 and are **part of this spec**, not background.

## 🔴 Decisions for Arpit

**D1 — what a generated line says about `fetch`.** Recommended: the attribute's
default becomes `""` (*routed*), so `fux add` / `fux ingest` stop writing
`fetch=http` and a written `fetch=` is a **pin** the human meant. This reverses
`sourcelist.py:333`'s 2026-09-15 comment and narrows SR-URL-LIST decision 12
the way `decoder=` already did. Alternative: keep writing the *resolved* stem
into every line at add time — the table then acts only at `fux add`, and
changing a route later means editing every line, which is the fifty-copies
problem this item exists to remove.

**D2 — migration of existing lists.** Every line fux has written says
`fetch=http`, and fux cannot tell a generated pin from a meant one. Recommended:
**no automatic rewrite** — `fux doctor` gains a finding *"N URL line(s) pin
`fetch=http`; routes never apply to a pinned line"* and names the one-line
fix; the consumer edits. Alternative: a one-shot `fux ingest --unpin-default`
that strips `fetch=<the source default>` only — explicit, but it is fux
rewriting a committed file's meaning, which the repo has refused before.

**D3 — module claims at all.** Recommended: yes, `ROUTES` read with `ast`,
because it is the half of the decoder pattern that makes *drop a file in and
it works* true, and the read-as-text precedent exists in
`doctor._fetcher_capabilities`. Alternative: table-only — one fewer mechanism,
and a consumer's own fetcher is reachable only after a `fux.toml` edit.

Two smaller calls, decided here unless he objects: **collisions are hard errors**
(stricter than decoders, because the wrong session produces a plausible index);
**the shipped templates claim nothing** (adapter cap).

## Definition of done

1. `Attribute("fetch", …)` has the default D1 rules; `render_line` behaves per
   D1; a hand-written list without `fetch=` reads as routed. Pins round-trip
   byte-identical.
2. `[sources.url.routes]` is a `dict[str, str]` in `config.py`'s `UrlSource`,
   declared in the config schema and the `fux.toml` template (commented
   example), validated at load for the three pattern shapes with a named error
   for anything else (proposal §3 items 6–7).
3. `urlsrc.resolve_urls()` is the **only** resolver: pin → binding → claim →
   default, with the specificity order and the collision / redirect / missing-
   file errors of proposal §2. `refer_answer._load_fetchers` is asserted to
   reach it through `resolve_urls` and nothing else.
4. Claims are read by a new `urlsrc.claims(fetchers_dir)` using `ast` on
   `ROUTES` — literal tuple/list of `str` only; anything else is a hard error
   naming file and line; no `ROUTES` = no claims. **No import anywhere on the
   resolve path**, gated by the same monkeypatch shape as
   `tests/test_doctor_fetcher_bindings.py::test_it_never_imports_a_fetcher`.
5. `fux doctor` gains `fetcher routes` (a route naming no file is a failure; a
   route matching no listed URL is a finding; a module-claim collision is a
   failure) and the D2 pinned-lines finding. Both offline, never importing.
6. `fux add <url>` reports the resolved fetcher, fetches through it, and writes
   the line per D1. `--fetch <name>` is added; `--cdp` / `--http` remain as
   aliases.
7. Templates: `http.py.txt` and `cdp.py.txt` docstrings show a **commented**
   `ROUTES` example and say the templates claim nothing and why. Byte-identical
   twins under `.fux/fetchers/` in this repo updated with them.
8. A repo with no routes table and no `ROUTES` behaves byte-for-byte as before,
   **except** the D1 rendering change — and a test states that exception.
9. Records, skills and docs below are amended in the same change.

## In scope / out of scope

**In:** the grammar default, the config key, the resolver, the `ast` claim
reader, the two doctor checks, `fux add` flags, templates and their twins,
records, the fetcher/config/sources agent guides, GLOSSARY.

**Out — filed as their own items if wanted:**

- **Scheme routing** (`s3://`, `sftp://`). `_url_reason` admits only `http(s)`;
  opening it is a URL-grammar change with its own record. The specificity
  order already leaves the slot (proposal §2).
- **Path-prefix routes** (`contoso.sharepoint.com/sites/hr`). A route is a fact
  about a host; a path is a fact about a document, which is the line's job.
- **Automatic escalation** of any kind. SR-FETCHER decision 5, untouched.
- Anything in `node/` — there is no fetcher seam there (`refer/source.mjs`).

## Key files

| area | files |
|---|---|
| grammar | `src/fux/ingest/sourcelist.py` (`URLS`, line 333 comment, `render_line`, `_fetcher_reason`) |
| config | `src/fux/config.py` (`UrlSource`, `fetcher_config`, the schema), `src/fux/templates/fux.toml.txt`, `fux.toml` |
| resolver | `src/fux/ingest/urlsrc.py` (`resolve_urls`, `fetcher_for`, new `claims`, new `route`) |
| answer path | `src/fux/query/refer_answer.py::_load_fetchers` (assert, no copy) |
| doctor | `src/fux/doctor.py` (beside `_fetcher_bindings`, `_fetcher_config_tables`, `_fetcher_capabilities`) |
| CLI | `src/fux/cli.py` (lines ~477–485, `--fetch`), `src/fux/sources.py` (the add verb) |
| templates | `src/fux/templates/{http,cdp}.py.txt` ↔ `.fux/fetchers/{http,cdp}.py` (byte-identical) |
| agent guides | `src/fux/templates/agents/FETCHER-SKILL.md`, `CONFIG-SKILL.md`, `SOURCES-SKILL.md`, `rule-/steering-/*-fetcher-files*` → regenerate `.agents/`, `.claude/`, `.kiro/` (decision 15 traps: edit the template, re-copy, ≤1200 B pointers, no `: ` in descriptions) |
| docs | `docs/GLOSSARY.md` (*route*, *pin*, *claim*), `docs/handbook.html` fetcher section |

## Records amended in the same change

- `0117_fetcher` — new decision **16**: routing (the four layers, the key, the
  specificity order, collisions, claims-read-not-imported, templates claim
  nothing). Decision 5's *declared, never detected* gains a sentence saying a
  host map is declared.
- `0116_url-list` — decision 12's empty-default narrowing extended to `fetch`
  per D1; decision 13 unchanged and cited.
- `0113_config` — the `[sources.url.routes]` key, its shape, and that it is a
  binding not a config sub-table (it is read by fux, unlike `[sources.url.config]`).
- `0152_doctor` — the two new checks.
- `0139_decode` — one cross-reference line: the pattern now has a second
  instance, and `_bind`'s extend/redirect asymmetry is cited from there.
- `records/README.md` / `DOC-REGISTRY.md` rows; `work/proposals/fetcher-routing.md`
  → `status: graduated`.

## Tests

- **New:** `tests/ingest/test_fetcher_routes.py` — pattern grammar (all of
  proposal §3 items 1–7, 11, 12), specificity order, collision error, redirect
  refusal, extend allowed, missing file error, D1 rendering + round-trip, pin
  wins, default when nothing matches, byte-identical behaviour with no routes.
- **New:** `tests/test_doctor_fetcher_routes.py` — the failures/findings, the
  pinned-lines count, and a `never imports` guard.
- **New:** an assertion that `refer_answer._load_fetchers` obtains
  `fetcher_path` via `urlsrc.resolve_urls` (source-order or monkeypatch).
- **Rewrite:** `tests/ingest/test_urlsrc.py`, `test_sourcelist.py`,
  `tests/test_source_verbs.py`, `tests/test_setup.py` (template twins),
  `tests/test_setup_agents_guides.py`, `test_sr_config_keys` (a config **key**
  is added this time — the parser must see it).
- ⚠ Run under `pytest.ini` on the Mac (`uv run pytest -q tests`, then
  `tests_e2e`); the bridge VM has no pytest and the full suite has exhausted
  inodes there before.

## Hazards

1. **D1 before code.** Building with the old default makes every route dead on
   every existing line and the tests will pass anyway — the exact W-83 class.
2. **Never import to resolve.** `_fetcher_reason`'s docstring is the law here;
   `ast` only. The doctor monkeypatch test is the gate.
3. **Collision is an error, not a sort.** Do not copy `registry()`'s
   last-consumer-wins loop; the reason is in the proposal §2.
4. **Twins.** Templates ↔ `.fux/fetchers/`; agent templates ↔ three vendor
   copies; a doc's Mermaid ↔ SVG if any figure names the fetcher path.
5. **The table is read by fux; `[sources.url.config]` is not.** Keep them in
   separate paragraphs of SR-CONFIG or the adapter-cap argument for `config`
   gets read as applying to `routes`.
6. **Wildcard does not match apex.** Say it in the template docstring, the
   skill and the error text; it is the first thing a consumer will get wrong.
