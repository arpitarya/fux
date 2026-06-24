---
name: fux-ingest
description: "ingest a URL, PDF, Excel, TXT, or image → draft governed Fux rules — the agent extracts (HTTP/CDP for URLs, the pdf/xlsx skills for files, native vision for images), classifies the source's trust, and drafts status: draft rules with provenance; the engine validates and governs"
trigger: /fux ingest
---

# /fux ingest — file or web source → draft rules (agent extracts, fux governs)

Read a URL, PDF, Excel/CSV, TXT/Markdown, or image and draft the rules it implies as
`status: draft` Fux entries **with provenance**. The split that keeps Fux `$0` and
trustworthy:

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
/fux ingest <url|file> [--domain <domain>] [--cdp-port <n>] [--cdp-host <host>]
```

`<url|file>` may be an `http(s)://` URL or a local path: `.pdf`, `.xlsx`/`.csv`,
`.txt`/`.md`, or an image (`.png`/`.jpg`/…).

## Procedure

### Step 1 — Ensure the engine is available

Follow `skills/fux/SKILL.md` Step 1–2 to confirm `$FUX` resolves and the project
has a `.fux/` footprint (`$FUX init` if not).

### Step 2 — Extract the source (branches on source type)

Pick the branch for the input and record `source_type` for Step 4:

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

**TXT / Markdown (`source_type: txt`)** — read the file directly.

**Image (`source_type: image`)** — use your native vision/OCR to read the text
or figures in the image. See the OCR caution below before trusting it.

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
source_type: <url|pdf|xlsx|txt|image>
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
Tell the user what to do next:

- Review each draft against the source.
- For anything that should **bind**: `/fux debate "<rule>"` → `fux ratify <id>`.
- Regulatory drafts: verify against the primary/official source first.
- Image/OCR-derived money or regulatory drafts: verify against the original
  image/document before trusting the figure.

### Step 6 — Report

```
✔ Drafted N rules from <source>  [domain: <domain>]  — all status: draft

  convention  api-rate-limit-100rpm    100 requests/min per API key
  regulatory  vat-standard-rate-20pct  DRAFT-VERIFY · 20% standard VAT (cite §X)

Next: review, then /fux debate → fux ratify anything that binds.
Re-check a source later:  fux ingest <id> --recheck   (opt-in; needs the [scrape] extra)
```

## Re-verifying a source later (opt-in, `$0`-fenced)

`fux ingest <id> --recheck` re-reads the rule's `source` (URL or local file),
recomputes `source_hash`, and raises a `source-drift` finding if it changed since
`fetched`. It is **behind the `[scrape]` extra and never on the default
`fux check` path** — drift in an external source must never silently fail a build.

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
