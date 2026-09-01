---
type: OpenItem
id: W-98
title: "W-98 — browser-session resource fetching + the acquired plane"
description: "Fux cannot ingest a SharePoint/M365 Excel URL: http.py sends no session and lands a login page in the index, cdp.py returns a DOM snapshot with a hardcoded text/html, and ingest discards raw after decoding. Four phases, four checkpoints: cdp.py returns the resource, engine-side refusal detection fails closed, a clock-free .fux/acquired/ plane retains source bytes, and a per-document ttl= drives re-fetch. Phase 1 is gated on an untested CORS spike."
status: open
lane: agent
timestamp: 2026-09-01T00:00:00Z
---

# W-98 — browser-session resource fetching + the acquired plane

**Model: Opus** for every phase. The spike is a gate call, the refusal
predicate's fail-closed semantics are a law-adjacent judgment, and four
records are rewritten in place — all four are cases where a wrong answer
returns confident and plausible rather than red. Phase 3's manifest and
eviction code alone would be Sonnet-executable against §9's test list; the
phases around it are not.

**One-liner:** Rebuild `cdp.py` to return the *resource* instead of a DOM snapshot, add engine-side refusal detection, retain source bytes in a new `.fux/acquired/` plane, and drive re-fetch from a per-document `ttl=`.

**Owner / executor:** Claude Code (local — this is only testable against a signed-in Chrome and a real tenant)
**Status:** Ready to build, **phased** — see §3
**Stress-tested:** Challenged on (a) packaging four ADR-sized features as one change, (b) whether the in-page fetch actually works against SharePoint, (c) "evict oldest" in a plane that has no clock. (a) survived only as a **four-phase split** — Phase 1 alone delivers the original goal with zero engine changes. (b) did **not** survive: the in-page `fetch()` may be CORS-blocked on SharePoint's download redirect, and nobody has tested it — Phase 1 now **starts with a spike**, and the rest of the plan is contingent on it. (c) produced two non-negotiables (ordering by `run_seq`, never evicting a blob whose URL is failing). **Residual risk: the spike. If CORS blocks the read, technique changes before anything else is built.**

---

## 1. Context & background

Fux cannot ingest a Microsoft 365 / SharePoint Excel URL today. Three separate reasons:

- `http.py` sends no session, so a share link returns a sign-in page with HTTP 200 — which decodes "successfully" as HTML and lands a login page in the index. Silent wrong answer, not an error.
- `cdp.py` does not download anything. It runs `Page.navigate` → `Runtime.evaluate("document.documentElement.outerHTML")` and returns `(html, "text/html")` with the type **hardcoded**. On an Excel URL that captures Excel Online's toolbar markup; the cells are painted to a `<canvas>` and are not in the DOM at all.
- Ingest discards `raw` after decoding, so nothing retains the original file. ARC is in-memory and dies with the process; `runtime/fetch-cache/` is a 300s throttle guard, off by default, and only fills at verify time.

Everything downstream already works: `_TYPE_EXT` maps the OOXML spreadsheet MIME to `.xlsx`, `decode/xlsxdoc.py` decodes it, and `validate()` + `UrlHealth.token_sha` already give change-detection. **The gap is entirely at acquisition.**

## 2. Definition of done

Per phase; each phase is independently shippable.

**Phase 1 — `cdp.py` returns the resource**
- [ ] Spike completed and recorded (see §8, Risk 1) before any fetcher code is written
- [ ] `cdp.py` `fetch(url)` returns real bytes plus the real Content-Type, not a DOM snapshot
- [ ] A SharePoint `.xlsx` share link ingests and `fux ask` returns cell content from it
- [ ] `LAUNCH_CHROME = False`; a missing Chrome fails with an actionable message
- [ ] `validate(url)` implemented via in-page HEAD → `ETag`, `None` when unavailable
- [ ] Navigation happens once per **origin**, not once per URL
- [ ] ADR-0020 (`0020_cdp-fetcher.md`) **rewritten in place** to describe what it does now
- [ ] CHANGELOG entry for the `fetch=cdp` semantic break

**Phase 2 — refusal detection**
- [ ] Structural checks in the engine, always on: landed-off-origin, declared-type vs magic bytes (`PK\x03\x04` for OOXML, `%PDF-` for PDF)
- [ ] ~~`.fux/refusals.py` loaded by path, contract `refused(url, final_url, content_type, raw) -> str | None`~~ **SUPERSEDED — it is `.fux/refusals.toml`, a declarative rules table.** A code predicate is explicitly deferred: it could open a socket, raise from anywhere, and fail in a way indistinguishable from *"this page is fine"*. The starter file that fux now writes is `src/fux/templates/refusals.toml.txt`; the original spec copy was archived on 2026-09-01 as [`archive/handoff/W-98-refusals-starter.toml`](../../archive/handoff/W-98-refusals-starter.toml) — **named, not cited**: the live specification is [ADR-REFUSAL](../../docs/adr/0051_refusals.md).
- 🔴 **BLOCKED 2026-09-01 — the spec trips an accepted record's veto condition.** Three of the nine conditions (`status`, `final_url_host`, `final_url_contains`) and the always-on `landed-off-origin` check put HTTP facts inside the engine. **[ADR-FETCHER](../../docs/adr/0019_fetcher.md) decision 13, ratified by Arpit 2026-08-28**, says fux *"never reads a status code, a header, or an error string"* — and its own veto check names *"`urlsrc.py` mentions a status code"* as proof the boundary regressed. ⚠ **Separately, the contract cannot deliver them anyway**: `fetch()` returns `(bytes, content_type)`, with no `final_url` and no `status`. Phase 1's `Resource` holds both, so `cdp.py` knows them — it has no way to say so.
- [ ] **Fails closed**: a predicate that raises, or a file that will not load, is treated as a refusal
- [ ] A refusal becomes `Skipped(reason=...)` carrying the predicate's own string
- [ ] Test fixture: a real captured SSO login page is rejected, a real workbook is not
- [ ] New ADR for the refusal contract

