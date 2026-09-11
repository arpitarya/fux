---
name: fux-config
description: Read, explain and diagnose Fux configuration — fux.toml, .fux/tune.toml (`fux tune`) and .fux/output.toml (`fux output`), precedence, validation errors, and judging a tuning change honestly. Use for "change fux defaults", "always show the confidence band", "tune ranking weights", "what does this fux.toml key do", "fux.toml won't load". Explaining is always fine; edits change ranking for everyone, so make them ONLY when explicitly asked.
---

# Configuring Fux

Resolve the `fux` command first — see the `fux-usage` skill (`fux` → `uv run fux` → `./.venv/bin/fux`, on Windows `.venv\Scripts\fux.exe` → `python -m fux`).

> ⚠ **These files are committed. An edit changes what every teammate, CI job
> and agent in this repo gets back.** Reading and explaining them is always
> fine. Change one only when a human asked for that change by name.

---

## 1 · Which file owns the question

| the ask | file | how it is written |
|---|---|---|
| where documents come from, how URLs are fetched, which agent files `fux setup` installs | `fux.toml` | `fux setup`, once |
| which documents come back first, confidence floors, how much of a document is indexed | `.fux/tune.toml` | `fux setup` once; `fux tune` prints the defaults |
| how results are shown — band, top, json, sections, hops | `.fux/output.toml` | `fux setup` once; `fux output` prints the defaults |
| what is redacted from the index | `.fux/pii.toml` | see `fux-pii` |

**Fux never rewrites any of them.** `fux tune` and `fux output` read no
repository — they print the **engine defaults**, not this repo's values.
All four are committed; only `.fux/runtime/` and `.fux/acquired/` are local.

**See what this repo changed from the defaults:**

```bash
diff <(fux tune) .fux/tune.toml
diff <(fux output) .fux/output.toml
fux doctor --json    # rows: "fux.toml loads", "output.toml present", "ranking priors"
```

⚠ **`fux doctor` has no row for `tune.toml`.** A broken tune file surfaces on
`fux ask`, `find`, `answer`, `graph`, `path` — not on `doctor`.

⚠ **`fux ask` and `fux find` keep answering on a `fux.toml` that `fux ingest`
refuses.** A query succeeding proves nothing about `fux.toml`; the
`fux.toml loads` row in `fux doctor --json` does.

---

## 2 · `fux.toml` — policy

| key | default | meaning |
|---|---|---|
| `[sources] dirs_file` | `.fux/sources/dirs` | the committed directory list |
| `[sources.url]` *(table)* | absent | its **presence** enables URL ingestion |
| `fetcher` | `.fux/fetchers/http.py` | fetcher for lines with no `fetch=`; its directory is where `fetch=<name>` resolves |
| `urls_file` | `.fux/sources/urls` | the committed URL list |
| `meta` | `"hashed"` | `"hashed"` or `"plain"` — whether display text is readable in the index |
| `max_parallel` | **none — required** | integer ≥ 1; effective value is `min(this, fetcher's MAX_PARALLEL)` |
| `keep` | `true` | retain fetched bytes in `.fux/acquired/` |
| `ttl` | `"24h"` | the URL's declared freshness window — `0` or an integer + `s`/`m`/`h`/`d`; read `answer`'s verdict rather than assuming it (see `fux-answer`) |
| `update` | `"auto"` | `"never"` pins these URLs: `fux update` does not fetch them |
| `enrich` | `false` | whether `fux enrich` plans work for these URLs |
| `sweep_minutes` | `60` | how often `fux daemon` re-checks URLs |
| `acquired_max_bytes` | store default | byte cap on `.fux/acquired/` |
| `[sources.url.config]` | `{}` | handed **verbatim** to the fetcher's `configure()`; fux reads no key in it |
| `[index] shards` | `256` | documents the value; any other number is an error |
| `[agents] install` | all of `claude`, `codex`, `copilot`, `kiro` | vendors `fux setup` writes files for; `[]` = none |

**`meta`, `keep`, `ttl`, `update` and `enrich` are source-wide defaults** — a
line in the URL list that sets the same attribute wins for its own URL.

