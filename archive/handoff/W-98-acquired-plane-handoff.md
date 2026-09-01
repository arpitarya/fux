# Handoff: browser-session resource fetching + the acquired plane

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

**Phase 2 — refusal detection (declarative, pure over bytes)**

> ⚠ **This phase was respecified on 2026-09-01 after Claude Code stopped it pre-code.** The original version put `status`, `final_url_host`, `final_url_contains` and an always-on landed-off-origin check inside the engine, which trips **ADR-FETCHER decision 13**'s veto: *"urlsrc.py mentions a status code, a header name, or matches text inside an exception."* Every transport condition is removed. The fetcher contract is **unchanged** — `fetch(url) -> (bytes, content_type)` stands.

- [ ] **One** engine check, always on: declared content type vs magic bytes (`PK\x03\x04` for OOXML, `%PDF-` for PDF). A rules file adds refusals; it can never subtract one.
- [ ] `.fux/refusals.toml` — a committed, vendor-neutral rules table. Starter file at `work/handoff/refusals.toml`; joins `COMMITTED_FILES` in `fuxdir.py` beside `.fuxignore` / `tune.toml` / `output.toml`
- [ ] `refusals.schema.json` beside the loader, following the `config.schema.json` / `state.schema.json` pattern
- [ ] **Six conditions, all pure over the bytes:** `content_type` (prefix, parameters stripped), `requested_suffix`, `requested_suffix_not`, `body_contains` (first 64 KB, texty responses only), `body_starts_with` (hex), `max_bytes`. Rules ORed in file order, first match wins; conditions within a rule ANDed
- [ ] **No `status`, no `final_url_*`, no redirect awareness anywhere.** A MIME type is format vocabulary and is fux's business; a 302 is transport vocabulary and is the fetcher's
- [ ] `name` and `reason` required on every rule; the reason is recorded verbatim as the skip reason, and the rule name is reported by `fux doctor`
- [ ] **Missing file is legitimate** (the magic-byte check is the floor, no warning). **Malformed file refuses to run**, loudly, as a malformed `fux.toml` does — a silently-unparsed rules file is indistinguishable from a repo with no rules
- [ ] Test fixtures: captured SSO login page rejected with the expected rule name; a real workbook not rejected. No browser, no network
- [ ] New ADR for the refusal contract, carrying the veto condition in §10
- [ ] **No `.fux/refusals.py`.** A code predicate is deferred; add it only if a real signature turns out not to be expressible as a match

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

- Repo: `/Users/arpitarya/my_programs/fux`, `fux-engine` 2.0.0-alpha.0
- **Read first, in this order:**
  - `src/fux/ingest/urlsrc.py` — the fetcher contract, `fetch_all`, `_unpack`, `_decode_fetched`, `_TYPE_EXT`
  - `src/fux/templates/cdp.py.txt` — the file being rebuilt (the shipped template; `.fux/fetchers/cdp.py` is the consumer copy)
  - `src/fux/store/fuxdir.py` — `COMMITTED` / `DERIVED` / `DECLARED`, `derived_dir()`, `CACHEDIR_TAG`
  - `src/fux/ingest/sourcelist.py` — `ListSpec`, `Attribute`, `URLS`
  - `src/fux/maintain/urlstate.py` — `UrlHealth`, `fail_streak`, `run_seq`, the counters-not-clocks rule
  - `src/fux/refer/fetchcache.py` and `refer/freshness.py` — where the wall clock is allowed to live
  - `src/fux/refer/source.py` — verify-time resolution, the "a document fetched two ways is two documents" rule
  - `docs/adr/TEMPLATE.md`, `docs/adr/0003_fux-directory.md`, `docs/adr/0019_fetcher.md`, `docs/adr/0020_cdp-fetcher.md`
- **Patterns to reuse:** `derived_dir()` for creating a tagged directory; `urlstate.py`'s advisory-state shape for the manifest; `_decode_fetched`'s `(value, why)` return for the refusal predicate; `load_fetcher()`'s import-by-path for loading `refusals.py`.

## 5. Technical approach (decided — do not re-litigate)

