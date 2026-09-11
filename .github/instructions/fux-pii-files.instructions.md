---
applyTo: ".fux/pii.toml"
---

# Editing Fux PII rules

`.fux/pii.toml` decides which values are redacted from the committed index.

- **Only when a human asked.** Never delete or empty the file to get past an
  error - fux refuses to run without it on purpose.
- **Never write a real identifier** into a rule, test or message - use obvious
  fakes such as `jane.doe@example.com`.
- **Probe a rule against the corpus before enabling it**; an over-broad rule
  silently removes real search vocabulary.
- **A checksum (`validate`) is a 1-in-10 filter**, not proof.
- A matching value is redacted; the document is still indexed.
- A rule change re-extracts everything on the next `fux ingest`; URL documents
  change only when re-fetched.

Full procedure: the `fux-pii` skill.
