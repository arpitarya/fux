# `.fux/`

Fux's directory in your repo. Every child is declared below as
**committed** (belongs in git) or **derived** (rebuildable, ignored,
tagged with [`CACHEDIR.TAG`](https://bford.info/cachedir/)).

| entry | kind | what it is |
|---|---|---|
| `README.md` | committed | this file: written once by fux, yours to annotate |
| `.gitignore` | committed | lists only the derived directories, never `*` |
| `index/` | committed | the wire-format index (ADR-0004) |
| `sources/` | committed | the committed source lists (`dirs`, `urls`), one entry per line |
| `fetchers/` | committed | consumer-owned code (`cdp.py`), edit freely |
| `runtime/` | derived | reserved for M2 accelerator segments; carries `CACHEDIR.TAG` |
| `cache/` | derived | reserved for M4 ARC fetch cache; carries `CACHEDIR.TAG` |

## The fetcher is yours

`fetchers/cdp.py` is **your** code, committed to **your** repo. Fux
loads it by path under `fux ingest --refresh-urls` and never rewrites
it. Change the port, the transport, the extraction, anything.

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
