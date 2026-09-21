---
type: OpenItem
id: W-199
title: "W-199 — fetcher routing: a URL resolves to a fetcher the way a file resolves to a decoder"
description: "Arpit's ask 2026-09-18 — build fetchers the way decoders are built: a module claim (`ROUTES`), a committed binding (`[sources.url.routes]`), a per-line pin (`fetch=`), one resolver, `fux doctor` findings. Key is the URL host. Pattern in work/proposals/fetcher-routing.md. Ruled 2026-09-20 (D1-D4); D1-D4 and three doctor rows built the same day, and DoD 10 -- the `decoder=` half of the pipe -- built 2026-09-21. CLOSED, all ten met."
status: closed
ruled: 2026-09-20
closed: 2026-09-21
lane: agent
timestamp: 2026-09-18T00:00:00Z
filed: 2026-09-18
ball: agent
---

## ✅ CLOSED 2026-09-21 — DoD 10 SHIPPED, so all ten are met

**The `decoder=` half of the pipe is built.** Every URL line now states
`decoder=<stem>` beside its `fetch=<stem>`; `fux add` observes the response's
`Content-Type` on its one fetch and writes the stem, refusing rather than
guessing; ingest decodes by the **declared** stem and never reads a header for
routing again.

| | what landed |
|---|---|
| **grammar** | `Attribute("decoder", …, required=True)` on `URLS`, validated by `_url_decoder_reason` — which refuses an **empty** value, the one difference from the `types` grammar. `Attribute.required_hint` so each required attribute names its own fix. |
| **the plane** | `decode.decoder_named(stem, root)` (consumer, then built-in; **never** the `[decoders]` table), `decode.decode_with`, `Decoder.primary`, and `prose` reserved — `.fux/decoders/prose.py` is refused at registry build. |
| **ingest** | `_decode_fetched(raw, decoder, url, root)`; `propose_decoder` carries the old header-then-extension ladder to `fux add`; `decoder_rel_path` keeps the URL's suffix when the decoder claims it (`csv`/`mail` branch on it); `acquired_ext` names a retained blob by the declared decoder. |
| **the floor** | `refusals.MAGIC_BY_DECODER` — the body is checked against the **line's** format first, the header second. |
| **ask time** | `urlsrc.declared_decoder(root, loc)`, read by `refer/source.py` and `enrich.py`, so an ask-time decode is identical to the ingest-time one **by construction**. |
| **CLI** | `fux add --decoder <stem>`, mandatory with `--no-fetch`, and `decoder=<observed>` in a `--dry-run` preview so the dry run still opens nothing. |
| **doctor** | `url decoders` (error) and `observed types` (warn) — **the second is W-200's second provenance finding**, which had no field to read until now. |

**Records:** SR-URL-LIST 13/17 + the attribute table, SR-FETCHER 17, SR-DECODE 21,
SR-URL-INGEST 6a, SR-REFUSAL, SR-ACQUIRED, SR-CLI, SR-DOCTOR (two rows),
SR-REFER, SR-URL-FRESHNESS, SR-ENRICH, SR-NODE-SEARCH, SR-DOTFUX, SR-DIR-LIST,
SR-ARCHIVED-CONTENT, SR-PII, SR-OUTPUT. GLOSSARY gains *the pipe*.

**Tests:** `tests/ingest/test_url_decoders.py` (29),
`tests/decode/test_decoder_named.py` (12),
`tests/test_doctor_url_decoders.py` (11),
`tests/test_add_observes_the_decoder.py` (16), plus the declared-decoder half of
`tests/ingest/test_refusals.py` and one e2e refusal case. ~80 URL-line fixtures
across 16 files were rewritten, not exempted.

🔴 **Four things this half cost, each named rather than discovered:**

1. 🔴 **`fux add <url>` opens the network TWICE** — once to observe the type,
   once in the ingest that follows, because the line must exist before
   `fux ingest` will fetch for it. `--decoder` skips the probe, and so does
   re-adding a line that already declares one. The alternatives were a window
   in which the committed file does not load, or a second way for bytes to
   enter the index.