1. **`cdp.py` returns the resource, never a rendering.** Navigate to establish the browser session, then `Runtime.evaluate` with `awaitPromise: true` running an in-page `fetch(url, {credentials:'include'})` → `arrayBuffer` → base64 → decode → return with the response's real content type. A rendered DOM carries nonces, timestamps and session ids, so its sha changes on every fetch — nondeterministic input to an engine that asserts byte-identical results.
2. **No `dl.py`.** Once `cdp` fetches resources, `cdp` and the proposed `dl` are the same file. The roster is two fetchers on one axis: *whose session*.
3. **Auth is the browser's.** No credentials are stored, read, or handled anywhere. Not signed in → fail loudly.
4. **Refusal detection is engine-side, not per-fetcher.** W-86 P8 removed conversion from the fetchers because it lived there as two hand-maintained copies nothing checked; per-fetcher refusal detection repeats that mistake, and a login page through `http.py` is exactly as poisonous as one through a browser.
5. **Refusal detection is declarative data, not code.** A refusal signature is a pattern match — a host you were bounced to, a content type that cannot be right, a marker in the markup — and that is data. Data is diffable, reviewable, and testable against a captured page with no browser and no network; a Python predicate could do the same job and could also open a socket, raise from anywhere, and fail in a way indistinguishable from *"this page is fine"*. Adding a system tomorrow is a table entry, not a code review. This also matches the repo's own idiom: `sources/urls`, `.fuxignore`, `tune.toml` and `output.toml` are all committed, diffable, line-oriented policy.
   ⚠ **This supersedes the earlier `refusals.py` predicate design, and with it the fail-closed rule for a broken predicate.** Going declarative makes *missing* and *malformed* distinguishable, which a Python import could not: a missing file is a legitimate configuration, a malformed one is a hard failure. There is no third state to fail closed on.
6. **Fux ships zero vendor knowledge.** The engine's always-on check is a format fact (magic bytes). Every organisation-specific rule lives in the consumer's committed `refusals.toml`, including the ones the starter file ships with — those are examples the consumer owns and may delete, exactly as `cdp.py` ships with Chrome specifics.
7. **Refusal conditions are pure over the bytes, and the fetcher contract does not widen.** `fetch(url) -> (bytes, content_type)` stands. **ADR-FETCHER decision 13** — *fux never reads a status code, a header, or an error string* — binds here exactly as it binds `is_rate_limited`, and its veto names `urlsrc.py` specifically. `content_type` qualifies because a MIME type is **format** vocabulary; `status` and `final_url` do not, because a 302 is **transport** vocabulary and belongs to whatever protocol the fetcher happens to speak.
   **The detection cost is near zero, which is why this is a hold and not a sacrifice.** An identity provider that bounces you still has to return a page, and that page is HTML where a document was requested — caught by rule 1 without knowing the provider exists. Provider-specific detection survives as `body_contains` on form-field names (`name="loginfmt"`, `name="SAMLRequest"`), which are an API between the page and its own backend and so outlive the redesigns that rewrite every visible string.
   **Reopen only on evidence:** a real captured refusal that the six byte-pure conditions cannot express. That is the veto condition on the refusal ADR. Widening the contract to add capability that is currently redundant, four days after decision 13 was ratified, is how a law stops meaning anything.
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

**Risk 1 — the spike. Lower than first assessed, but still the gate.** SharePoint download URLs commonly 302 to a CDN, and a fetch that follows a cross-origin redirect without CORS headers returns an **opaque response whose body cannot be read**.

