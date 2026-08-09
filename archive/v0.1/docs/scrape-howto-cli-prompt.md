# Fux — Web-Rules, Self-Docs & CLI Help: One-Shot Prompt

Paste into Claude Code in the `fux` repo. Full spec: `docs/scrape-howto-cli-handoff.md`.

```
Implement four related features for Fux per docs/scrape-howto-cli-handoff.md, in one pass. Read that
handoff plus fux/cli.py, fux/clicmds.py, fux/cliquery.py, fux/config.py, fux/recall.py, fux/check.py,
fux/data/schema.json, and fux/data/skills/ first. Plan briefly, show me the plan, then implement IN THIS
ORDER (D first — it's the data source for C).

HARD CONSTRAINTS (the whole point of Fux — do not break):
- $0, stdlib only, deterministic. NO network and NO LLM on the maintenance path (check/gate/verify/seal/
  recall/how). A guard test must prove no network/LLM import is reachable from those modules.
- The agent fetches and interprets; fux governs. Network (HTTP/CDP) and turning text into rule prose are
  the host agent's tokens via a skill — never engine code. Same fence as /fux debate and /fux critic.
- Web-sourced rules are status: draft, never auto-active, never auto-constitutional.
- Files ≤100 lines (≤50 for *_utils). No new runtime deps. Docs in the SAME change.

D — CLI help (build FIRST; it is C's corpus):
- Create ONE structured command registry (single source of truth): per command name, group (authoring ·
  verification · governance · runtime), one-line description, copy-paste example.
- `fux --help` groups commands by group with aligned descriptions (not a flat dump). Add `fux help <cmd>`
  (and `fux <cmd> --help`): description + usage + example + related commands. Stdlib only.
- Regenerate cli.md FROM the registry so docs can't drift from help.

C — fux explains fux (answer how FUX ITSELF works, not just project docs):
- Ship a SELF-KNOWLEDGE BUNDLE: new selfbuild.py (≤100) + `fux self-build` runs fux's own AST graph
  extraction over fux/*.py + reads fux's .fux/rules + docs → emits data/self/{graph.json, rules.json,
  INDEX.md}. $0, deterministic, AST-only, shipped in the wheel.
- Add a `--self` scope to query/explain/path/recall (and the `how` corpus) that reads data/self/ instead
  of the project — works in ANY repo, even one with no .fux/. `fux explain --self "drift"` → how seal/
  check/drift relate across fux's real modules (EXTRACTED+INFERRED edges), grounded in code not prose.
  This is the surface that answers "how does fux work."
- New `how` command + howto.py (≤100): quick answer + the exact command, via the EXISTING recall (recall.py,
  BM25F, $0) over the command registry (D) + self-docs. e.g. `fux how "which rules govern a file"` →
  `fux refs <path>`.
- Deterministic by default. Opt-in `--explain` = richer NL answer using host-agent tokens (fenced) —
  never required, never on the $0 path.

B — Configurable CDP port:
- New cdp_utils.py (≤50): resolve the CDP endpoint by precedence — `--cdp-port`/`--cdp-host` flags →
  FUX_CDP_PORT/FUX_CDP_HOST env → cdp_port/cdp_host in .fux/config.toml → default 127.0.0.1:9299. Add the
  config defaults + template entry. Document the precedence in cli.md.

A — Scrape websites → draft rules (`/fux scrape <url>`, a SKILL):
- Add data/skills/scrape/SKILL.md: the agent (1) fetches via HTTP, escalating to CDP (using cdp_utils for
  the endpoint) when the page is a client-rendered shell; (2) classifies the source → type + trust
  (docs→convention; own docs→rule/glossary; market/data→rule; regulatory/tax/compliance→regulatory,
  DRAFT-VERIFY, human-ratify mandatory); (3) drafts Rule/Why/Edge as status: draft with provenance.
- Schema: add optional `source`, `fetched`, `source_hash` (additive; existing rules stay valid).
- Opt-in only: `fux scrape --recheck` re-fetches a rule's source, recomputes source_hash, raises a new
  `source-drift` finding if it changed — behind a network extra, NEVER on the default check path.
- Wire the skill into install.sh + the skills index.

TESTS + PROVE IT:
- `fux how` returns the correct command + explanation for a fixed question set (deterministic, byte-stable).
- `fux query/explain/path --self` answers from fux's OWN module graph in any repo (no project .fux/ needed);
  the data/self/ bundle regenerates byte-identically from fux's source (self-knowledge can't drift from code).
- CDP endpoint resolves by the full precedence chain; default is 9299.
- Scrape drafts carry source/fetched/source_hash + status: draft; regulatory flagged verify-against-source;
  nothing auto-ratifies.
- GUARD TEST: no network/LLM import reachable from check/gate/verify/recall/how/seal; default install is
  model-free and offline.
- `fux --help` grouped + readable; `fux help <cmd>` shows the example; cli.md regenerated from the registry.
Run `python -m pytest -q` and paste output. Update README/fux-plan/cli.md in the same change.
```
