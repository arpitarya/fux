# Claude Code prompt: browser-session resource fetching + the acquired plane

You are rebuilding fux's browser fetcher to return **resources instead of DOM snapshots**, adding engine-side refusal detection, retaining source bytes in a new `.fux/acquired/` plane, and driving re-fetch from a per-document `ttl=`.

The full spec is in `work/handoff/HANDOFF_acquired-plane.md`. **Read it first.** Its Definition of Done, Non-negotiables and Out-of-scope lists are binding — especially the out-of-scope list, which exists because each item on it is something a helpful agent would otherwise add.

## Before anything else — the spike

**Do not write fetcher code until this is resolved.** The plan rests on an assumption: that an in-page `fetch(url, {credentials:'include'})` can read the body of a SharePoint download URL. SharePoint commonly 302s cross-origin, and a cross-origin redirect without CORS headers yields an **opaque response whose body cannot be read**.

Microsoft documents this failure and its shape in [Working with CORS](https://learn.microsoft.com/en-us/onedrive/developer/rest-api/concepts/working-with-cors?view=odsp-graph-online) — the prohibition applies to *preflighted* requests (those carrying an `Authorization` header). This design sends cookies only, no `Authorization`, so it is a CORS-simple GET with no preflight. And navigating to the file's own site first makes the download path **same-origin**, which is not subject to CORS at all. Likely fine — confirm anyway.

Run this snippet, unchanged, at each step. Report the four values it logs.

```js
const probe = (u) => fetch(u, {credentials:'include'})
  .then(r => r.arrayBuffer().then(b => ({
    ok: r.ok, status: r.status, type: r.headers.get('content-type'),
    finalUrl: r.url, bytes: b.byteLength,
    head: [...new Uint8Array(b).slice(0,4)].map(x=>x.toString(16).padStart(2,'0')).join(' ')
  })))
  .then(console.log).catch(e => console.error('FAILED', e));
```

1. **Plumbing, no tenant.** On `https://httpbin.dev/`: `probe('https://httpbin.dev/image/png')` → expect `head` starting `89 50 4e 47`.
2. **Cross-origin redirect, no tenant.** On `https://httpbin.dev/`: `probe('https://httpbin.dev/redirect-to?url=https://raw.githubusercontent.com/&status_code=302')`.
3. **Failure shape, no tenant.** Probe an origin sending no `Access-Control-Allow-Origin`; record the exact error so detection matches reality.
4. **The real thing.** Ask me to run it in my signed-in Chrome: navigate to the file's own site, then `probe('/_layouts/15/download.aspx?SourceUrl=<server-relative-url>')` → expect `head` of `50 4b 03 04` and the OOXML spreadsheet MIME.

- Steps 1–3 pass and step 4 returns real bytes → proceed as specified.
- Step 4 opaque/blocked/zero bytes → **stop and report.** Technique changes to `Fetch.enable` + `Network.getResponseBody` or `Page.setDownloadBehavior`. Do not pick a fallback silently.

## Context to load first

- `src/fux/ingest/urlsrc.py` — the fetcher contract, `fetch_all`, `_unpack`, `_decode_fetched`, `_TYPE_EXT`
- `src/fux/templates/cdp.py.txt` — the file being rebuilt
- `src/fux/store/fuxdir.py` — `COMMITTED` / `DERIVED` / `DECLARED`, `derived_dir()`
- `src/fux/ingest/sourcelist.py` — `ListSpec`, `Attribute`, `URLS`
- `src/fux/maintain/urlstate.py` — `run_seq`, `fail_streak`, and the counters-not-clocks rule
- `src/fux/refer/fetchcache.py`, `refer/freshness.py`, `refer/source.py`
- `docs/adr/TEMPLATE.md`, `0003_fux-directory.md`, `0019_fetcher.md`, `0020_cdp-fetcher.md`
- Respect `CLAUDE.md` and `AGENTS.md`.

## Task — four phases, in order, each stopping for my confirmation

**Phase 1 — `cdp.py` returns the resource.** Navigate once per *origin* to establish the session, then `Runtime.evaluate` with `awaitPromise: true` doing the in-page fetch → `arrayBuffer` → base64 → decode → return `(bytes, real_content_type)`. `LAUNCH_CHROME = False`. Add `validate(url)` via in-page HEAD → `ETag`, returning `None` when unavailable **or when the local blob is missing**. Rewrite ADR-0020 in place. This phase needs **no engine change** and on its own delivers Excel ingestion.

**Phase 2 — refusal detection, declarative and pure over bytes.** RESPECIFIED 2026-09-01 after you stopped it — you were right, and the resolution is **hold**: every transport condition is removed and **the fetcher contract does not change.** `fetch(url) -> (bytes, content_type)` stands; ADR-FETCHER decision 13 stands unamended; its veto does not fire.

One always-on engine check: declared content type vs magic bytes. Nothing else, and **no `status`, no `final_url`, no redirect awareness anywhere in `src/`.** Plus `.fux/refusals.toml`, a committed vendor-neutral rules table — a starter file is at `work/handoff/refusals.toml` and **its header comment is the specification, read it first.** Six conditions, all pure over the bytes: `content_type`, `requested_suffix`, `requested_suffix_not`, `body_contains`, `body_starts_with`, `max_bytes`. Rules ORed in file order with first-match-wins, conditions within a rule ANDed. `name` and `reason` required; the reason goes verbatim into `Skipped(reason=...)` and the rule name is reported by `fux doctor`. **A missing file is legitimate** (the magic-byte check is the floor, say nothing); **a malformed file refuses to run**, loudly, as a malformed `fux.toml` does. Add `refusals.toml` to `COMMITTED_FILES` in `fuxdir.py` and write a `refusals.schema.json` following the `config.schema.json` pattern. **Do not write a `refusals.py`** — a code predicate is explicitly deferred.

The new refusal ADR's veto condition is: *a real captured refusal that the six byte-pure conditions cannot express.* If you hit one while building, stop and report it — that is the evidence that would reopen the contract question, and it is the only thing that should.

**Phase 3 — the acquired plane.** `.fux/acquired/` with `objects/<sha[:2]>/<sha256>.<ext>` + `manifest.json`, declared in `fuxdir.py` as a third category, `CACHEDIR.TAG`'d, listed by name in `.fux/.gitignore`. `keep` line attribute, default `false`. Persist in `fetch_all` **after** the refusal check and **before** decode. Manifest written once at the end of the run. Configurable cap, eviction by `run_seq`.

**Phase 4 — freshness.** `ttl=` accepting `30s`/`15m`/`1h`/`7d` and bare `0`. At ask time: TTL live → `cached`; expired → `validate()` first, fetch only on a changed/absent token. New `as-ingested` verdict when a fetch fails but the blob matches. `fux update --failed`.

## Required workflow

1. **Explore** before writing. Do not assume structure.
2. **Plan** each phase — the steps and the files you will change — and **pause for my confirmation** before implementing it. Four phases means four checkpoints.
3. **Implement incrementally.** Keep the suite green between phases.
4. **Update docs to match** — README, CHANGELOG, docstrings, and the ADRs. For `CLAUDE.md` / `AGENTS.md` / `src/fux/templates/agents/*`: **propose the edits and surface them for my review — do not silently rewrite steering files.** Do not report done while docs contradict code.
5. **Verify:** `uv run pytest`, `uv run ruff check src/ tests/`, `uv run fux doctor`. Fix what you break.

## Constraints (hard)

- **Zero third-party dependencies in `src/`.** Stdlib only. No `requests`, `websockets`, `playwright`, `httpx`. The hand-rolled RFC 6455 WebSocket stays.
- **`src/fux/` opens no socket.** Network lives only in `.fux/fetchers/`. The refusal matcher is pure over bytes — no network, no I/O — and gets the same test assertion `sources.py` and `refer/source.py` have.
- **No vendor knowledge in `src/`.** The engine's check is a format fact only (magic bytes). No hostname, product name, or provider string from any vendor appears anywhere under `src/` — all of that lives in the consumer's committed `refusals.toml`, including the starter rules.
- **No HTTP vocabulary in `src/`.** ADR-FETCHER decision 13: fux never reads a status code, a header, or an error string. `urlsrc.py` must not mention one, and the fetcher contract stays `(bytes, content_type)` — a bare `str` still accepted. If a phase seems to need `status` or a redirect target, **that is the signal to stop and ask**, not to widen the tuple.
- **No wall clock in the acquired plane.** "Oldest" means oldest by `run_seq` with a deterministic tie-break. `time.time()` or `mtime` inside the plane is wrong even if tests pass. Wall clock stays in `runtime/fetch-cache/`.
- **Never evict a blob whose URL has `fail_streak > 0`** — that is exactly the copy that cannot be re-acquired. Record evictions in the manifest; never silently drop the entry.
- **No auth of any kind.** No OAuth, no Graph, no device code, no token cache, no credential handling, no new env var or secret. Auth is the browser's session, borrowed. Not signed in → fail loudly.
- **No `dl.py`**, no third fetcher, no opening of the `fetch` attribute enum.
- **No `blob` field on the index record.** The record shape does not change. (`query/output.schema.json` does, in Phase 4 — that is the output schema.)
- **No offline re-decode from blobs.** Keep the layout capable of it; do not build it.
- **No automatic escalation between fetchers**, no content sniffing, no "too thin" classifier.
- **Do not modify:** `query/rank.py`, `bm25f.py`, `rerank.py`, `confidence.py`, `derive/`, or `archive/`.
- **Do not delete the rendering implementation** — move it to `archive/`.

## Acceptance criteria (self-check before finishing each phase)

- [ ] A SharePoint `.xlsx` share link ingests and `fux ask` returns cell content from it
- [ ] A captured login page is rejected as a `Skipped` with a readable reason, never indexed
- [ ] `fux doctor` reports no undeclared `.fux/` entry; `.fux/.gitignore` lists `acquired` by name, never `*`
- [ ] `fux update` with a matching ETag performs no body download
- [ ] `as-ingested` never renders as `current`
- [ ] No socket and no third-party import anywhere in `src/`
- [ ] Tests added and passing; docs updated or explicitly noted as not needed

## Tests

Duration parsing including malformed input; manifest round-trip; eviction ordering by `run_seq` and the failing-URL exclusion; refusal predicate failing closed on raise / missing file / unloadable file; magic-byte checks; `_TYPE_EXT` routing for xlsx, pdf, docx. Use **captured fixtures** (a real login page, a small real workbook) so refusal tests need no Chrome. `uv run pytest`.

## ADR discipline

`docs/adr/TEMPLATE.md` says **one feature, one ADR** — this is four records, not one:

- `0020_cdp-fetcher.md` — **rewritten in place.** A record states what is true now and carries no history; there are no "Amended" sections.
- `0003_fux-directory.md` — rewritten in place for the third category.
- `0050_acquired-plane.md` — a `status: proposed` draft exists; complete it and move to `accepted`.
- One new record each for the refusal contract and URL freshness.

⚠ **Every `Output —` block must be real, captured output.** The draft contains none on purpose. Capture them during the build; never invent a transcript. Update `owns:` frontmatter and the ownership table in `docs/adr/README.md` together.

## Guardrails

- **Ask before:** deleting any file, changing a public contract, altering `fux.toml` schema defaults, or any irreversible action.
- If a requirement is ambiguous, or conflicts with what you find in the code, **STOP and ask rather than guessing.** Specifically: if `cdp.py`'s `HTMLParser`/`urljoin` imports turn out to still be live rather than dead code from W-86 P8, stop — the docstring and the code disagree and I want to know which is wrong.