Microsoft documents this exact failure, and the shape of the answer, in [Working with CORS](https://learn.microsoft.com/en-us/onedrive/developer/rest-api/concepts/working-with-cors?view=odsp-graph-online):

> "To download files from OneDrive in a JavaScript app you cannot use the `/content` API, since this responds with a `302` redirect. A `302` redirect is explicitly prohibited when a CORS *preflight* is required, such as when providing the **Authorization** header." … "Because these URLs are pre-authenticated they can be retrieved **without a CORS preflight request**."

**Two reasons this likely works here:**
- The prohibition is on *preflighted* requests. This design sends **no `Authorization` header** — cookies only — so the request is a CORS-simple GET, no preflight, and redirects are followed normally.
- More decisively: navigate to the **file's own site** first, then fetch a **same-origin** download path (`/_layouts/15/download.aspx?SourceUrl=<server-relative-url>`). A same-origin request is not subject to CORS at all.

Neither is a substitute for running it. **Before writing any fetcher code**, confirm empirically (§9, Spike) and record the result.
→ If blocked, the design survives but the technique changes to `Fetch.enable` + `Network.getResponseBody` (browser-internal, unaffected by CORS) or `Page.setDownloadBehavior`. **Stop and report which fallback is needed before continuing.**

Other cases:
- **Excel Online vs the file** — a `:x:/g/` link opens the web app. The download form of the link is what returns the workbook. Confirm during the spike.
- **Logged out** → structural checks + predicate → `Skipped`, prior record kept, never a deletion (ADR-URL-INGEST decision 4).
- **`validate()` short-circuits the write.** A matching token means `fetch()` is never called, so a locally deleted blob is never restored. `validate()` must return `None` when the blob is missing.
- **`fetch` runs under a thread pool.** Two URLs deriving the same filename is a race; content-addressing plus temp-then-rename removes it. `MAX_PARALLEL` stays `1` for `cdp.py` — the shared `_session` WebSocket makes concurrent frames produce *plausible documents attributed to the wrong URLs*, which passes every determinism check and is caught only by a human reading an answer.
- **`http.py`'s `MAX_BYTES = 8 * 1024 * 1024`** carries the comment *"a page larger than this is a download, not a doc."* That is now false — downloads are the point. Raise it or make it configurable. This is the **only** change `http.py` needs.
- **`cdp.py` still imports `HTMLParser` and `urljoin`**, and its docstring still describes "deterministic HTML→markdown", which `fetch()` no longer does. Confirm this is dead code from W-86 P8 and delete it — or, if something still calls it, stop and report, because the docstring and the code disagree.
- **`xlsxdoc.py` clips silently** at `MAX_ROWS_PER_SHEET = 500` / `MAX_COLS = 40`. Real 365 workbooks exceed both. Out of scope for this change, but emit a truncation marker if it is cheap.
- **`[sources.url.config]` goes to every fetcher verbatim**, and `http.py.configure()` raises on unknown keys. Any new `cdp` tunable placed there breaks `http.py`. Keep `cdp.py`'s tunables as module constants, or add per-fetcher tables — do not loosen `http.py`'s strictness, which is what catches typo'd tunables.

## 9. Testing & validation

### Spike — run these in order, before Phase 1

Tests 1–3 need **no tenant** and de-risk the plumbing independently of SharePoint. Test 4 is the only one that cannot be substituted.

| # | What it proves | How |
|---|---|---|
| 1 | Binary bytes survive the CDP base64 round-trip | Navigate to `https://httpbin.dev/`, then in-page fetch `https://httpbin.dev/image/png` — **same-origin**, binary. Byte length must match and the bytes must start with `\x89PNG`. |
| 2 | A cross-origin redirect is followed and readable | Navigate to `https://httpbin.dev/`, fetch `https://httpbin.dev/redirect-to?url=https://raw.githubusercontent.com/&status_code=302`. Reading the body proves redirect-following works when the target is CORS-permissive. |
| 3 | What failure *looks like* | From `https://httpbin.dev/`, fetch any origin that sends no `Access-Control-Allow-Origin`. Confirm the exact error/opaque shape, so the fetcher's detection matches reality rather than a guess. |
| 4 | **The real thing** | A signed-in Chrome on the tenant. Navigate to the file's own site, then in-page fetch the same-origin `/_layouts/15/download.aspx?SourceUrl=<server-relative-url>`. Bytes must start with `PK\x03\x04` and the type must be the OOXML spreadsheet MIME. |

**Closest public proxy for test 4:** a **personal OneDrive** share link on a consumer Microsoft account — same download-redirect infrastructure, no corporate tenant needed. Good enough to shape the code; the corporate tenant still confirms it, since Conditional Access can change the redirect chain.

⚠ `httpbin.dev` is a third-party service. If it is down, any same-origin binary asset on a site you can navigate to serves for tests 1 and 3 equally well — the tests are about the plumbing, not the host.

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

- **OPEN QUESTION: does the in-page fetch survive SharePoint's download redirect?** Blocking for Phase 1. Resolve by spike before writing code (§8, Risk 1).
- **OPEN QUESTION: does `ttl=` accept `d` (days), and is there a `never` value** for a frozen document? Recommendation: support `s/m/h/d`, bare `0` for always, and **no** `never` — an unbounded TTL and a document nobody re-checks are the same thing, and `never` invites indefinite staleness with no signal.
- **OPEN QUESTION: what is the default acquired cap?** Recommendation: `2GB`, configurable, with `fux doctor` reporting actual usage from the first run so the number can be corrected against evidence rather than guessed twice.
- **OPEN QUESTION: does `--offline` join `fux ask`** to force the `as-ingested` path? Recommendation: defer to Phase 4's end, and only if the bimodal ask latency (27ms warm vs a fetch) actually proves annoying in use. ADR-CLI is strict about surface.