2. 🔴 **`fux add` on a URL that is DOWN now writes no line at all** and exits 1.
   It used to write the line and report *"the line is written; the fetch
   failed"* — recording and fetching are separate outcomes (SR-CLI decision 3),
   and that separation cannot survive an attribute whose value comes from the
   fetch. The message names `--decoder <stem>` as the offline route.
3. ⚠ **The break is wider than `fetch=`'s.** No line written before today
   carries `decoder=`, because there was no attribute to write — so **every**
   existing `.fux/sources/urls` stops loading, where `fetch=`'s break only
   reached hand-written lines.
4. ⚠ **One resolution changed answer by one extension.** `decoder_rel_path`
   prefers the URL's own suffix when the declared decoder claims it, so a
   `.tsv` URL served as `text/csv` now decodes tab-separated where the header
   ladder read it as one comma-separated column. Better, and still *changed*.

⚠ **What was NOT done, and is not owed by this item:** SR-FETCHER decision 2's
bare-`str` transition ramp still contradicts *"a fetcher emits a format a
decoder reads"*. Its cost was never measured and removing it breaks every
consumer fetcher written before 2026-08-26, so it stays — named in SR-FETCHER
17d rather than left as silence (this item's §Open question).

**Addendum 2026-09-20 (W-206 review) — one spec, two rulings that compose.**
[`proposals/fetcher-routing.md`](../proposals/fetcher-routing.md) is the **pipe**
ruling of 2026-09-18 (`decoder=<stem>` **required** on every URL line, written once
at `fux add`, no default, break on old lists); this item is the **routing** ruling
of 2026-09-20 (`fetch=<stem>` mandatory, resolved routes → claims → refuse). Its
edge case 14 ("no host table") is **superseded** by D3 above; everything else in
its §2–§3 (16 cases, not twenty) stands and is part of this spec. **DoD gains
line 10: `decoder=` per the pipe ruling** — `fux add` fills it from `--decoder`
or the response's `Content-Type` through the decoder registry, refuses when
nothing maps; ingest decodes by the declared stem; `fux doctor` checks every
`decoder=` resolves. The W-200 provenance finding this item owes reads that field.

## ✅ D1–D4 AND THE DOCTOR ROWS ARE BUILT — 2026-09-20 (Claude Code)

**Shipped, in the ruled order D2 → D1 → D3 → D4 → doctor.** DoD items **1–9 are
met**; ⚠ **item 10 — the `decoder=` half of the pipe ruling — was NOT built that
day** and is why this item stayed open. It arrived in the addendum above during
the same session and was outside the prompt that built this. **It shipped
2026-09-21** — see the closing block at the top.

| | what landed |
|---|---|
| **D2** | `[sources.url] fetcher` **deleted** — refused by name, `CHANGELOG` under *Removed — BREAKING*. `fetch=` is a **required** attribute: a line without one fails to parse, naming the line and the word to add. |
| **D1** | `fux add --fetch <stem>`; without it the routes table then the module claims resolve one, and **nothing matching REFUSES**, naming the host tried and the stems on disk. |
| **D3** | `ingest/routes.py` — four pattern shapes, `re:` compiled **and anchored at load**, claims read with `ast` and never imported, collisions refused rather than sorted. |
| **D4** | `.fux/index/REGISTER`, committed, L3-bound; `ingest/register.py`. |
| doctor | `fetcher routes`, `pinned fetchers`, `register`. |

**Records:** SR-FETCHER 16, SR-URL-LIST 16, SR-CONFIG 16, SR-INGEST 22,
SR-DOCTOR's three rows, SR-CLI, SR-DOTFUX, SR-MERGE-DRIVER. GLOSSARY gains
*route · pin · claim · register*. Templates carry a commented `ROUTES` example,
twins refreshed, the two agent guides re-copied into all three vendor trees.

🔴 **Four things this spec did not predict, each found by a test:**

1. 🔴 **The register conflicted on merge.** It is committed inside
   `.fux/index/`, where the merge driver was bound to `*.jsonl` alone — so a
   merge that resolved **every shard cleanly** conflicted on the register, which
   is precisely the *machine planes never conflict because two people worked at
   once* property the driver exists for. Fixed by binding it and by passing
   **`%P`**: `%A` is a temp file whose basename tells the driver nothing.
   ⚠ **A repo registered before today passes three arguments and will refuse a
   register rather than merge it** — `fux hooks` re-registers.
2. 🔴 **The ruling's `outcome` column could not survive its own L3 rule.**
   `indexed` then `reused` is what it says on two runs from identical sources,
   which breaks the byte-identity the same decision requires. **`kind` replaced
   it**; the run-shaped outcome is what W-200's ledger already carries.
3. 🔴 **`fux add` was silently re-routing an existing pin.** Re-adding a URL to
   change its `ttl` overwrote its `fetch=` with whatever the table now said —
   the opposite of D1's *every line is a pin*. An existing line's `fetch=` is now
   left alone. Found by `test_an_unflagged_attribute_keeps_what_the_line_already_said`.
4. ⚠ **A doctor detail quoted a `FuxError` into its text**, and a `FuxError`
   message may hold an em dash — which crashes `fux doctor` on a Windows console
   exactly when the repo is already broken. The row now says *see that row*.

⚠ **"Node: no change" held, and the twin gate still fired.** `sourcelist.mjs`
is the `dirs` half only, so nothing about `fetch=` reaches it — but Python's
`parse` gained a generic required-attribute check, and a `dirs` attribute made
required later would have Python refusing a line Node accepts, with
`query/__init__` degrading to *no archived directories* and the two readers
returning different archived sets from one file. **The concept is ported as a
dead branch** rather than exempted.

⚠ **What the test fixtures cost, stated:** ~110 cases across 14 modules carried
either the deleted key or a bare URL line. They are rewritten, not exempted.

---

## ✅ RULED 2026-09-20 (Arpit, Cowork) — D1, D2, D3 and a fourth deliverable

**D1 — `fetch=` is never empty and never defaulted.** *"The set should never be
empty. It should be a mandatory argument when we are doing an add so that the
fetcher gets defined."* So: every URL line **states** `fetch=<stem>` (SR-URL-LIST
decision 12 stands, unnarrowed); `fux add` writes the stem it **resolved** —
`--fetch <stem>` if given, else the routes table / module claims (D3) — and
**refuses** when nothing resolves, printing the hosts it tried and the fetcher
stems on disk. The recommended *routed = empty* form is **rejected**. ⚠ What
this gives up, said aloud: a route changed later does not move an existing line
— every line is a pin. `fux doctor` gains a finding *"N line(s) pin a fetcher the
routes table would now resolve differently"*, and the consumer edits.

