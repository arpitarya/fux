---
id: no-secrets-in-vcs
domain: security
type: convention
status: active
created: 2026-06-01
updated: 2026-06-01
aliases: [secrets, api-keys, env-files, credentials]
keywords: [dotenv, token, password, vault, leak]
---
**Convention:** Never commit secrets — `.env` files, API keys, tokens, private
keys — to version control. They belong in a secrets manager or untracked local
env, never in the tree, and never in a synced/shared `global` rules repo either.

**Why:** A secret in git history is a secret leaked: history is permanent, repos
get cloned and synced across machines, and a single push to a public remote
exposes it irreversibly. The blast radius is far larger than the convenience.

**How to apply:** Keep `.env*` in `.gitignore`; load secrets from the
environment or a vault at runtime. If a key was committed, rotate it — deleting
the file does not unleak it. This rule is itself a `fux check` lint target.