**Phase 3 — the acquired plane**
- [ ] `.fux/acquired/` created, `CACHEDIR.TAG`'d, listed **by name** in `.fux/.gitignore`
- [ ] Declared in `fuxdir.py` as a third category; `fux doctor` does not report it as undeclared
- [ ] `objects/<sha[:2]>/<sha256>.<ext>` + `manifest.json`, manifest written **once** at the end of `fetch_all`
- [ ] `keep` line attribute, default `false`, three-layer resolution
- [ ] Cap configurable in `fux.toml`; eviction by `run_seq`; **never** evicts a blob whose URL has `fail_streak > 0`
- [ ] `fux doctor` reports size, blob count, and evictions
- [ ] `fux remove <url>` drops the blob; `fux update` sweeps unreferenced blobs
- [ ] ADR-0003 (`0003_fux-directory.md`) rewritten for the third category; new ADR for the plane (draft at `docs/adr/0050_acquired-plane.md`)

**Phase 4 — freshness**
- [ ] `ttl=` line attribute accepting `30s` / `15m` / `1h` / `7d`, and bare `0` for always-fetch
- [ ] At ask time: TTL live → `cached`; expired → `validate()` first, fetch only on a changed/absent token
- [ ] Sixth verdict `as-ingested` when a fetch fails but the blob matches; **never** collapses into `current`
- [ ] `query/output.schema.json` carries the new verdict
- [ ] `fux update --failed` re-runs only entries with `fail_streak > 0`
- [ ] New ADR for URL freshness

**All phases**
- [ ] Documentation updated per §9.5
- [ ] `uv run pytest` green; no new third-party dependency anywhere in `src/`

## 3. Scope

**In scope:** the four phases above, in order. Each ends at a green test suite and a committed ADR.

**Out of scope — explicitly, do not add these:**
- **No `dl.py`.** The rebuilt `cdp.py` is the browser-session fetcher. Two fetchers total.
- **No OAuth, no Microsoft Graph, no device-code flow, no token storage, no app registration.** Auth is the browser's, borrowed. If the user is not signed in, the fetch **fails** — that is the design, not a gap to fill.
- **No opening of the `fetch` attribute enum.** `fetch=cdp` already parses; no third fetcher name is being added.
- **No `blob` field on the index record.** The record shape does not change. (`query/output.schema.json` does, in Phase 4 — that is the output schema, not the record.)
- **No offline re-decode from blobs.** Refreshing a URL document means re-fetching it. Keep the manifest and layout *capable* of it; do not build it.
- **No automatic escalation between fetchers.** A `fetch=http` line that returns a login page stays a `fetch=http` line that returned a login page, recorded as a skip. A human edits the line.
- **No new CLI verb.** `--failed` is a flag on the existing `fux update`.
- **No wall clock in the acquired plane.**

## 4. Current state

- Repo: `/Users/arpitarya/my_programs/fux`, `fux-engine` 2.0.0-alpha.4
- **Read first, in this order:**
  - `src/fux/ingest/urlsrc.py` — the fetcher contract, `fetch_all`, `_unpack`, `_decode_fetched`, `_TYPE_EXT`
  - `src/fux/templates/cdp.py.txt` — the file being rebuilt (the shipped template; `.fux/fetchers/cdp.py` is the consumer copy)
  - `src/fux/store/fuxdir.py` — `COMMITTED` / `DERIVED` / `DECLARED`, `derived_dir()`, `CACHEDIR_TAG`
  - `src/fux/ingest/sourcelist.py` — `ListSpec`, `Attribute`, `URLS`
  - `src/fux/maintain/urlstate.py` — `UrlHealth`, `fail_streak`, `run_seq`, the counters-not-clocks rule
  - `src/fux/refer/fetchcache.py` and `refer/freshness.py` — where the wall clock is allowed to live
  - `src/fux/refer/source.py` — verify-time resolution, the "a document fetched two ways is two documents" rule
  - `docs/adr/TEMPLATE.md`, `docs/adr/0003_fux-directory.md`, `docs/adr/0019_fetcher.md`, `docs/adr/0020_cdp-fetcher.md`
- **Patterns to reuse:** `derived_dir()` for creating a tagged directory; `urlstate.py`'s advisory-state shape for the manifest; `_decode_fetched`'s `(value, why)` return for the refusal matcher; `config.schema.json` for `refusals.schema.json`. ⚠ **Not `load_fetcher()`'s import-by-path** — there is no `refusals.py` to load; the rules are a committed TOML table read with `tomllib`.

## 5. Technical approach (decided — do not re-litigate)