**D2 — no default fetcher; break.** *"There is no default fetch. It is a
mandatory argument. About backward compatibility, let it break."* So:
`[sources.url] fetcher` is **deleted** from `config.py`, the schema, the
template and this repo's `fux.toml`; a line without `fetch=` fails to load with
an error naming the line and the fix; no rewrite, no lenient read. Called out in
`CHANGELOG.md` under *Removed — BREAKING* (the W-177/W-194 shape) and one line
in `README.md`. Existing lines that say `fetch=http` are valid pins and keep
working.

**D3 — module claims, yes; patterns may be regex.** *"I agree with what is
recommended. We can have a regex kind of way where a default fetcher can be
defined."* So: `ROUTES` read with `ast`, never imported; the routes table and a
`ROUTES` claim accept the three host shapes **and** a `re:` prefixed pattern
(`"re:^.*\\.sharepoint\\.com$" = "cdp"`), compiled at load, anchored, matched
against the normalised host. **Two patterns matching one host is a hard error**
naming both — there is no specificity order between two regexes, so ambiguity
is refused, not sorted. The table is where a *default-by-pattern* lives; there is
no default-by-nothing (D2).

**D4 — a committed register of what was ingested.** *"A log file should be
generated of every document that is indexed, and because we are maintaining the
index we should maintain that log file as well — today there is nowhere we
document what files and URLs were ingested."* W-200's
`.fux/runtime/ingest-log.jsonl` is gitignored and advisory; this is different:
**`.fux/index/REGISTER`** (name provisional), committed beside the index, one
sorted line per document — `loc · sha · decoder@version · fetcher (URLs) · outcome`.
🔴 Bound by **L3**: no wall clock, no run id, sorted by `loc`, byte-identical
across runs from the same sources — it is derived from the same inputs as the
index and a test asserts `fux ingest` twice writes it once. Bound by **L2**: paths
and hashes, never content. **Not L8**: it records the corpus, not who asked. SR-INGEST
gains the decision; `fux doctor` compares it to the ledger plane and reports
drift.