**Refused by name, with the new home in the message:** `[ranking]`, `[decode]`,
`[dense]`, `[sources] dirs`, `[sources] types_file`, `[sources.url] urls`,
`[sources.url] middleware`.

⚠ **Any other unknown key is silently ignored.** `metta = "plain"` or
`[index] max_phrases = 64` in `fux.toml` does nothing and says nothing. Ranking
and index-limit keys live in `.fux/tune.toml`.

---

## 3 · `.fux/tune.toml` — ranking, plus index limits

| table | keys (engine default) | read by |
|---|---|---|
| `[bm25f]` | `k1` 1.2 (> 0) · `b` 0.75 (0–1) · `body` 1.0 · `heading` 3.0 · `title` 2.0 · `path` 1.5 · `ctx` 1.0 (≥ 0; 0 ignores the field) | `ask` `find` `answer`, MCP |
| `[ranking]` | `archived_weight` 1.0 · `superseded_weight` 1.0 · `recency_half_life_days` 0.0 (off) · `rerank_weight` 0.0 (off) · `expand_weight` 0.2 — all ≥ 0 | same |
| `[graph]` | `damping` 0.85 · `iterations` 3 · `laziness` 0.5 · `hop_decay` 0.5 · `expand_limit` 10 · `seed_depth` 5 | `graph` (`path` reads `hop_decay`) |
| `[refer]` | `budget` 8000 · `per_doc_fraction` 0.5 · `min_passage_bytes` 120 < `max_passage_bytes` 4000 | `answer` |
| `[confidence]` | `separation_floor` 0.1 · `doc_coverage_floor` 0.0 | the **band** only — never a score or an order |
| `[index]` | `max_phrases` 32 · `max_table_rows` 20000 | **`fux ingest`** |
| `[priority]` | `"<source entry>" = <weight>`, unlisted = 1.0 | `ask` `find` `answer` |

- **`expand_weight` is a no-op unless a caller passes `--expand`.** `0` turns
  expansion off even when one is passed.
- **`[priority]`:** weight must be > 0 (zero means exclude — that belongs in the
  source list, see `fux-sources`). Matched as a **string prefix of each result's
  `loc`**, longest entry wins — so `"docs"` also matches `docs-old/…`; write
  `"docs/"`.
- ⚠ **`[index]` changes the committed index.** The next `fux ingest`
  re-extracts every document, and `--no-tune` does not undo it.
- **Absent file or absent key = the engine default.** An unknown table or key
  is an error; up to ten value errors are reported together.
- **`--no-tune`** (on `ask`, `find`, `answer`, `graph`, `path`) ignores the
  file — the *"is it me or the config?"* switch.
- **Receipts:** `fux answer --receipt --json` records `receipt.predicate.inputs.tune`
  — the sha256 of the file's bytes, or `"none"` when absent. **Any byte
  change, a comment included**, makes `fux verify <receipt> --json` report
  `verdict: "drifted:config"`.

---

## 4 · Judging a tuning change honestly

**Rule: compare per query, by rank, against a list written down before the
edit.** Scores are not comparable across settings; an average hides a query
that broke.

1. **Before editing**, write the queries and the `loc` you expect first.
2. **Check the prior can act here.** The `ranking priors` row in
   `fux doctor --json` names each prior switched off and how many documents
   declare its input; **0 documents means changing it changes nothing**.
3. **Capture both arms**, scratch output outside the repo:

   ```bash
   while IFS= read -r q; do
     fux ask "$q" --json --top 5 --no-output-config |
       python3 -c 'import json,sys; print(" ".join(r["loc"] for r in json.load(sys.stdin)["results"]))'
   done < queries.txt > /tmp/before.txt
   # edit ONE key in .fux/tune.toml, re-run into /tmp/after.txt, then:
   diff /tmp/before.txt /tmp/after.txt
   ```

4. **Report fixed and broken counts separately.** Two fixed and two broken is
   not an improvement; a handful of flips on a small set is *no detected change*.
