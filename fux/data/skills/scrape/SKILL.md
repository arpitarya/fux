---
name: fux-scrape
description: "scrape a website → draft governed Fux rules — the agent fetches (HTTP, escalating to CDP for client-rendered pages), classifies the source's trust, and drafts status: draft rules with provenance; the engine validates and governs"
trigger: /fux scrape
---

# /fux scrape — web page → draft rules (agent fetches, fux governs)

Read a web page and draft the rules it implies as `status: draft` Fux entries
**with provenance**. The split that keeps Fux `$0` and trustworthy:

- **The agent** (you, this session) does the fetching and the judgement — HTTP,
  CDP rendering, deciding what's a rule. Those are *your* tokens.
- **The engine** only validates the result (`fux check`), and re-verifies a
  drafted source on demand (`fux scrape <id> --recheck`). It never fetches on the
  maintenance path and never calls a model.

A scraped rule is **never** auto-active and **never** auto-constitutional. It is a
*draft* until a human reviews it and (if it binds) runs `/fux debate` → `fux ratify`.

## Inputs

```
/fux scrape <url> [--domain <domain>] [--cdp-port <n>] [--cdp-host <host>]
```

## Procedure

### Step 1 — Ensure the engine is available

Follow `skills/fux/SKILL.md` Step 1–2 to confirm `$FUX` resolves and the project
has a `.fux/` footprint (`$FUX init` if not).

### Step 2 — Fetch the page (HTTP first, escalate to CDP)

Try a plain HTTP fetch — it's `$0` and enough for static/server-rendered pages:

```bash
$FUX fetch-rules "<url>" --raw > /tmp/fux-scrape.txt
```

**Escalate to CDP only if** the extracted text is a *client-rendered shell* —
near-empty body, a lone spinner, or literal "enable JavaScript / loading…". Then
render the page through a Chrome DevTools Protocol endpoint and read the text the
browser produced. Resolve the endpoint **once**, by this precedence (the engine
computes it for you — no hard-coded port):

```bash
# flags > FUX_CDP_PORT/FUX_CDP_HOST env > cdp_port/cdp_host in .fux/config.toml > 127.0.0.1:9299
CDP=$($FUX_PY -c "from fux import cdp_utils, config, paths; \
import pathlib; \
print(cdp_utils.endpoint(config.load(paths.Footprint(pathlib.Path('.')).config)))")
echo "CDP endpoint: $CDP"   # e.g. http://127.0.0.1:9299
```

Pass `--cdp-port` / `--cdp-host` to override for one run. Use your CDP/browser
tooling (e.g. `chrome --remote-debugging-port=<port>`, then navigate + read
`document.body.innerText`) against `$CDP` — that fetch is your tokens, not the
engine's.

### Step 3 — Classify the source → type + trust

The source's nature sets the rule `type` **and** how much you trust a scrape:

| Source | `type` | Trust / handling |
|---|---|---|
| Third-party docs / API reference | `convention` | A convention to follow; cite the page. |
| Your own / your team's docs | `rule` or `glossary` | First-party — a real rule or a defined term. |
| Market / pricing / data feed | `rule` | Add a **data caveat** — values change; date-stamp it. |
| **Regulatory / tax / compliance / legal** | **`regulatory`** | **DRAFT-VERIFY.** A scrape is *never* the authority. Add a note: *verify against the primary source*. Human ratification is **mandatory** before it binds. |

When in doubt, prefer the *lower-trust* classification (a `regulatory` page is
never "just a convention").

### Step 4 — Draft each rule with provenance (`status: draft`)

For each constraint/term/formula the page implies:

```bash
$FUX new <type> <id> --domain <domain>
```

Then open the stub and write the frontmatter + body. **Force `status: draft`** and
add the three provenance fields:

```markdown
---
id: <kebab-id>
type: <convention|rule|glossary|regulatory>
status: draft            # web-sourced — never active until a human reviews it
domain: <domain>
source: "<exact url>"
fetched: "<ISO date, e.g. 2026-06-23>"
source_hash: "<see below>"
---

**Rule/Convention/Term/Formula:** <precise statement from the page>

**Why:** <obligation or rationale — for regulatory, cite the section/clause AND
add: "scraped draft — verify against the primary source before relying on it">

**Edge cases:** <scope, exceptions, caveats from the page>
```

Compute `source_hash` the same way `--recheck` will, so a later recheck compares
like with like (canonical = whitespace-collapsed, lower-cased, `sha256[:16]`):

```bash
$FUX_PY -c "from fux import scrape; import sys; print(scrape.source_hash(sys.stdin.read()))" \
  < /tmp/fux-scrape.txt
```

### Step 5 — Validate and govern

```bash
$FUX build && $FUX check && $FUX lint
```

Fix every schema and `no-why` finding. Then **stop** — do not activate or ratify.
Tell the user what to do next:

- Review each draft against the page.
- For anything that should **bind**: `/fux debate "<rule>"` → `fux ratify <id>`.
- Regulatory drafts: verify against the primary/official source first — a scrape
  is a lead, not law.

### Step 6 — Report

```
✔ Drafted N rules from <url>  [domain: <domain>]  — all status: draft

  convention  api-rate-limit-100rpm    100 requests/min per API key
  regulatory  vat-standard-rate-20pct  DRAFT-VERIFY · 20% standard VAT (cite §X)

Next: review, then /fux debate → fux ratify anything that binds.
Re-check a source later:  fux scrape <id> --recheck   (opt-in; needs the [scrape] extra)
```

## Re-verifying a source later (opt-in, `$0`-fenced)

`fux scrape <id> --recheck` re-fetches the rule's `source`, recomputes
`source_hash`, and raises a `source-drift` finding if the page changed since
`fetched`. It is **behind the `[scrape]` extra and never on the default
`fux check` path** — drift in an external page must never silently fail a build.

## Quality bar

Every drafted entry must:
- Be `status: draft` (web-sourced rules never start active).
- Carry `source`, `fetched`, and `source_hash`.
- Have a real `**Why:**` — regulatory drafts cite the clause **and** say "verify
  against the primary source".
- Be self-contained: understandable without re-opening the page.

## Cost

Fetching, rendering, and turning text into rule prose use the current agent/LLM
(your session). The engine side — `$FUX fetch-rules --raw`, `fux check`,
`fux scrape --recheck` — is `$0`, deterministic, no model.
