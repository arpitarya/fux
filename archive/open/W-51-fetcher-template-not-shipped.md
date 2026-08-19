# W-51 — the default fetcher path names a file fux never writes and does not ship

**Status:** OPEN (Lane A — agent-executable) · **Filed:** 2026-08-19
**Blocked by:** — · **Model:** **Sonnet.** A written definition of done, an
entry in a generated set, and tests — *but land it with
[W-50](W-50-url-fetch-mechanism.md), which writes the file it generates.*
**Opened by:** [ADR-FETCHER](../../docs/adr/0019_fetcher.md) §Consequences

## The defect

Three facts that are individually fine and jointly broken:

| where | says |
|---|---|
| `src/fux/config.py` | `DEFAULT_FETCHER = ".fux/fetchers/cdp.py"` |
| `src/fux/store/fuxdir.py` | `GENERATED_FILES = ("README.md", ".gitignore")` |
| `pyproject.toml` | `[tool.hatch.build.targets.wheel] packages = ["src/fux"]` |

So the documented default names a file that fux **does not generate** and that
is **not in the wheel**. `.fux/fetchers/cdp.py` exists in *this* repo and
nowhere else. A consumer who follows the documentation gets:

```console
$ fux ingest --refresh-urls
error: [sources.url] fetcher not found: .fux/fetchers/cdp.py
# exit 1
```

**URL ingestion has never worked out of the box.** It shipped in 0.31.x and the
only corpus that has ever exercised it is one that happens to contain the file.

## Two live docstrings claim otherwise

- `.fux/fetchers/cdp.py`: *"Fux writes it once if it is missing"* — it does not.
- `src/fux/config.py`: *"the shipped template lives at `.fux/fetchers/cdp.py`"*
  — it is not shipped.

Both were true of an intention, never of the code. They are why the gap survived
a release: every reader who checked found a sentence saying it was handled.

## Definition of done

- [ ] `.fux/fetchers/http.py` joins the generated set and is written
      **write-if-missing** by `ensure_layout`
      ([ADR-HTTP-FETCHER](../../docs/adr/0021_http-fetcher.md) decision 2).
- [ ] **Decide `cdp.py`'s fate in the same change** — the question this item
      cannot answer alone. Either it is generated too (a ~25 KB file every
      consumer gets whether or not they own a browser), or it stops being the
      documented default and becomes a named example the docs point at.
      **`DEFAULT_FETCHER` must name a file that will exist**, whichever way.
- [ ] Both false docstrings corrected — `cdp.py`'s header and `config.py`'s
      `UrlSource` docstring.
- [ ] **Tests:** a fresh tree with `[sources.url]` and a URL list ingests with
      no hand-written fetcher; `ensure_layout` does not overwrite an edited
      `http.py`; `DEFAULT_FETCHER` resolves to a path that exists after a first
      ingest.
- [ ] `CHANGELOG.md` under `[Unreleased] → Fixed`.
- [ ] [ADR-FETCHER](../../docs/adr/0019_fetcher.md) §Consequences and
      [ADR-CDP-FETCHER](../../docs/adr/0020_cdp-fetcher.md) §Consequences:
      replace the known-defect notes with a fixed-in reference.
      **Same change** — Law zero.
- [ ] [ADR-DOTFUX](../../docs/adr/0003_fux-directory.md) decision 2's committed
      list and `fuxdir.py`'s `COMMITTED`/`GENERATED_FILES` agree.
- [ ] This file archived to `archive/open/`, its OPEN-WORK row deleted, outcome
      in [`../IMPLEMENTATION.md`](../IMPLEMENTATION.md).

## Hazards

- **Do not fix it by shipping a fetcher inside the wheel and importing it.**
  A fetcher fux imports is a fetcher fux owns, and the adapter cap is gone —
  [ADR-HTTP-FETCHER](../../docs/adr/0021_http-fetcher.md) §Alternatives rejects
  exactly this.
- **Do not make `ensure_layout` overwrite.** Write-if-missing is what makes a
  generated file safely the consumer's
  ([ADR-DOTFUX](../../docs/adr/0003_fux-directory.md) decision 6). An
  overwriting generator would eat every fetcher edit on the next ingest.

## Evidence

`src/fux/config.py` `DEFAULT_FETCHER` · `src/fux/store/fuxdir.py`
`GENERATED_FILES` · `pyproject.toml` wheel packages — read the three together.
