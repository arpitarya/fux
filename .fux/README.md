# `.fux/`

Fux's directory in your repo. Every child is declared below as
**committed** (belongs in git) or **derived** (rebuildable, ignored,
tagged with [`CACHEDIR.TAG`](https://bford.info/cachedir/)).

| entry | kind | what it is |
|---|---|---|
| `README.md` | committed | this file: written once by fux, yours to annotate |
| `.gitignore` | committed | lists only the derived directories, never `*` |
| `index/` | committed | the wire-format index (ADR-RECORD) |
| `sources/` | committed | the committed source lists (`dirs`, `urls`), one entry per line |
| `fetchers/` | committed | consumer-owned code (`cdp.py`, `http.py`), edit freely |
| `decoders/` | committed | consumer-owned code, one module per format. THESE COPIES ARE WHAT RUN, not the ones inside the installed package (ADR-DECODE) |
| `enrich/` | committed | pinned enrichment text, one file per source content sha, plus `queue.tsv` (W-86 P6: what fux could NOT read and a model must). Committed, because a backlog is a team fact |
| `tune.toml` | committed | the tunables: HOW results are ordered, never what is indexed (ADR-TUNE) |
| `output.toml` | committed | the output defaults: HOW a result is SHOWN, never which documents come back (ADR-OUTPUT) |
| `.fuxignore` | committed | what is NOT indexed, in .gitignore's grammar. The one place exclusions belong, read before the source lists (ADR-FUXIGNORE) |
| `runtime/` | derived | M2 accelerator segments, M4's fetch cache at `runtime/fetch-cache/`, the write lock, and `enrich-progress.tsv` (W-86 P6: which queued documents THIS machine has handled - local by design, so two people's progress cannot conflict on a pull); carries `CACHEDIR.TAG` |

## The fetchers are yours

`fetchers/http.py` and `fetchers/cdp.py` are **your** code, committed
to **your** repo. `fux setup` writes them once if they are missing;
`fux ingest` never writes a fetcher at all. Fux loads one by path
under `fux add <URL>` or `fux update`, and never rewrites it. Change the
port, the transport, the extraction, anything.

One consequence of living in a dotdir: linters that skip hidden
directories by default (ruff does) will not lint it. That is fine, it
is consumer code, not a CI target.

## Rules

- Anything here that is not in the table above is undeclared; `fux
  doctor` warns about it.
- Derived directories can be deleted at any time; committed ones
  cannot be rebuilt from anything but their source systems.
- Fux writes `README.md` and `.gitignore` **only if missing**. Your
  edits survive every ingest.