**Ball → 🟢 `agent`.** Nothing here waits on Arpit. Build order: D2 → D1 → D3 →
D4 → doctor rows, one pre-registration for the byte-identity claims (D4 and the
*no routes = unchanged* claim of DoD 8). **DoD items 1, 2, 6 and 8 below are read
through this block where they differ.**


# W-199 — fetcher routing

**Model: Opus** — it changes a list-grammar default that every generated line
carries, adds a config key, adds a resolver with a specificity order, adds two
doctor checks, and amends four records. The wrong default silently pins every
existing repo.

🔴 **FILED INTO THE INBOX 2026-09-20.** This item's queue row read `🟢 agent`
from the day it was written, while its own frontmatter said `ball: arpit` and
its §Decisions hold three unruled calls. **The row was wrong and the file was
right**; the row now reads `🔴 arpit` and D1–D3 are in *Blocked on Arpit*.
⚠ **Nothing was built against the recommended defaults**, because D1 changes
what every generated URL line says and hazard 1 is explicit that building on the
old default makes every route dead on every existing line **while the tests pass
anyway** — the W-83 class.

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
`host:port` — **and a fourth, `re:<regex>`, added by D3**. Most specific match
wins among the literals; a regex never competes and a collision is a hard error.

⚠ **The pipe proposal's §2–§3 are part of this spec, and the citation was wrong
in two ways** (corrected 2026-09-20, W-206 B3). It said *"the twenty edge
cases"*; there are **sixteen**, under
[`fetcher-routing`](../proposals/fetcher-routing.md) **§3 — Edge cases the
builder must handle**, with the grammar in **§2 — The pattern** (its
*"The line states both halves"*, *"How `fux add` fills the two attributes"* and
*"Precedence, for the record"* subsections). 🔴 **And its edge case 14 says
`ROUTES` was dropped** — true of the 2026-09-18 pipe ruling and superseded by
D3 above; that case now carries the supersession note.

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
10. ✅ **`decoder=` per the pipe ruling — BUILT 2026-09-21** (added 2026-09-20 by the
    W-206 review; [`fetcher-routing`](../proposals/fetcher-routing.md) §2).
    `fux add` fills `decoder=<stem>` from `--decoder` or the response's
    `Content-Type` through the decoder registry, and **refuses when nothing
    maps**; ingest decodes by the **declared** stem rather than re-deriving one;
    `fux doctor` checks every `decoder=` resolves. **A URL line without
    `decoder=` does not load** — the same break `fetch=` took in D2.

    **This is the half of the pipe ruling that `fetch=`'s half already has**, and
    the two were built five days apart because the routing ruling arrived in
    between. ⚠ **W-200's second provenance finding waits on this line** — *"M
    URL(s) whose declared `decoder=` disagrees with the last observed
    `content_type`"* reads the field this item has not yet written.

## In scope / out of scope

**In:** the grammar default, the config key, the resolver, the `ast` claim
reader, the two doctor checks, `fux add` flags, templates and their twins,
records, the fetcher/config/sources agent guides, GLOSSARY.

⚠ **One thing W-200 left waiting on this** (2026-09-20): `fux doctor`'s second
provenance finding — *"M URL(s) whose declared `decoder=` disagrees with the
last observed `content_type`"* — is **not built and not stubbed**. It is this
item's hook; it lands when D1–D3 are ruled and the routing exists.

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
