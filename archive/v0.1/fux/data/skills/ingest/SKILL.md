---
name: fux-ingest
description: "batch-ingest N URLs/files/globs (PDF, Excel, Word, TXT, image, JSON/YAML, Swagger/OpenAPI) — and optionally follow a page to the documents it links — → a draft review queue of governed Fux rules; the agent extracts (HTTP/CDP, its pdf/xlsx/docx/vision skills) and drafts status: draft rules with provenance, the engine validates, queues, and governs"
trigger: /fux ingest
---

# /fux ingest — batch file/web sources → draft review queue (agent extracts, fux governs)

Read **one or many** sources — URLs, PDF, Excel/CSV, Word, TXT/Markdown, images,
JSON/YAML, or Swagger/OpenAPI specs — and draft the rules they imply as
`status: draft` Fux entries **with provenance**, collected into a **draft review
queue** (`.fux/ingest/queue.md`). With `--follow-links`, when a URL is an HTML
*page*, also discover and ingest the documents it links — **bounded and confirmed**
(§ "Following links"). The split that keeps Fux `$0` and trustworthy:

- **The agent** (you, this session) does the extraction and the judgement — HTTP,
  CDP rendering, PDF/Excel reading, OCR/vision, deciding what's a rule. Those are
  *your* tokens.
- **The engine** only validates the result (`fux check`), and re-verifies a
  drafted source on demand (`fux ingest <id> --recheck`). It never fetches or reads
  a file on the maintenance path and never calls a model.

An ingested rule is **never** auto-active and **never** auto-constitutional. It is a
*draft* until a human reviews it and (if it binds) runs `/fux debate` → `fux ratify`.

`/fux scrape <url>` still works as a **deprecated alias** for this skill (URL-only,
one release) — prefer `/fux ingest` going forward.

## Inputs

```
/fux ingest <sources…> [--follow-links] [--cross-origin] [--max <N>] [--yes]
            [--full] [--domain <domain>] [--cdp-port <n>] [--cdp-host <host>]
/fux ingest --queue            # show the draft review queue, then stop
```

`<sources…>` is **one or more** `http(s)://` URLs and/or local paths/globs:
`.pdf`, `.xlsx`/`.csv`, `.docx`, `.txt`/`.md`, images (`.png`/`.jpg`/…),
`.json`, `.yaml`/`.yml`, or a Swagger/OpenAPI spec (file, raw-spec URL, or
Swagger-UI page).

## Procedure

### Step 1 — Ensure the engine is available

Follow `skills/fux/SKILL.md` Step 1–2 to confirm `$FUX` resolves and the project
has a `.fux/` footprint (`$FUX init` if not).

### Step 1.5 — Expand + dedup the source list ($0, engine)

Let the engine expand globs deterministically and dedup the source list — never
hand-expand `*.pdf` yourself:

```bash
$FUX ingest <sources…>      # prints the expanded, deduped source list + type per item
```

If `--follow-links` is set and a source is an HTML **page**, run § "Following
links" *first* to turn that page into a confirmed set of document URLs, then add
those to the list. A **direct file URL** (ends in a doc extension) is ingested as
that file — it skips discovery.

Then **loop Steps 2–5 over each source** (this is PR2's single-source pipeline,
run N times). The loop is **partial-failure-tolerant**: if a source 404s, is
unreadable, or won't parse, record it as `failed` with the reason (Step 5b) and
**continue** — one bad source never aborts the batch.

### Step 2 — Extract the source (branches on source type)

Pick the branch for the input and record `source_type` for Step 4. **Before
drafting, reduce the extracted text** — see § "Reduce before draft".

**URL (`source_type: url`)** — HTTP first, escalate to CDP only if the page is a
client-rendered shell (near-empty body, a lone spinner, "enable JavaScript…"):

```bash
$FUX fetch-rules "<url>" --raw > /tmp/fux-ingest.txt
```

