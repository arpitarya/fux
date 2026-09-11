# `.fux/`

Fux's directory in your repo. Every child is declared below, in one
of THREE kinds:

- **committed** - belongs in git. This is the product.
- **derived** - rebuildable from the committed bytes by `fux build`.
  Ignored, tagged with [`CACHEDIR.TAG`](https://bford.info/cachedir/),
  and safe to delete at any time.
- **acquired** - the bytes a fetch returned. Ignored and tagged like
  derived, but NOT rebuildable: deleting it loses the only local copy,
  and getting it back means re-fetching from a source that must still
  exist and a session that must still hold.

| entry | kind | what it is |
|---|---|---|
| `README.md` | committed | this file: written once by fux, yours to annotate |
| `.gitignore` | committed | lists the ignored directories BY NAME, never `*` |
| `index/` | committed | the wire-format index (ADR-RECORD) |
| `sources/` | committed | the committed source lists (`dirs`, `urls`), one entry per line |
| `fetchers/` | committed | consumer-owned code (`cdp.py`, `http.py`), edit freely |
| `decoders/` | committed | consumer-owned code, one module per format. THESE COPIES ARE WHAT RUN, not the ones inside the installed package (ADR-DECODE) |
| `enrich/` | committed | pinned enrichment text, one file per source content sha, plus `queue.tsv` (W-86 P6: what fux could NOT read and a model must). Committed, because a backlog is a team fact |
| `tune.toml` | committed | the tunables: HOW results are ordered, never what is indexed (ADR-TUNE) |
| `output.toml` | committed | the output defaults: HOW a result is SHOWN, never which documents come back (ADR-OUTPUT) |
| `formats.toml` | committed | which files are documents (`include`) and which decoder reads each extension (`[decoders]`). Optional - absent means the built-in default. Replaced .fux/sources/types on 2026-09-11 (ADR-TYPES) |
| `.fuxignore` | committed | what is NOT indexed, in .gitignore's grammar. The one place exclusions belong, read before the source lists (ADR-FUXIGNORE) |
| `pii.toml` | committed | REQUIRED - every command refuses without it. What is REDACTED from the committed index - and ONLY from it. The acquired bytes, the refer plane and every answer quote still see the document as it is (ADR-PII) |
| `refusals.toml` | committed | what a REFUSAL looks like here - the sign-in walls, paywalls and error shells a server returns INSTEAD of the document. Consumer-owned; fux ships no vendor knowledge (ADR-REFUSAL) |
| `runtime/` | derived | M2 accelerator segments, M4's fetch cache at `runtime/fetch-cache/`, the write lock, and `enrich-progress.tsv` (W-86 P6: which queued documents THIS machine has handled - local by design, so two people's progress cannot conflict on a pull); carries `CACHEDIR.TAG` |
| `acquired/` | acquired | the bytes a fetch actually returned, for URLs whose line says keep=true. Gitignored and NOT rebuildable - re-acquirable only, and only while the source is still reachable; carries CACHEDIR.TAG |

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
- Derived directories can be deleted at any time. Committed ones
  cannot be rebuilt from anything but their source systems.
- `acquired/` sits between the two: deleting it costs you the local
  copy of bytes you already fetched, and a re-fetch is the only way
  back. `fux doctor` reports its size.
- Fux writes `README.md` and `.gitignore` **only if missing**. Your
  edits survive every ingest.