1. **`cdp.py` returns the resource, never a rendering — via CDP interception, not an in-page fetch.** `Page.navigate` → `Fetch.enable` at `requestStage: "Response"` on a pattern narrowed to the target → `Fetch.requestPaused` → `Fetch.getResponseBody` → `Fetch.continueRequest`/`failRequest`. A rendered DOM carries nonces, timestamps and session ids, so its sha changes on every fetch — nondeterministic input to an engine that asserts byte-identical results. ⚠ **Amended 2026-09-01 (Arpit), on spike step 5's measurement.** This item read *"`Runtime.evaluate` with `awaitPromise: true` running an in-page `fetch(url, {credentials:'include'})`"* until then. That technique is **measurably incapable of the job**: CORS and CSP are page-level and an in-page fetch is subject to both (a no-`ACAO` cross-origin URL returned `TypeError` in-page and **8557 bytes** under interception), and a cross-origin in-page fetch sees only CORS-safelisted response headers, so **`ETag` is invisible and `validate()` could never have worked**. CDP is browser-internal and neither restriction reaches it. Evidence: §9, step 5.
2. **No `dl.py`.** Once `cdp` fetches resources, `cdp` and the proposed `dl` are the same file. The roster is two fetchers on one axis: *whose session*.
3. **Auth is the browser's.** No credentials are stored, read, or handled anywhere. Not signed in → fail loudly.
4. **Refusal detection is engine-side, not per-fetcher.** W-86 P8 removed conversion from the fetchers because it lived there as two hand-maintained copies nothing checked; per-fetcher refusal detection repeats that mistake, and a login page through `http.py` is exactly as poisonous as one through a browser.
5. **The refusal predicate fails closed.** `is_rate_limited` fails open because a false negative costs speed; here a false negative writes a login page into the committed index.
6. **Retention lives in `fetch_all()`**, so `http.py` gains it with zero lines changed.
7. **Order is load-bearing:** `_unpack` → refusal check → acquired persist → `_decode_fetched`. Never store a refusal.
8. **The blob sha stays off the committed record.** A sha on a committed record states a fact true on one machine only — two developers pull the same repo, one has the bytes, and the record claims both do. The url→sha map lives in the plane, gitignored and advisory, exactly as `url-state.json` is.
9. **`.fux/acquired/` is a third `fuxdir` category.** Gitignored like derived, but **not rebuildable** — only re-acquirable, and only while the source exists and the session holds. It cannot live under `runtime/`, whose contract is "rebuilt from the committed shards by `fux build`".
10. **The plane is clock-free.** `run_seq` only. The wall clock stays in `runtime/fetch-cache/`, per `fetchcache.py`'s stated invariant.
11. **A configured duration is policy, not a recorded observation** — so `ttl=1h` in a committed file does not breach that invariant, any more than `max_parallel = 4` does.
12. **`as-ingested` is a sixth verdict.** ADR-REFER decision 6's three-state guarantee exists so nothing collapses "we did not look" into "we looked and it was fine"; "we could not look, but the index is internally consistent" is a distinct position and needs a distinct name.

## 6. Non-negotiables / constraints

- **Zero third-party dependencies in `src/`.** Stdlib only. The WebSocket client is hand-rolled RFC 6455 on `socket` and stays that way. No `requests`, no `websockets`, no `playwright`.
- **`src/fux/` never opens a socket.** All network lives in consumer fetcher files under `.fux/fetchers/`. Tests assert this for `sources.py` and `refer/source.py`; the refusal predicate gets the same assertion — it is pure over bytes, with no network and no I/O.
- **No wall clock outside `runtime/fetch-cache/`.** "Evict oldest" means **oldest by `run_seq`**, with a deterministic tie-break. An implementation that reads `mtime` or `time.time()` inside the acquired plane is wrong even if it passes.
- **Never evict a blob whose URL has `fail_streak > 0`.** That is precisely the copy that cannot be re-acquired. Prefer evicting blobs whose URL is currently healthy.
- **An evicted entry is recorded, not silently dropped** — `refer` must be able to distinguish "never had it" from "had it, evicted", or `as-ingested` degrades to `unverified` with no explanation.
- **Config order must never change committed bytes.** `ttl=` values are stored verbatim and compared *resolved*, so `60m` and `1h` are the same policy but not the same line; `fux add` writes the canonical form.
- **Declared, never detected.** No sniffing, no automatic escalation, no classifier deciding a page is "too thin".
- **Do not touch:** `src/fux/query/rank.py`, `bm25f.py`, `rerank.py`, `confidence.py`, the accelerator under `derive/`, or anything in `archive/`. Ranking is not in this change.
- **Do not delete the rendering implementation.** Move it to `archive/` — changing what `fetch=cdp` *means* is a semantic break, acceptable at alpha, but the old behaviour should survive somewhere.

## 7. Dependencies & prerequisites

- A **running** Chrome with the developer's real profile, started with `--remote-debugging-port=9222`, already signed in to the target tenant. A launched headless Chrome has no profile, therefore no session, therefore fails every time — this is the single most likely source of a confusing early failure.
- A real SharePoint/OneDrive `.xlsx` share URL on a tenant the developer can sign in to.
- A captured SSO login page saved as a test fixture (bytes + content type + final URL).
- No secrets, env vars, or credentials of any kind. If the implementation introduces one, it has taken a wrong turn.

## 8. Edge cases & risks

**Risk 1 — CLOSED 2026-09-01, and the answer was to change the technique.** ~~SharePoint download URLs commonly 302 to a CDN, and a fetch that follows a cross-origin redirect without CORS headers returns an opaque response whose body cannot be read.~~ **This risk no longer applies to the design.** It was a risk *of the in-page fetch*, which §5.1 no longer uses — and the fallback this section itself named (`Fetch.enable`, browser-internal, unaffected by CORS) is now the primary technique, adopted by Arpit on spike step 5's measurement. CORS and CSP are page-level; CDP is not. The Microsoft CORS guidance that framed this risk is no longer load-bearing on anything in this spec. Evidence: §9, step 5.

**Kept below verbatim as the record of the reasoning that was superseded** — it is why the spike existed, and deleting it would leave step 5 looking like a free win rather than a correction.