Escalating: resolve the CDP endpoint (no hard-coded port — the engine computes it):

```bash
# flags > FUX_CDP_PORT/FUX_CDP_HOST env > cdp_port/cdp_host in .fux/config.toml > 127.0.0.1:9299
CDP=$($FUX_PY -c "from fux import cdp_utils, config, paths; \
import pathlib; \
print(cdp_utils.endpoint(config.load(paths.Footprint(pathlib.Path('.')).config)))")
echo "CDP endpoint: $CDP"   # e.g. http://127.0.0.1:9299
```

Pass `--cdp-port` / `--cdp-host` to override for one run. Use your CDP/browser
tooling against `$CDP` — that fetch is your tokens, not the engine's.

**PDF (`source_type: pdf`)** — use your `pdf` skill to extract text and tables.
If the PDF is a scan (no extractable text layer), OCR it — but see the **OCR
caution** in Step 3.5 before trusting any number you read this way.

**Excel / CSV (`source_type: xlsx`)** — use your `xlsx` skill to read the
structured cells; note the sheet/range a figure came from.

**Word (`source_type: docx`)** — use your `docx` skill to extract the headings,
section text, and tables. The engine never opens a `.docx`.

**TXT / Markdown (`source_type: txt`)** — read the file directly.

**Image (`source_type: image`)** — use your native vision/OCR to read the text
or figures in the image. See the OCR caution below before trusting it.

**JSON / YAML (`source_type: json` / `yaml`)** — read the file/response and treat
the **structure as the contract**: keys, required/enum/constraint fields, and
defined shapes are rules; example *values* are not. Draft from the schema, not the
sample data.

**Swagger / OpenAPI (`source_type: openapi`)** — the standout structured source.
The spec may be a `.json`/`.yaml` file, a raw-spec URL, or a **Swagger-UI page**
(a client-rendered shell — CDP-render it as in the URL branch to find the linked
`openapi.json`/`swagger.json`, then fetch *that*). Parse the spec and draft **one
rule per contract**:

- one per **endpoint contract** (method + path + its required request/response shape),
- one per **required-param set** (which params are mandatory, their types/enums/limits),
- one per **auth scheme** (which security scheme guards which operations),
- one per **deprecation** (`deprecated: true` operations/params).

Because the spec is machine-precise, `source_hash` + `fux ingest <id> --recheck`
later **flag contract drift** — an endpoint dropped, a param removed, a scheme
changed (Step "Re-verifying" below). Spec sources are the prime beneficiaries.

### Step 3 — Classify the source → type + trust

The source's nature sets the rule `type` **and** how much you trust the extraction:

| Source | `type` | Trust / handling |
|---|---|---|
| Third-party docs / API reference | `convention` | A convention to follow; cite the source. |
| Your own / your team's docs | `rule` or `glossary` | First-party — a real rule or a defined term. |
| Market / pricing / data feed | `rule` | Add a **data caveat** — values change; date-stamp it. |
| **Regulatory / tax / compliance / legal** | **`regulatory`** | **DRAFT-VERIFY.** Never the authority. Add a note: *verify against the primary source*. Human ratification is **mandatory** before it binds. |

When in doubt, prefer the *lower-trust* classification (a `regulatory` source is
never "just a convention").

#### Step 3.5 — Image/OCR trust caution (handoff §4)

