# Fux — Ingest from Files (generalize `scrape` → `ingest`) · PR2 Handoff

**Owner:** Arpit · **Repo:** `fux` · **Driving model:** Claude Code.
**This is the SECOND, separate PR.** It runs *after* the self-build PR (`selfbuild.py` + `--self`) is merged. Single concern: extend the already-shipped URL scraper into a multi-source ingester.

---

## 0. What's already shipped (PR1 — do NOT redo or break)

`/fux scrape <url>` already exists and is committed: URL fetch with CDP escalation (configurable port), source classification, draft rules with `status: draft` + provenance frontmatter (`source`, `fetched`, `source_hash`), the `--recheck` re-verify, and the `$0`-guard test. **This PR builds on that — it generalizes the source, it doesn't reimplement the pipeline.**

---

## 1. Non-negotiables (unchanged)

- `$0`, stdlib only, deterministic on the engine path. **The agent extracts; fux governs.** Fetching a URL, parsing a PDF/Excel, OCR/vision on an image — all the *host agent's* job via its skills, never engine code.
- The engine imports **no** network, LLM, PDF, Excel, or OCR/vision library. Guard test proves it.
- Ingested rules are `status: draft`, never auto-active, never auto-constitutional.
- Files ≤100 lines (≤50 utils). No new runtime deps. Docs in the SAME PR.

---

## 2. What this PR adds

1. **Rename `/fux scrape` → `/fux ingest`.** Keep a thin **deprecated `scrape` alias** → `ingest` for one release so the just-shipped command doesn't break; print a one-line deprecation note. The rename lands *with* the reason for it (file support), not on its own.
2. **Source-type extract branches (all agent-side).** Only the *extract* step branches; classify → draft → govern is the shipped pipeline, reused:
   - **URL** → HTTP, CDP-escalate on a client-rendered shell (unchanged from PR1).
   - **PDF** → the agent's `pdf` skill (text + tables; OCR for scans).
   - **Excel / .csv** → the agent's `xlsx` skill (structured cells).
   - **TXT / Markdown** → read directly.
   - **Image** → the agent's native vision / OCR.
3. **Schema: add `source_type`** (`url|pdf|xlsx|txt|image`). `source`/`fetched`/`source_hash` already exist from PR1; additive, existing rules stay valid.
4. **Image/OCR trust caution.** A figure read from an image or scanned PDF is low-confidence; an image-derived **money or regulatory** number is flagged `verify-source` and requires human confirmation — NEVER auto-trusted. Regulatory sources stay DRAFT-VERIFY (verify against the primary, human ratify mandatory).
5. **Extend `--recheck` to files.** Re-read a rule's `source` (file bytes or URL), recompute `source_hash`, raise the existing `source-drift` finding when the file/page changed since `fetched`. Still behind the opt-in extra, never on the default `check` path.
6. **Extend the guard test** — engine imports no PDF/Excel/OCR/vision library, in addition to no network/LLM.

---

## 3. Changes (file by file)

1. `data/skills/scrape/SKILL.md` → **rename to** `data/skills/ingest/SKILL.md`; generalize the flow to the five source branches in §2.2; update `install.sh` + the skills index.
2. `cli.py` — rename the `scrape` command to `ingest`; register a deprecated `scrape` alias that calls `ingest` and prints the deprecation note.
3. `data/schema.json` — add optional `source_type` enum.
4. `check.py` — `source-drift` recheck handles file sources (hash file bytes); validate `source_type` when present. No change to the default (non-recheck) path.
5. Tests — ingest from URL/PDF/Excel/TXT/image each produces a `status: draft` rule with `source_type` + provenance; an image/OCR-derived money/regulatory draft is flagged `verify-source`; `--recheck` on a changed file fires `source-drift`; the deprecated `scrape` alias still works; **guard test**: no network/LLM/PDF/Excel/OCR/vision import reachable from the engine path.
5. Docs — `cli.md` (rename, the five sources, `source_type`, deprecation note), `README.md` (one line: "ingest rules from URL/PDF/Excel/TXT/image"), `fux-plan.md` (update the ingestion section).

---

## 4. Acceptance

- `fux ingest <url|file>` drafts rules from a URL, PDF, Excel, TXT, or image, each carrying `source` / `source_type` / `fetched` / `source_hash` and `status: draft`.
- Regulatory and image/OCR-derived money drafts are flagged `verify-source`; nothing auto-ratifies or auto-promotes to constitutional.
- `--recheck` detects a changed file source (`source-drift`), opt-in only.
- Deprecated `scrape` alias still works and warns; rename otherwise complete.
- Guard test green: the engine imports no PDF/Excel/OCR/vision/network/LLM library; default install offline + model-free.
- Files ≤100 lines; docs in sync in this PR.
