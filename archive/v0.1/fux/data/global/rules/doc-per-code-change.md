---
id: doc-per-code-change
domain: process
type: convention
status: active
created: 2026-06-01
updated: 2026-06-01
aliases: [docs-in-same-pr, doc-update, knowledge-current]
keywords: [documentation, drift, rule, update, session]
related: [files-max-100-lines]
---
**Convention:** Every code change ships with the knowledge update it implies in
the same session — update the governing `rule`/`formula`/`adr`, or author one if
the logic was previously undocumented.

**Why:** Documentation rots the moment code and prose diverge. Coupling the two
in one unit of work is the only durable way to keep the *why* alive; deferred
"I'll document it later" is how the business-rules gap (plan §1) opened in the
first place.

**How to apply:** Fux enforces this at edit time: the PostToolUse hook flags when
you touch a file that a rule governs without updating that rule. Treat the flag
as part of the change, not a follow-up. New logic on a hot path earns a new rule.
