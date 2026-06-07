---
name: fux-fetch-rules
description: "parse a URL, PDF, or text file and automatically derive + create durable Fux rule entries from the content — the agent reads the document and extracts every actionable rule"
trigger: /fux fetch-rules
---

# /fux fetch-rules — derive rules from a document

Read a source document (URL, PDF, or text file) and automatically extract every
actionable rule it contains as durable `.fux/rules/` entries. The agent does the
derivation — you don't need to read the document yourself.

## Inputs

```
/fux fetch-rules <source> [--domain <domain>]
```

- `<source>` — an `http(s)://` URL, a local `.pdf`, `.txt`, or `.md` path
- `--domain` — optional scope label (e.g. `tax`, `api`, `security`). If omitted,
  infer it from the document content.

## Procedure

### Step 1 — Ensure the engine is available

Follow `skills/fux/SKILL.md` Step 1–2 to confirm `$FUX` resolves and the
project has a `.fux/` footprint (`$FUX init` if not).

### Step 2 — Read the source

**URL or text file** — use the CLI extractor:

```bash
$FUX fetch-rules "<source>" --raw
```

**Local PDF** — use the agent's file reader directly when it handles PDFs
natively. For a remote PDF URL, the CLI extractor handles it if `pypdf` is
installed (`pip install 'fux-engine[pdf]'`); otherwise download first:

```bash
curl -sL "<url>" -o /tmp/fux-source.pdf
# then Read /tmp/fux-source.pdf
```

Read the **entire** document. Do not summarise prematurely.

### Step 3 — Derive rules

Parse the content for every **actionable constraint, formula, or decision** the
project must respect. Apply these extraction patterns:

| Signal in the text | Fux type to create |
|---|---|
| Numeric formula, calculation, rate | `formula` |
| "must / shall / must not / is required to" | `rule` |
| Naming or style convention | `convention` |
| Law, regulation, external standard | `regulatory` |
| Architecture or design decision already made | `adr` |
| Step-by-step operational procedure | `runbook` |
| Boundary condition, exception, known gotcha | `edge-case` |
| Defined term with a precise meaning | `glossary` |

Rules to skip:
- Pure narrative / background with no obligation (history, motivation without a constraint)
- Redundant restatements of the same rule already extracted
- Vague preferences ("try to", "consider") unless the source clearly treats them as requirements

For each derived rule, determine:
- **`id`** — kebab-case, descriptive, unique (e.g. `stcg-equity-rate`, not `rule-1`)
- **`type`** — from the table above
- **`domain`** — from the `--domain` arg or inferred
- **Rule statement** — the precise constraint, copied faithfully (not paraphrased away)
- **Why** — the obligation source: cite the section/clause for regulatory; the design
  rationale for conventions; the formula derivation for formulas
- **Edge cases / Applies to** — scope, exceptions, caveats from the document

### Step 4 — Create the entries

For each derived rule, scaffold and fill in one operation:

```bash
$FUX new <type> <id> --domain <domain>
```

Then open the file and write:

```markdown
---
...frontmatter...
source: "<origin URL or filename>"
---

**Rule/Formula/Convention/…:** <precise statement from the document>

**Why:** <obligation or rationale — cite section/clause if regulatory>

**Edge cases:** <exceptions, scope limits, caveats>
```

Set `source:` in the frontmatter to the origin URL or filename so provenance is
always traceable. Set `code_refs:` to files the rule governs if already known;
otherwise leave `[]`.

Work through all derived rules before moving to Step 5 — do not stop after the
first few.

### Step 5 — Build and validate

```bash
$FUX build
$FUX lint
```

Fix every `no-why` lint warning before finishing. A rule without a `**Why:**` is
half a rule — the *why* is the whole point.

### Step 6 — Report

Print a compact summary of what was created:

```
✔ Derived N rules from <source>  [domain: <domain>]

  formula     stcg-equity-rate          Short-term capital gains on equity: 20%
  regulatory  sebi-lot-size-quarterly   NSE F&O lot sizes set by SEBI, revised quarterly
  convention  date-format-iso8601       All dates stored as ISO-8601 (YYYY-MM-DD)
  …

Run `fux recall "<topic>"` to retrieve any of these in future sessions.
Rules with empty code_refs: set them once you know which files they govern.
```

## Quality bar

Every created entry must:
- Have a non-empty `**Why:**` section (not just "from document")
- Have a `source:` frontmatter field with the exact origin
- Use a descriptive kebab-case `id` (not `rule-1`, `item-3`, `extracted-4`)
- Be self-contained: a reader with no access to the source document must understand
  the rule from the entry alone

## Cost

The derivation step uses the current agent/LLM. The fetch/extract step
(`$FUX fetch-rules --raw`) is `$0` — pure stdlib, no API cost.