5. **For one query, `fux ask "<q>" --why --json`** gives
   `derivation.documents[].rank` beside `rank_untuned` (present when a tune
   file exists; absent means not computed). ⚠ The untuned arm is the **engine
   defaults**, not your previous file.

---

## 5 · `.fux/output.toml` — how results are shown

| table | keys (default) | reaches |
|---|---|---|
| `[cli]` | `band` false · `top` 5 | `band`: ask/find/answer · `top`: ask/find |
| `[cli.ask]` | `explain` false · `sections` true | ask |
| `[cli.path]` | `hops` 2 | path |
| `[cli.answer]` | `no_refer` false · `journal` false | answer |
| `[cli.json]` | `enabled` false | `--json` on ask, find, answer, explain, graph, path, doctor, hooks, daemon |
| `[mcp]` | `top` 5 | `fux mcp` only |

**Precedence, highest first:**

```text
CLI flag -> [cli.json.<verb>] -> [cli.json] -> [cli.<verb>] -> [cli]     (JSON tables only when JSON is on)
tool argument -> [mcp]                                                   (MCP inherits nothing from [cli])
```

- **A present file is the only source.** A key a verb needs and the file does
  not set is an error naming where to add it. An **absent** file means engine
  defaults, and `doctor` warns `output.toml present`.
- **`--no-output-config`** bypasses the file on `ask`, `find`, `answer`,
  `explain`, `graph`, `path`, `doctor`, `hooks`, `daemon` and `mcp`.
- **A one-verb key at `[cli]` is refused** — `explain` belongs under `[cli.ask]`.
  Also refused: `json` (use `[cli.json] enabled`), `no_tune`, `tune`,
  `no_output_config`, `fast`, `scan`, `no_progress`; under `[mcp]`, `band` and `json`.
- **MCP:** the confidence block is always on. `[mcp]` is read once when
  `fux mcp` starts — **restart the server after an edit**.

**"Always show the confidence band":**

```toml
[cli]
band = true
```

⚠ **`[cli.json] enabled = true` turns JSON on for `doctor`, `hooks`, `daemon`
and the graph verbs too, and there is no `--no-json`.** Scope it — keep the
shared key, since every JSON-capable verb needs one:
`[cli.json] enabled = false` plus `[cli.json.ask] enabled = true`.

---

## 6 · Error → fix

Every one exits `1` and names the file. **Quote the message; fix what it
names.**

| message contains | do |
|---|---|
| `[ranking] moved to .fux/tune.toml` | move the keys into tune's `[ranking]`, delete the table |
| `[decode] moved to .fux/tune.toml` | move `max_table_rows` to tune's `[index]` |
| `max_parallel must be present` | add `max_parallel = 4` under `[sources.url]` |
| `unknown table(s)` / `unknown key(s)` (tune) | fix the spelling; `fux tune` lists every key |
| `field weights lost the _weight suffix` | rename `heading_weight` → `heading`, etc. |
| `does not set` (output.toml) | add the named key where the message says |
| `unresolved merge conflict` | resolve by hand, keep one side |
| `invalid TOML` | fix the syntax at the reported line |

---

## Don't

- **Don't redirect `fux tune` or `fux output` over an existing file.** They print
  engine defaults and would erase this repo's choices. Merge by hand.
- **Don't edit a config file as a side effect** of another task.
- **Don't put tune keys in `fux.toml`** — outside the refused tables, an unknown key there is ignored silently.
- **Don't lower `separation_floor` to make answers read `grounded`.** It makes
  fux quieter about not knowing; it makes nothing better.
- **Don't claim a tuning win from one query or an average score.**
- **Don't take a working `fux ask` as proof `fux.toml` is valid** — check `fux doctor --json`.
- **Don't forget to restart `fux mcp`** after changing `[mcp]`.

`archived_weight` scales documents declared archived (1.0 = no effect); to read a
result carrying `archived: true`, follow the `fux-archived-results` policy.

Related skills: fux-usage, fux-search, fux-answer, fux-graph, fux-sources, fux-index, fux-maintain, fux-mcp, fux-fetcher, fux-pii, fux-decoder, fux-enrich, fux-archived-results.
