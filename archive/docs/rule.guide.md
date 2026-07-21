# Fux Rules — How to Write Them

How to write a `.fux/rules/<id>.md` entry — the atomic unit of the Fux substrate
(plan §6). A rule exists to **capture one piece of durable knowledge once** — a
business rule, a formula and its *why*, a decision, a gotcha — so neither a human
nor an agent ever has to re-derive it from the code. If you can answer "how does X
work and *why*" from a rule instead of grepping, the rule earns its keep.

## When to write one

Author **by demand, not exhaustively** (plan §12 break-even). Write a rule the
first time a question would otherwise re-scan the codebase: hot paths (valuation,
P&L, broker quirks, auth) cross that line almost immediately; rarely-touched
corners may never need one. Reach for `fux new <type> <id>`.

## Pick the type (plan §6)

| type | for |
|---|---|
| `rule` | a business rule / policy |
| `formula` | a calculation + worked example (carry `examples:`) |
| `invariant` | a must-always-be-true assertion (carry a `check:`) |
| `adr` | an architecture/decision record — the *why* |
| `edge-case` | a known gotcha |
| `convention` | a code/process convention |
| `regulatory` | an external/legal rule (tax, market hours, SEBI) |
| `runbook` | an operational procedure |
| `glossary` | a domain term |
| `narrative` | long-form prose (exempt from atomic sizing) |
| `memory` | a cross-session observation (`subtype` + `scope`) |
| `spec` / `task` | planning artifacts (see [spec.guide.md](spec.guide.md)) |

## Required structure (the *why* is mandatory)

1. **Frontmatter** — `id` (kebab), `domain`, `type`, `status`, `created`,
   `updated`. Add `code_refs:` pointing at the exact lines the rule governs
   (`path#Lstart-Lend`), `related:` ids, and `aliases:`/`keywords:` for recall.
2. **`**Rule:`/`**Formula:`/`**Decision:`** — the statement, one line.
3. **`**Why:`** — **mandatory.** A rule without a *why* is half a rule; the *why*
   is the entire reason Fux exists (plan §1). State the rationale and the
   alternative you rejected.
4. **`**Edge cases:`** — guards, units, empty-input behaviour.

## Link it into the substrate

- `code_refs:` — what the rule governs. `fux refs <file>` and the graph's
  `governs` edges depend on these; `fux check` flags them when dead or stale.
- `related:` / `edges:` — `depends-on`, `supersedes`, `contradicts`,
  `implements`. These power conflict detection and the graph (plan §6, §10.6).
- `check:` (invariant/formula) — a Python expression `fux verify` evaluates
  against verification data. Make a drifting rule **fail**, not just warn.

## Lifecycle & provenance (plan §10.5)

`status: draft` while shaping → `active` once trusted → `deprecated` for history
(kept, but excluded from context injection). Keep `updated` current — `fix` mode
bumps it for you when the governed code changes.

## Checklist

- [ ] Right `type` chosen.
- [ ] `**Why:`** present and specific (not "because it's correct").
- [ ] `code_refs` point at real lines; `fux check` is clean.
- [ ] `related`/`edges` link neighbours; recall finds it (`fux recall`).
- [ ] Invariant/formula carry `check:`/`examples:` where assertable.
- [ ] File ≤100 lines (narrative/memory exempt); `fux build` run.