> **Risk 1 (superseded) — the spike. Lower than first assessed, but still the gate.** SharePoint download URLs commonly 302 to a CDN, and a fetch that follows a cross-origin redirect without CORS headers returns an **opaque response whose body cannot be read**.
>
> Microsoft documents this exact failure, and the shape of the answer, in [Working with CORS](https://learn.microsoft.com/en-us/onedrive/developer/rest-api/concepts/working-with-cors?view=odsp-graph-online):
>
> "To download files from OneDrive in a JavaScript app you cannot use the `/content` API, since this responds with a `302` redirect. A `302` redirect is explicitly prohibited when a CORS *preflight* is required, such as when providing the **Authorization** header." … "Because these URLs are pre-authenticated they can be retrieved **without a CORS preflight request**."
>
> **Two reasons this likely works here:**
> - The prohibition is on *preflighted* requests. This design sends **no `Authorization` header** — cookies only — so the request is a CORS-simple GET, no preflight, and redirects are followed normally.
> - More decisively: navigate to the **file's own site** first, then fetch a **same-origin** download path (`/_layouts/15/download.aspx?SourceUrl=<server-relative-url>`). A same-origin request is not subject to CORS at all.
>
> Neither is a substitute for running it. **Before writing any fetcher code**, confirm empirically (§9, Spike) and record the result.
> → If blocked, the design survives but the technique changes to `Fetch.enable` + `Network.getResponseBody` (browser-internal, unaffected by CORS) or `Page.setDownloadBehavior`. **Stop and report which fallback is needed before continuing.**

*(That is what happened. `Fetch.getResponseBody` on a `Fetch.requestPaused` at `requestStage: "Response"` is the form adopted — `Network.getResponseBody` needs the response to still be in the buffer and races the page.)*

Other cases:
- **Excel Online vs the file** — a `:x:/g/` link opens the web app. The download form of the link is what returns the workbook. Confirm during the spike.
- **Logged out** → structural checks + predicate → `Skipped`, prior record kept, never a deletion (ADR-URL-INGEST decision 4).
- **`validate()` short-circuits the write.** A matching token means `fetch()` is never called, so a locally deleted blob is never restored. `validate()` must return `None` when the blob is missing.
- **`fetch` runs under a thread pool.** Two URLs deriving the same filename is a race; content-addressing plus temp-then-rename removes it. `MAX_PARALLEL` stays `1` for `cdp.py` — the shared `_session` WebSocket makes concurrent frames produce *plausible documents attributed to the wrong URLs*, which passes every determinism check and is caught only by a human reading an answer.
- **`http.py`'s `MAX_BYTES = 8 * 1024 * 1024`** carries the comment *"a page larger than this is a download, not a doc."* That is now false — downloads are the point. Raise it or make it configurable. This is the **only** change `http.py` needs.
- **`cdp.py`'s `HTMLParser`/`urljoin` are NOT dead code — RULED 2026-09-01 (Arpit): keep the code, fix the docstring.** Nothing in `src/` calls `extract_links`, but it is retained deliberately: the in-file comment says crawling is a fetcher's job because the decoder plane may not open a socket, and `tests/ingest/test_cdp_fetcher.py` asserts it stays. **The stale thing is the module docstring**, which still describes a `Runtime.evaluate` → "deterministic HTML→markdown" pipeline that `fetch()` has not done since W-86 P8. Rewrite the docstring in Phase 1; delete nothing.
- **`xlsxdoc.py` clips silently** at `MAX_ROWS_PER_SHEET = 500` / `MAX_COLS = 40`. Real 365 workbooks exceed both. Out of scope for this change, but emit a truncation marker if it is cheap.
- **`[sources.url.config]` goes to every fetcher verbatim**, and `http.py.configure()` raises on unknown keys. Any new `cdp` tunable placed there breaks `http.py`. Keep `cdp.py`'s tunables as module constants, or add per-fetcher tables — do not loosen `http.py`'s strictness, which is what catches typo'd tunables.

## 9. Testing & validation

### Spike — run these in order, before Phase 1

⚠ **SUPERSEDED 2026-09-01 — kept verbatim as the record of what was actually
run.** Steps 1–3 were measured against this table and their results are filed
below; step 5 then retired the technique the table was testing, and Arpit
adopted interception. **Step 4 is no longer a gate.** Do not execute this table
as instructions — read it as history, and read step 5 for what is true now.

Tests 1–3 need **no tenant** and de-risk the plumbing independently of SharePoint. Test 4 is the only one that cannot be substituted.

| # | What it proves | How |
|---|---|---|
| 1 | Binary bytes survive the CDP base64 round-trip | Navigate to `https://httpbin.dev/`, then in-page fetch `https://httpbin.dev/image/png` — **same-origin**, binary. Byte length must match and the bytes must start with `\x89PNG`. |
| 2 | A cross-origin redirect is followed and readable | Navigate to `https://httpbin.dev/`, fetch `https://httpbin.dev/redirect-to?url=https://raw.githubusercontent.com/&status_code=302`. Reading the body proves redirect-following works when the target is CORS-permissive. |
| 3 | What failure *looks like* | From `https://httpbin.dev/`, fetch any origin that sends no `Access-Control-Allow-Origin`. Confirm the exact error/opaque shape, so the fetcher's detection matches reality rather than a guess. |
| 4 | **The real thing** | A signed-in Chrome on the tenant. Navigate to the file's own site, then in-page fetch the same-origin `/_layouts/15/download.aspx?SourceUrl=<server-relative-url>`. Bytes must start with `PK\x03\x04` and the type must be the OOXML spreadsheet MIME. |

**Closest public proxy for test 4:** a **personal OneDrive** share link on a consumer Microsoft account — same download-redirect infrastructure, no corporate tenant needed. Good enough to shape the code; the corporate tenant still confirms it, since Conditional Access can change the redirect chain.

⚠ `httpbin.dev` is a third-party service. If it is down, any same-origin binary asset on a site you can navigate to serves for tests 1 and 3 equally well — the tests are about the plumbing, not the host.

### Spike — RESULTS, steps 1–3 (measured 2026-09-01, Claude Code)

**Steps 1–3 are done. Step 4 (the tenant) is the only one left, and it is still
decisive** — but it is now a *narrow* question rather than an open one.

**Method.** Headless Chrome 9333 with a throwaway `--user-data-dir` (never the
real profile — steps 1–3 need no session), driven over the shipped
`templates/cdp.py.txt` WebSocket client, `Runtime.evaluate` with
`awaitPromise: true`. Reproduce by navigating to a **CSP-free** page and
evaluating:

```js
(async (u, cred) => { try {
  const r = await fetch(u, {credentials: cred});
  const b = await r.arrayBuffer();
  return JSON.stringify({ok: r.ok, status: r.status, type: r.headers.get('content-type'),
    finalUrl: r.url, respType: r.type, bytes: b.byteLength,
    head: [...new Uint8Array(b).slice(0,4)].map(x => x.toString(16).padStart(2,'0')).join(' ')});
} catch (e) { return JSON.stringify({error: String(e)}); } })(URL, MODE)
```

| # | from | target | creds | result |
|---|---|---|---|---|
| 1 | `httpbin.dev` | same-origin `/image/png` | include | ✅ 8090 bytes, `89 50 4e 47` |
| 2 | `example.com` | cross-origin, `ACAO: *` | **omit** | ✅ 87533 bytes, `respType: cors` |
| 3 | `example.com` | cross-origin, `ACAO: *` | **include** | 🔴 `TypeError: Failed to fetch` |
| 4 | `example.com` | **302** → cross-origin `ACAO: *` | **omit** | ✅ 87533 bytes, redirect followed |
| 5 | `example.com` | **302** → cross-origin `ACAO: *` | **include** | 🔴 `TypeError: Failed to fetch` |
| 6 | `example.com` | no `ACAO` at all | omit | 🔴 `TypeError: Failed to fetch` |

**Five findings, and two of them change the plan.**

1. ✅ **The CDP base64 round-trip is byte-exact.** Binary survives; magic bytes
   and lengths match. The transport in §5.1 is sound.
2. ✅ **A cross-origin 302 IS followed and its body IS readable** — rows 2 vs 4
   differ only in the redirect and give identical bytes. **§8's Risk 1 named
   the wrong villain:** the redirect was never the problem.
3. 🔴 **`credentials:'include'` is what kills it, and it is structural, not
   incidental.** Rows 2/3 and 4/5 differ **only** in credentials mode. A
   credentialed CORS request may not be answered with `ACAO: *` — the spec
   forbids the wildcard once cookies are attached, and a CDN that serves every
   origin serves the wildcard. **So: cross-origin + cookies cannot work, and no
   amount of retrying changes that.** The design survives only on the
   **same-origin** path §8 already called "more decisive" — navigate to the
   file's own site, then fetch `/_layouts/15/download.aspx?SourceUrl=…`, which
   CORS never examines.
4. ✅ **Failure is a thrown `TypeError`, never a readable-but-empty opaque
   response.** `fetch` defaults to mode `cors`, which rejects rather than
   returning an opaque body — so `cdp.py` detects this in a `try/catch`, and
   **not** by testing for zero bytes. §8's "opaque response whose body cannot
   be read" describes `mode:'no-cors'`, which this design never uses.
5. 🔴 **The page's own CSP `connect-src` blocks the fetch BEFORE CORS is
   consulted — and it silently invalidated this spike's first two attempts.**
   `httpbin.dev` ships `connect-src 'self' *.httpbin.dev`, so *every*
   cross-origin row failed identically no matter what the target's CORS said,
   which reads exactly like a CORS block. ⚠ **§9's spike table names
   `httpbin.dev` as the host for tests 1–3; for anything cross-origin it is the
   one host that cannot answer the question.** Use a CSP-free page
   (`example.com`) for cross-origin, `httpbin.dev` only for same-origin.

**What step 4 must now answer — one question, not four.** Not *"does the fetch
work"* (it does, same-origin). It is: **does `/_layouts/15/download.aspx` return
the bytes on the site's own origin, or does it 302 to a CDN?** If it returns
them same-origin, Phase 1 proceeds as written. If it redirects off-origin,
finding 3 says the technique **cannot** work with cookies attached and the
fallback (`Fetch.enable` + `Network.getResponseBody`) is required — that is the
gate, and no session picks it silently. Also worth capturing at the same time:
the tenant page's `content-security-policy` header, per finding 5.

### Spike — STEP 5, and it retires the CORS question entirely (2026-09-01)

**Arpit, on reading steps 1–3: *"it is chrome dev tools — can I just scrape the
web, or can't I provide an id to download the file?"* He is right, and §5.1's
technique is the thing that was wrong.**

**CORS and CSP are PAGE-level restrictions.** They applied only because §5.1
chose to run the fetch *inside the page* with `Runtime.evaluate`. CDP itself is
browser-internal, and neither reaches it. Measured, same headless Chrome, no
tenant:

| target | in-page `fetch` (steps 1–3) | `Fetch.enable` + `Fetch.getResponseBody` |
|---|---|---|
| `microsoft.com/robots.txt`, **no `ACAO`** | 🔴 `TypeError: Failed to fetch` | ✅ **8557 bytes**, `text/plain;charset=iso-8859-1` |
| cross-origin binary, no `ACAO` | — | ✅ 17174 bytes, head `00 00 01 00` |
| `Content-Disposition: attachment` | — | ✅ intercepted **before** Chrome makes it a download |

Row 1 is the *same URL* that failed under an in-page fetch in step 3's control.

**A second, independent reason, and it is the one that matters most for
`validate()`.** A cross-origin in-page fetch exposes only the **CORS-safelisted**
response headers unless the server sends `Access-Control-Expose-Headers` — so
**`ETag` would be invisible**, and Phase 1's `validate()` could never have
worked cross-origin. Interception reads every header. This is not a performance
argument; the in-page technique cannot deliver a stated deliverable.

**Proposed amendment to §5.1 — `Page.navigate` + `Fetch.enable` at
`requestStage: "Response"` + `Fetch.getResponseBody`, and no in-page fetch at
all.** What it buys: no CORS, no CSP, no same-origin gymnastics, no need to
construct a `/_layouts/15/download.aspx?SourceUrl=…` URL, real response headers
including `ETag`, and **step 4 stops being a gate** — the technique no longer
depends on SharePoint's redirect topology, so a tenant run confirms rather than
decides.

**What it costs, stated plainly:**
- `CdpSession._call()` **cannot do this today.** It discards every message that
  is not its own id, so an interleaved `Fetch.requestPaused` event is thrown
  away. It needs a small event pump (~20 lines, stdlib, no new dependency).
- **Every paused request must be continued or failed, or the page hangs.**
  Narrow the `urlPattern` to the target rather than `*`, and always resolve
  what you pause.
- A navigation that lands on a login page is intercepted just the same — which
  is correct, and exactly what Phase 2's refusal detection is for. The final
  URL and `responseStatusCode` are both visible on the paused event.

**`Browser.setDownloadBehavior` is the answer to the "provide an id" half of the
question** — `Browser.downloadProgress` hands back a `guid` and Chrome writes
`<downloadPath>/<guid>`. **Not recommended:** it goes via disk, gives no
response headers (so no `ETag`, no real content type), and needs a completion
dance. Row 3 above shows interception gets the attachment case without any of
that. Recorded so it is not rediscovered as a new idea.

✅ **ADOPTED — Arpit, 2026-09-01.** He lifted §5.1's *do not re-litigate* on
reading this table and ruled for interception. §5.1 item 1 now carries the new
technique and the reason it changed. **Step 4 is no longer a gate**: the
technique does not depend on SharePoint's redirect topology, so a tenant run
confirms Phase 1 rather than deciding it.

### The rest

- **Unit:** duration parsing (`1h`/`15m`/`0`/malformed); manifest round-trip; eviction picks by `run_seq` and skips failing URLs; refusal predicate fails closed on raise, on missing file, and on unloadable file; magic-byte checks; `_TYPE_EXT` routing for xlsx/pdf/docx.
- **Fixtures, not live network:** a captured login page and a captured small workbook, both as bytes + content type + final URL. The refusal tests must not need Chrome.
- **Integration:** ingest a real SharePoint xlsx end-to-end (manual, needs a signed-in Chrome); `fux ask` returns cell content; `fux update` with a matching ETag performs no download; `fux update --failed` selects only failing entries.
- **Assertions to keep green:** no socket in `src/`; no third-party import in `src/`; `fux doctor` reports no undeclared `.fux/` entry; `.fux/.gitignore` lists `acquired` by name and never `*`.
- **Commands:** `uv run pytest`, `uv run ruff check src/ tests/`, `uv run fux doctor`.

## 9.5 Documentation impact

- [x] **README** — required. The URL-ingestion paragraph describes `cdp.py` as a browser renderer and lists two networked paths; both change.
- [x] **AI agent files (`CLAUDE.md`, `AGENTS.md`, `src/fux/templates/agents/*`)** — required. New plane, new consumer-owned file, changed `fetch=cdp` semantics. ⚠ **Propose these edits and surface them for Arpit's review — do not silently rewrite steering files.**
- [x] **CHANGELOG** — required. `fetch=cdp` changing meaning is a user-facing semantic break.
- [x] **ADR** — required, and **this is four records, not one.** `docs/adr/TEMPLATE.md` states *one feature, one ADR*:
  - `0020_cdp-fetcher.md` — **rewritten in place**, not superseded. A record states what is true now and carries no history.
  - `0003_fux-directory.md` — **rewritten in place** for the third category.
  - `0050_acquired-plane.md` — new (draft provided, `status: proposed`).
  - One new record each for the refusal contract and URL freshness, at the next free numbers.
  - ⚠ **Every ADR output block must be real, captured output.** The draft deliberately contains none — capture them during the build. An invented transcript is worse than no transcript.
  - `owns:` frontmatter must match the ownership table in `docs/adr/README.md`; update both.
- [x] **Docstrings** — required. `cdp.py`'s module docstring describes a flow it will no longer perform.

## 10. Open questions

- ~~**does the in-page fetch survive SharePoint's download redirect?**~~ **RESOLVED 2026-09-01 — the question is retired, not answered.** There is no in-page fetch any more. Spike step 5 measured that CDP interception is unaffected by the redirect topology the question was about, and Arpit adopted it (§5.1 item 1, §9 step 5). Phase 1 is unblocked.
- **OPEN QUESTION: does `ttl=` accept `d` (days), and is there a `never` value** for a frozen document? Recommendation: support `s/m/h/d`, bare `0` for always, and **no** `never` — an unbounded TTL and a document nobody re-checks are the same thing, and `never` invites indefinite staleness with no signal.
- **OPEN QUESTION: what is the default acquired cap?** Recommendation: `2GB`, configurable, with `fux doctor` reporting actual usage from the first run so the number can be corrected against evidence rather than guessed twice.
- **OPEN QUESTION: does `--offline` join `fux ask`** to force the `as-ingested` path? Recommendation: defer to Phase 4's end, and only if the bimodal ask latency (27ms warm vs a fetch) actually proves annoying in use. ADR-CLI is strict about surface.

---

## 11. The execution prompt

*Lifecycle step 3 — the paste-ready prompt that executes this spec. It lives
here rather than in a directory of its own because the handoff directory was
retired on 2026-08-18, and `work/open/` is one file per item (Arpit,
2026-09-01).*

### Claude Code prompt: browser-session resource fetching + the acquired plane

You are rebuilding fux's browser fetcher to return **resources instead of DOM snapshots**, adding engine-side refusal detection, retaining source bytes in a new `.fux/acquired/` plane, and driving re-fetch from a per-document `ttl=`.

The full spec is §1–§10 of this file. **Read it first.** Its Definition of Done, Non-negotiables and Out-of-scope lists are binding — especially the out-of-scope list, which exists because each item on it is something a helpful agent would otherwise add.

### the spike — RESOLVED, do not re-run it

**The spike is closed.** Steps 1, 2, 3 and 5 are measured and filed in W-98 §9
(`work/open/W-98-acquired-plane.md`). **Arpit ruled on 2026-09-01** that §5.1's
in-page `fetch(url, {credentials:'include'})` is replaced by CDP interception:

    Page.navigate(url)
    Fetch.enable(patterns=[{urlPattern: <target>, requestStage: "Response"}])
    -> Fetch.requestPaused   (final request.url, responseStatusCode,
                              responseHeaders all visible)
    Fetch.getResponseBody    (base64 body)
    Fetch.continueRequest / Fetch.failRequest   <- ALWAYS, or the page hangs

**Why the old technique is gone, in one line each:**

- CORS and CSP are **page-level**; CDP is browser-internal and neither reaches
  it. Measured: the same no-`ACAO` cross-origin URL returned `TypeError`
  in-page and **8557 bytes** under interception.
- A cross-origin in-page fetch exposes only **CORS-safelisted** response
  headers, so **`ETag` is invisible** — Phase 1's `validate()` could never have
  worked. Interception reads every header.
- `Content-Disposition: attachment` is intercepted **before** Chrome turns it
  into a download, so no `Browser.setDownloadBehavior` dance is needed.
  (`Browser.setDownloadBehavior` was considered and rejected: via disk, no
  response headers, no `ETag`. Recorded so it is not rediscovered.)

**Step 4 (the signed-in tenant run) is now a CONFIRMATION, not a gate.** The
technique no longer depends on SharePoint's redirect topology, so Phase 1 is
written first and the tenant run verifies it end to end.

**What this costs, and it is the one thing to get right:** `CdpSession._call()`
discards every message that is not its own id, so an interleaved
`Fetch.requestPaused` event is thrown away today. It needs a small event pump.
Narrow `urlPattern` to the target rather than `*`, and **always resolve what
you pause.**

### Context to load first

- `src/fux/ingest/urlsrc.py` — the fetcher contract, `fetch_all`, `_unpack`, `_decode_fetched`, `_TYPE_EXT`
- `src/fux/templates/cdp.py.txt` — the file being rebuilt
- `src/fux/store/fuxdir.py` — `COMMITTED` / `DERIVED` / `DECLARED`, `derived_dir()`
- `src/fux/ingest/sourcelist.py` — `ListSpec`, `Attribute`, `URLS`
- `src/fux/maintain/urlstate.py` — `run_seq`, `fail_streak`, and the counters-not-clocks rule
- `src/fux/refer/fetchcache.py`, `refer/freshness.py`, `refer/source.py`
- `docs/adr/TEMPLATE.md`, `0003_fux-directory.md`, `0019_fetcher.md`, `0020_cdp-fetcher.md`
- Respect `CLAUDE.md` and `AGENTS.md`.

### Task — four phases, in order, each stopping for my confirmation

**Phase 1 — `cdp.py` returns the resource.** `Fetch.enable` at `requestStage: "Response"` on a pattern narrowed to the target, `Page.navigate`, then `Fetch.requestPaused` → `Fetch.getResponseBody` → base64 decode → `Fetch.continueRequest` → return `(bytes, real_content_type)` read from the intercepted `responseHeaders`. **Every paused request is continued or failed, always.** `CdpSession._call` gains an event pump so an interleaved event is no longer discarded. `LAUNCH_CHROME = False`. Add `validate(url)` reading `ETag` off the same intercepted `responseHeaders`, returning `None` when unavailable **or when the local blob is missing**. Rewrite ADR-0020 in place. This phase needs **no engine change** and on its own delivers Excel ingestion.

🔴 **BLOCKED: see §2.** **Phase 2 — refusal detection, declarative.** Always-on structural checks in the engine (landed-off-origin, declared-type vs magic bytes) — a rules file **adds** refusals and can never subtract one. Plus `.fux/refusals.toml`, a committed vendor-neutral rules table: a starter file ships at `src/fux/templates/refusals.toml.txt`, and [ADR-REFUSAL](../../docs/adr/0051_refusals.md) is the specification — read that. Conditions are `final_url_host`, `final_url_contains`, `status`, `content_type`, `requested_suffix`, `requested_suffix_not`, `body_contains`, `body_starts_with`, `max_bytes`; rules ORed in file order with first-match-wins, conditions within a rule ANDed. `name` and `reason` are required; the reason goes verbatim into `Skipped(reason=...)` and the rule name is reported by `fux doctor`. **A missing file is legitimate** (structural checks are the floor, say nothing); **a malformed file refuses to run**, loudly, as a malformed `fux.toml` does. Add `refusals.toml` to `COMMITTED_FILES` in `fuxdir.py` and write a `refusals.schema.json` following the `config.schema.json` pattern. **Do not write a `refusals.py`** — a code predicate is explicitly deferred.

**Phase 3 — the acquired plane.** `.fux/acquired/` with `objects/<sha[:2]>/<sha256>.<ext>` + `manifest.json`, declared in `fuxdir.py` as a third category, `CACHEDIR.TAG`'d, listed by name in `.fux/.gitignore`. `keep` line attribute, default `false`. Persist in `fetch_all` **after** the refusal check and **before** decode. Manifest written once at the end of the run. Configurable cap, eviction by `run_seq`.

**Phase 4 — freshness.** `ttl=` accepting `30s`/`15m`/`1h`/`7d` and bare `0`. At ask time: TTL live → `cached`; expired → `validate()` first, fetch only on a changed/absent token. New `as-ingested` verdict when a fetch fails but the blob matches. `fux update --failed`.

### Required workflow

1. **Explore** before writing. Do not assume structure.
2. **Plan** each phase — the steps and the files you will change — and **pause for my confirmation** before implementing it. Four phases means four checkpoints.
3. **Implement incrementally.** Keep the suite green between phases.
4. **Update docs to match** — README, CHANGELOG, docstrings, and the ADRs. For `CLAUDE.md` / `AGENTS.md` / `src/fux/templates/agents/*`: **propose the edits and surface them for my review — do not silently rewrite steering files.** Do not report done while docs contradict code.
5. **Verify:** `uv run pytest`, `uv run ruff check src/ tests/`, `uv run fux doctor`. Fix what you break.

### Constraints (hard)

- **Zero third-party dependencies in `src/`.** Stdlib only. No `requests`, `websockets`, `playwright`, `httpx`. The hand-rolled RFC 6455 WebSocket stays.
- **`src/fux/` opens no socket.** Network lives only in `.fux/fetchers/`. The refusal matcher is pure over bytes — no network, no I/O — and gets the same test assertion `sources.py` and `refer/source.py` have.
- **No wall clock in the acquired plane.** "Oldest" means oldest by `run_seq` with a deterministic tie-break. `time.time()` or `mtime` inside the plane is wrong even if tests pass. Wall clock stays in `runtime/fetch-cache/`.
- **Never evict a blob whose URL has `fail_streak > 0`** — that is exactly the copy that cannot be re-acquired. Record evictions in the manifest; never silently drop the entry.
- **No auth of any kind.** No OAuth, no Graph, no device code, no token cache, no credential handling, no new env var or secret. Auth is the browser's session, borrowed. Not signed in → fail loudly.
- **No `dl.py`**, no third fetcher, no opening of the `fetch` attribute enum.
- **No `blob` field on the index record.** The record shape does not change. (`query/output.schema.json` does, in Phase 4 — that is the output schema.)
- **No offline re-decode from blobs.** Keep the layout capable of it; do not build it.
- **No automatic escalation between fetchers**, no content sniffing, no "too thin" classifier.
- **Do not modify:** `query/rank.py`, `bm25f.py`, `rerank.py`, `confidence.py`, `derive/`, or `archive/`.
- **Do not delete the rendering implementation** — move it to `archive/`.

### Acceptance criteria (self-check before finishing each phase)

- [ ] A SharePoint `.xlsx` share link ingests and `fux ask` returns cell content from it
- [ ] A captured login page is rejected as a `Skipped` with a readable reason, never indexed
- [ ] `fux doctor` reports no undeclared `.fux/` entry; `.fux/.gitignore` lists `acquired` by name, never `*`
- [ ] `fux update` with a matching ETag performs no body download
- [ ] `as-ingested` never renders as `current`
- [ ] No socket and no third-party import anywhere in `src/`
- [ ] Tests added and passing; docs updated or explicitly noted as not needed

### Tests

Duration parsing including malformed input; manifest round-trip; eviction ordering by `run_seq` and the failing-URL exclusion; refusal predicate failing closed on raise / missing file / unloadable file; magic-byte checks; `_TYPE_EXT` routing for xlsx, pdf, docx. Use **captured fixtures** (a real login page, a small real workbook) so refusal tests need no Chrome. `uv run pytest`.

### ADR discipline

`docs/adr/TEMPLATE.md` says **one feature, one ADR** — this is four records, not one:

- `0020_cdp-fetcher.md` — **rewritten in place.** A record states what is true now and carries no history; there are no "Amended" sections.
- `0003_fux-directory.md` — rewritten in place for the third category.
- `0050_acquired-plane.md` — a `status: proposed` draft exists; complete it and move to `accepted`.
- One new record each for the refusal contract and URL freshness.

⚠ **Every `Output —` block must be real, captured output.** The draft contains none on purpose. Capture them during the build; never invent a transcript. Update `owns:` frontmatter and the ownership table in `docs/adr/README.md` together.

### Guardrails

- **Ask before:** deleting any file, changing a public contract, altering `fux.toml` schema defaults, or any irreversible action.
- If a requirement is ambiguous, or conflicts with what you find in the code, **STOP and ask rather than guessing.** Specifically: if `cdp.py`'s `HTMLParser`/`urljoin` imports turn out to still be live rather than dead code from W-86 P8, stop — the docstring and the code disagree and I want to know which is wrong.
