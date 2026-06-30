---
agent: ask
description: Use Fux project knowledge to answer, review, or orient in this repository.
---

Use the Fux knowledge engine in this repository.

1. Run `fux context` to read the compact INDEX when `.fux/` exists.
2. For a question, run `fux recall "${input:question}"` and open only the relevant `.fux/` entries.
3. For a specific rule, use `fux why <id>`.
4. For a file, use `fux refs <path>` before explaining or changing governed code.
5. Treat `.fux/out/` as generated output from `fux build`.

Keep durable project knowledge in `.fux/` entries, not ad hoc notes.