A figure read from an **image** or a **scanned PDF** (OCR'd, no native text layer)
is inherently lower-confidence than extracted text — OCR misreads digits, currency
symbols, and decimal points. If the figure is a **money amount** or feeds a
**regulatory** rule:

- Add `**Why:** ... — read via OCR from an image/scan; verify-source before relying
  on it` to the body.
- Never auto-trust it. The draft must be reviewed by a human against the original
  image/document before it can bind, in addition to the normal regulatory
  DRAFT-VERIFY rule above.

### Step 4 — Draft each rule with provenance (`status: draft`)

For each constraint/term/formula the source implies:

```bash
$FUX new <type> <id> --domain <domain>
```

Then open the stub and write the frontmatter + body. **Force `status: draft`** and
add the provenance fields, including `source_type`:

```markdown
---
id: <kebab-id>
type: <convention|rule|glossary|regulatory>
status: draft            # ingested — never active until a human reviews it
domain: <domain>
source: "<exact url or file path>"
source_type: <url|pdf|xlsx|docx|txt|image|json|yaml|openapi>
fetched: "<ISO date, e.g. 2026-06-23>"
source_hash: "<see below>"
---

**Rule/Convention/Term/Formula:** <precise statement from the source>

**Why:** <obligation or rationale — for regulatory, cite the section/clause AND
add: "ingested draft — verify against the primary source before relying on it";
for an image/OCR-derived money or regulatory figure, also add: "read via OCR —
verify-source before relying on it">

**Edge cases:** <scope, exceptions, caveats from the source>
```

Compute `source_hash` the same way `--recheck` will, so a later recheck compares
like with like (canonical = whitespace-collapsed, lower-cased, `sha256[:16]`):

```bash
$FUX_PY -c "from fux import ingest; import sys; print(ingest.source_hash(sys.stdin.read()))" \
  < /tmp/fux-ingest.txt
```

For a file source, hash the extracted text the same way — or, for non-text files
(xlsx/image) where `--recheck` will just re-read raw bytes, hash that file's bytes
the same way `fetchrules.fetch_text` would (read it, decode with `errors="replace"`)
so a later recheck is apples-to-apples.

### Step 5 — Validate and govern

```bash
$FUX build && $FUX check && $FUX lint
```

Fix every schema and `no-why` finding. Then **stop** — do not activate or ratify.

### Step 5b — Record the source in the draft review queue

Whether the source drafted rules or failed, append one row to the queue so the
batch has a single triage surface. Append per source in your loop:

```bash
$FUX_PY -c "
from fux import ingestqueue as q, paths; import pathlib
root = paths.find_project_root() or pathlib.Path('.')
q.upsert(root, [q.Item(source='<source>', source_type='<type>',
                       status='draft', trust='<verify-source|>',
                       draft_id='<rule-id>', source_hash='<hash>')])"
```

A **failed** source records `status='failed'` + a `reason` and **no draft_id**.
`upsert` dedups by `source_hash` (re-ingesting an identical doc updates its row).
Show the whole queue any time with `fux ingest --queue`.

### Step 5c — Tell the user what to do next

- Review each draft against the source (triage the queue by trust flag first).
- For anything that should **bind**: `/fux debate "<rule>"` → `fux ratify <id>`.
- Regulatory drafts: verify against the primary/official source first.
- Image/OCR-derived money or regulatory drafts: verify against the original
  image/document before trusting the figure.

### Step 6 — Report

Report the batch as a whole — the queue is the output:

```
✔ Ingested M sources → K drafts (J failed)  [domain: <domain>]  — all status: draft
  tokens (reduce-before-draft): <before> → <after>

  draft   openapi  api/openapi.json    12 endpoint/param/auth/deprecation rules
  draft   pdf      ./circular-2026.pdf  3 rules   (⚑ regulatory · verify-source)
  failed  url      https://x/404        404 Not Found

Queue: fux ingest --queue
Next:  triage by trust flag, then /fux debate → fux ratify anything that binds.
Re-check a source later:  fux ingest <id> --recheck   (opt-in; needs the [scrape] extra)
```

## Following links (`--follow-links`, opt-in, BOUNDED)

Off by default. With `--follow-links`, when a URL resolves to an HTML **page**
(not a direct file), discover the documents it links and ingest them — under
**hard bounds the engine enforces for you** so this can never become a crawler:

1. **You** fetch the page HTML (HTTP, or CDP for a client-rendered shell) — your
   tokens, as always.
2. The **engine** filters the page's links to a bounded, allow-listed set:

```bash
$FUX_PY -c "
from fux import ingestfollow as f
import sys
html = open('/tmp/page.html').read()
for u in f.discover(html, '<page-url>', cross_origin=<False|True>, max_n=<N>):
    print(u)"
```

`discover` applies the bounds: **depth-1 only** (it inspects *this* page's links,
never recurses), **same-origin** by default (`--cross-origin` widens), an
**extension allow-list** (`.pdf .xlsx .csv .docx .txt .md .json .yaml .yml` +
images + OpenAPI/Swagger specs — **never** executables/scripts/archives), and a
**cap** (`--max N`, default 20) — over the cap it raises `FollowError`
(refuse-with-message; **no silent mass-download**).

3. **List-and-confirm by default:** show the user the discovered links and let
   them pick which to ingest. `--yes` takes all (up to the cap) without asking.
4. Ingest the confirmed set as ordinary sources (Steps 2–5b). A **direct file
   URL** (`…/circular.pdf`, or a raw-spec URL) is `is_direct_file()` → ingest it
   directly, skipping discovery.

## Reduce before draft (`$0`, deterministic — cut the token cost)

Reading whole PDFs/Excels/Words is the dominant token cost of ingestion. Before
you draft, feed your **extracted text** through the engine reducer and draft from
the *reduced* extract, not the whole document. It never parses a binary — it
operates on the text you already extracted:

```bash
$FUX_PY -c "
from fux import ingestreduce as r
import sys
text = sys.stdin.read()
out, stats = r.reduce(text, source_type='<type>', full=<False|True>)
sys.stderr.write(f'tokens {stats[\"before_tokens\"]} -> {stats[\"after_tokens\"]}\n')
print(out)" < /tmp/fux-ingest.txt > /tmp/fux-reduced.txt
```

- **Structure-aware per type:** PDF/Word → headings + tables + rule-bearing
  passages; **Excel → schema + sample rows + formulas, NEVER the full data grid**;
  JSON/YAML/Swagger → the contract/schema, not example values.
- **Rule-signal pre-filter** (reusing fux's recall tokenizer): keeps chunks with
  `must`/`shall`/`required`/`deprecated`/`limit`/`rate`/`threshold`/… plus their
  section — reduces toward candidates, never a hard cut.
- **Boilerplate/page-number strip + whitespace normalize + dedup.**
- **Incremental re-ingest:** on a changed source, diff new vs the cached prior
  extract and draft only the **changed** sections:
  `ingestreduce.changed_sections(old_text, new_text)`.
- **`--full` bypasses reduction** — use for high-stakes regulatory where
  precision beats cost. The reducer reports tokens before→after and files the
  saving via `cage_receipt` (fail-open).

Report the per-source `before → after` token saving in Step 6.

## Re-verifying a source later (opt-in, `$0`-fenced)

`fux ingest <id> --recheck` re-reads the rule's `source` (URL or local file),
recomputes `source_hash`, and raises a `source-drift` finding if it changed since
`fetched`. It is **behind the `[scrape]` extra and never on the default
`fux check` path** — drift in an external source must never silently fail a build.

For **Swagger/OpenAPI** sources this is the contract-drift signal: when the spec
changes (an endpoint dropped, a param removed, an auth scheme changed), `--recheck`
flags the drafted rule so you re-read the spec and re-draft the affected contracts.

## Connector sources (`--connector`, agent pulls structured data; fux governs)

A connector source — **Jira / Confluence / GitHub** — is distinct from file/URL: the
agent pulls **structured, server-side-filtered** data via the existing **MCP connectors
/ APIs**; **fux never builds a client or calls an API.** Then the *same* reduce → draft
→ review-queue → govern pipeline runs. These are **low-trust** (a ticket/wiki/PR is not
a spec): they land in the queue weighted `trust: candidate`, bounded and confirmed like
`--follow-links`, never auto-active. `source_type` is `jira|confluence|github`.

**Bounds (mandatory — the engine enforces them via `fux ingest --connector …`):**
- An explicit **server-side query/filter is required** — `fux ingest --connector jira
  --query "<JQL>"` etc. The engine **refuses an unbounded "everything" pull** (empty /
  `*` / `all`). Tokens you never fetch cost nothing.
- Cap the item count (`--max`); `--since <cursor>` does a **delta** (only what changed).
- **List-and-confirm before drafting**, same discipline as `--follow-links`.

**Efficiency stack — most impactful first ("pull less" beats "reduce more"):**
1. **Server-side filter, never the firehose.** Jira → JQL (acceptance-criteria/decision
   tickets, a board, a label — never "all sprints"); GitHub → API query (PRs/ADRs/docs,
   not CI logs or bot comments); Confluence → space/page query.
2. **Delta / `--since` cursor** — ingest once, then only what changed.
3. **Structure-slice each item** — Jira: title + description + **acceptance criteria**
   (drop comment threads/status history); GitHub: PR/commit title + body + linked issue +
   ADRs (drop CI logs/bot noise; code rules stay `fux mine`'s job); Confluence: page body
   (drop comments/version history).
4. **Reduce-before-draft** + **dedup by `source_hash`** on what remains.

**What's worth ingesting (recommended order — GitHub first, highest signal):** GitHub →
PR/commit *rationale* + ADRs + docs (the *why*); Jira → acceptance criteria + decisions;
Confluence → runbooks/decisions/glossary pages.

**Fallback ladder — when the MCP connector doesn't work (most efficient first; always
prefer structured, server-filtered JSON over scraped DOM):**
1. **MCP connector** — default. Structured, server-filtered, auth managed by the connector.
2. **Direct REST API + token (PAT)** — same JSON, same server-side filtering. *The* real
   fallback (the connector was only a wrapper around this).
3. **Native export / `git clone`** — bulk offline snapshot. **GitHub needs neither
   connector nor probe** — `git clone` gives code + ADRs + docs for `$0`, plus the API for
   PRs. Jira/Confluence: CSV / space export for a one-shot.
4. **CDP via the authenticated browser session, calling the JSON REST endpoints** — only
   when the API is reachable *only* through the logged-in browser (SSO-only, no PAT). The
   SPA calls `/rest/api/...` with the session cookie; `fetch()` those in page context →
   **structured JSON, not scraped DOM.**
5. **CDP DOM scraping** — absolute last resort, only when even the in-browser API is
   blocked. Fragile, token-heavy; accept the cost knowingly.

Probes (CDP) are rungs 4–5, **not** the default — reach for the REST API and export/clone
first. At every rung the *agent* fetches; fux governs; the engine stays `$0` and
client-free.

**Queue write (low-trust):** record each connector item exactly like Step 5b, with
`source_type='jira|confluence|github'` and `trust='candidate'`:
```bash
fux build >/dev/null 2>&1 || true
python -c "
from fux import ingestqueue as q, paths; import pathlib
root = paths.find_project_root() or pathlib.Path('.')
q.upsert(root, [q.Item(source='<jira-key|pr-url|page-id>', source_type='github',
                       status='draft', trust='candidate',
                       draft_id='<rule-id>', source_hash='<hash>')])"
```

## Quality bar

Every drafted entry must:
- Be `status: draft` (ingested rules never start active).
- Carry `source`, `source_type`, `fetched`, and `source_hash`.
- Have a real `**Why:**` — regulatory drafts cite the clause **and** say "verify
  against the primary source"; image/OCR-derived money or regulatory figures also
  say "verify-source".
- Be self-contained: understandable without re-opening the source.

## Cost

Fetching/reading, rendering, OCR, and turning content into rule prose use the
current agent/LLM (your session). The engine side — `$FUX fetch-rules --raw`,
`fux check`, `fux ingest --recheck` — is `$0`, deterministic, no model.
