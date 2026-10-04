---
type: Report
description: "W-247, the renderer split: cmd_ask / cmd_find / cmd_answer render what query.build_ask / build_find / build_answer compute, and fux.api reads the same builders. Stdout, stderr and exit code byte-identical on 537 invocations (291 on this repo, 246 on gen-1 rung-01000 re-ingested at v7); the library's own results byte-identical on 93 calls; Node differential 0 of 225."
run: 2026-10-04-api-renderer-split
item: W-247
classification: informed
filed: 2026-10-04
---

# Report: the renderer split is a no-op on every byte it can reach

A byte-equality check. This is a **surface capture** (the verbatim output of
the commands is what is compared) and **not a paired run**: there is no
quality endpoint and no headroom to report. No golden answer, relevance
judgment or score is involved, and nothing here states a quality delta.

## What was compared

The tree at `HEAD` (`877cb4ce`) against the working tree with the split, on the
same two snapshot roots, in one invocation order.

| set | corpus | invocations | identical | different |
|---|---|---:|---:|---:|
| `repo` | this repository's committed index, `git archive HEAD` plus a copied `.fux/runtime` | 291 | **291** | **0** |
| `lab` | fux-lab `corpora/golden/rung-01000`, 1 000 documents | 246 | **246** | **0** |
| | | **537** | **537** | **0** |

"Identical" means the exit code, stdout and stderr all match, byte for byte
(sha256 of each, in `evidence/digests-{before,after}-<set>.jsonl`; the two files
of each set are themselves byte-equal). 509 of the 537 print on stdout; usage
errors (rc 2) are in the set.

**Verbs and modes.** `ask`, `lexical`, `find` and `answer`, each in the modes it
has: prose, `--json`, `--band` (with and without `--json`), `--why` (both),
`--explain`, `--no-sections`, `--no-related`, `--no-tune`, `--fast`, `--expand`,
`-q` fusion (2 extra phrasings), `find --under / --phrase / --all`, and for
`answer`: `--no-refer`, `--audit`, `--receipt`, both together with `--band
--json`, `--cache-ttl`. Queries include a no-match gibberish query, an
archived-document query and a multi-document one. Four answers per two queries
run back to back **without** resetting `.fux/runtime/last-cited.json`, so the
"nothing has changed since you last asked" stderr report is exercised. The
list is `evidence/capture.py::invocations`.

## The library

`fux.api` was rewritten onto the same builders, so it is held to the same bar:
`evidence/library_dump.py` calls `find` (default, `top=2`, `under=`), `ask`
(default, `band=False, sections=False`, `queries=` fusion) and `answer` (refer
and `--no-refer`, with and without audit and receipt) and dumps `as_dict()` plus
captured stderr. Old tree against new: **byte-identical on `repo` (51 calls) and
`lab` (42 calls)**, sha256 in `evidence/library-dump-sha256.txt`.

`tools/differential/node_arm.py .`: **discordant 0 of 225**, including the
published bundle (8 queries x 3 verbs).

## How the comparison was made, and its limits

- **Before = the `HEAD` tree**, extracted with `git archive HEAD src` and put
  first on `PYTHONPATH`; **after = the working tree**. Same interpreter, same
  snapshot roots, same order. Raw captures (about 4 MB) were kept outside the
  repo; the digests are filed.
- **Both roots are copies.** `fux answer` writes `.fux/runtime/last-cited.json`
  and a live repo moves under a concurrent session, so neither the repo nor
  fux-lab was run in place. Every invocation starts with that file removed
  (except the deliberate `!keep` ones).
- **The `lab` copy is not the rung as it stands.** The rung's index is
  `fux.index.v5` and its `output.toml` predates `max_headings`, so this engine
  refuses every verb on it. In the *copy only* I ran `fux doctor --fix` and
  `fux ingest --full`, then `fux build`. The 1 000 documents are the rung's, the
  v7 index is regenerated. The original under `fux-lab/` was not touched
  (`git status` there shows only the `fux.toml` that was already untracked).
  `fux build` was also run in the repo snapshot, so the graph tier and the
  related tier are live in both.
- **Not covered:** `--journal` (it writes `provenance.jsonl`), a live URL fetch
  (both corpora are local files), `fux lexical --fast`, and `fux mcp` / `serve`,
  which read `run_query` directly and do not go through these functions.
- The first "after" pass differed on 40 and 59 `answer` invocations by one stderr
  line, `nothing has changed since you last asked`. That was the capture, not the
  code: a library dump had left `last-cited.json` populated and the script
  treated it as the pristine state. The script now removes the file per
  invocation and both sides were re-captured from scratch.

## Authorship

| artifact | author | could reach |
|---|---|---|
| `evidence/capture.py`, `evidence/library_dump.py`, the query lists | the W-247 builder session (Sonnet), before the refactor | none: no question set, judgment or score is involved |
| the refactor and this report | the same session | none |

Labelled `informed` because the builder chose the invocations it then
verified. It claims nothing a golden set could: only that these 537 invocations
print the same bytes.

## Reproduce

```bash
git archive HEAD src | tar -x -C "$OLD"          # the tree before
git archive HEAD | tar -x -C "$SNAP"; cp -a .fux/runtime "$SNAP/.fux/runtime"
(cd "$SNAP" && ../.venv/bin/python -m fux build)
PYTHONPATH="$OLD/src" .venv/bin/python work/regression/2026-10-04-api-renderer-split/evidence/capture.py run --set repo --root "$SNAP" --out before/repo
PYTHONPATH="$PWD/src" .venv/bin/python work/regression/2026-10-04-api-renderer-split/evidence/capture.py run --set repo --root "$SNAP" --out after/repo
.venv/bin/python work/regression/2026-10-04-api-renderer-split/evidence/capture.py diff before/repo after/repo
```

`lab` is the same against a copy of `fux-lab/corpora/golden/rung-01000` after
`fux doctor --fix`, `fux ingest --full` and `fux build` in the copy.
