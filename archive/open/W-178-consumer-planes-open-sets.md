---
type: Handoff
name: W-178
description: "`fetch=` becomes a TYPED attribute validated by NAME SHAPE, not an enum of shipped fetchers — so a consumer drops `.fux/fetchers/<name>.py` in and writes `fetch=<name>`, exactly as `.fux/decoders/<name>.py` + a `[decoders]` binding already works. Ruled by Arpit 2026-09-15. Ratified, NOT built."
item: W-178
filed: 2026-09-15
ball: agent
---

# W-178 — a consumer's fetchers open the same way their decoders already do

**Ratified, not built.**

**Model: Sonnet** for the diff — the change is four lines plus a doctor check,
and `types.decoder` is an exact, shipped precedent to copy. ⚠ **One paragraph is
Opus-shaped and is written out in full below** (§6): whether an open `fetch=`
name set widens L4's blast radius. It is analysed here so the build does not
have to re-reason it, but a reviewer should read that section rather than skim it.

## The ruling (Arpit, 2026-09-15, Cowork)

> *"I want a pattern where a consumer can build custom fetchers as well as custom
> decoders. They just put the file in those directories and then use flags and
> format file to map them."*

**Half of this already ships.** The ruling is a statement of symmetry, and the
work is making the fetcher side match the decoder side — not inventing a
mechanism.

## 1. The asymmetry, stated

| | decoders — **works today** | fetchers — **blocked** |
|---|---|---|
| where the file goes | `.fux/decoders/<name>.py` | `.fux/fetchers/<name>.py` |
| how it is mapped | `[decoders]` binding in [`.fux/formats.toml`](../../.fux/formats.toml) | `fetch=<name>` on a line in [`.fux/sources/urls`](../../.fux/sources/urls) |
| what validates the name | **shape only** — `_decoder_reason`, a module-stem regex | 🔴 **an enum of the two shipped fetchers** |
| where existence is checked | `decode.registry()` at ingest, plus a `fux doctor` row | ⚠ `urlsrc._fetcher_path()` at fetch time; **no doctor row** |
| custom name accepted? | **yes** — `confluence = "confluence"` is legal | **no** — rejected by the grammar |

## 2. The blocker, exactly

```python
# src/fux/ingest/sourcelist.py:263
Attribute("fetch", ("http", "cdp"), "http"),
```

A closed tuple. `fetch=glassbox` is rejected by the grammar **before**
`urlsrc.py` ever resolves the name.

🔴 **And the code on the other side of that gate already does the right thing.**
`src/fux/ingest/urlsrc.py` resolves by filename —

```python
def _fetcher_path(source_fetcher: str, fetch_name: str) -> str:
    """`fetch=<name>` -> `<fetchers dir>/<name>.py`, the dir from the config key."""
    return str(PurePosixPath(PurePosixPath(source_fetcher).parent) / f"{fetch_name}.py")
```

— and already raises a clean, actionable error when the file is absent
(`urlsrc.py:104`, *"fetcher not found: … — run `fux setup` …, or point
`[sources.url] fetcher` at …"*). **The module docstring states the open
behaviour as fact:** *"a name resolves to `<fetchers dir>/<name>.py`"*.

**The docstring and the validator have drifted, and nothing noticed.** This is
the W-83 class, and it is why the item exists even aside from the ruling: **no
third fetcher of any kind is possible today**, and neither
[SR-URL-LIST](../../records/0116_url-list.md) nor
[SR-CDP-FETCHER](../../records/0118_cdp-fetcher.md) says the set should be closed.

## 3. The precedent to copy — do not invent a second mechanism

`Attribute` already supports exactly this: **`values` empty + a `validate`
callable = a typed attribute** (`sourcelist.py:75-101`). `ttl` was the first;
`types.decoder` is the one to mirror, because it is a *name*, not a duration:

```python
# sourcelist.py:358
attributes=(Attribute("decoder", (), "", validate=_decoder_reason),),
```

`_decoder_reason` (`sourcelist.py:239-257`) validates **shape only**, and its
docstring already states the split this item should reuse verbatim:

> *"Whether a module by that name exists is deliberately NOT checked here: the
> parser cannot reach the decoder registry, and reaching for it would make
> reading a config file depend on importing every decoder."*

**The same reasoning holds for fetchers, and more strongly** — importing a
fetcher to validate a config line would fire `connect()` on a browser.

## 4. Definition of done

1. `fetch` is a typed attribute: `Attribute("fetch", (), "http", validate=_fetcher_reason)`.
2. `_fetcher_reason` mirrors `_decoder_reason` — a module-stem regex, shape only,
   no existence check, an error message of the same *kind* the enum produced.
   ⚠ Its default is `"http"`, **not `""`**, so `render_line`'s empty-default
   exception (`sourcelist.py:521-527`) does not apply and every generated line
   still states `fetch=`.
3. 🔴 **`_urls_header()` stops rendering `<duration>` for every typed attribute.**
   `src/fux/setup.py:668-672` hardcodes the typed placeholder:

   ```python
   (f"{a.name}={'|'.join(a.values) if a.values else '<duration>'}", a.default)
   ```

   Flip `fetch` to typed and **every repo `fux setup` touches gets a header
   saying `fetch=<duration>`.** The placeholder must come from the attribute.
   ⚠ **This is W-140 row 18 returning** — that header went stale once by being
   transcribed, was fixed by being *derived*, and this is the derivation itself
   being wrong. The fix is a placeholder field on `Attribute`, not a special case
   in `setup.py`.
4. **A `fux doctor` row for fetcher bindings**, mirroring `_decoder_bindings`
   (`doctor.py:860`): a line whose `fetch=` names a file not on disk is reported
   by `doctor`, not discovered when the next person's ingest dies.
   ⚠ `_fetcher_config_tables` (`doctor.py:547`) already asserts the opposite
   direction — *"each naming a fetcher on disk"* — so half the check exists and
   the two should read as a pair.
5. The `Attribute` docstring is amended. It currently says the enum *"is still
   the default and still the right shape for `fetch`, `meta`, `archived` and
   `keep`"* (`sourcelist.py:82-84`). **This ruling overturns that for `fetch`**,
   and a docstring asserting the opposite of the code is the defect this item
   was filed over.
6. A consumer can drop `.fux/fetchers/anything.py` in, write `fetch=anything`,
   and ingest — with no engine change and no fux release.

## 5. In scope / out of scope

**In:** the grammar, the header derivation, the doctor row, the records, the tests.

**Out:**
- **No new fetcher is written.** Not Glassbox, not anything.
  [`glassbox-sessions.md`](../proposals/glassbox-sessions.md) (B-248) stays a
  proposal and its §6 still argues sessions may not belong in the URL list at all.
- **No change to the decoder side.** It already works; this item makes the
  fetcher side match it.
- **`meta`, `keep`, `archived`, `enrich`, `update` stay enums.** They are policy
  values with a genuinely closed set. Only `fetch` names a *file*.
- **The attribute set stays closed.** Seven attributes, and adding an eighth is
  still a change to SR-URL-LIST. **Open values, closed keys** — the two are not
  the same loosening and this item only does the first.

## 6. ⚠ Does this widen L4? — read this section

**Claim: no, and the reasoning has to be stated because it looks like it does.**

An open `fetch=` name means a committed line can cause the engine to import an
arbitrary `.py` from `.fux/fetchers/` and call `fetch()` on it, over the network.

**That is already true today.** Three facts, each already recorded:

- **`cdp.py` is already arbitrary consumer code.** `fux setup` writes it once
  and never rewrites it ([SR-LAW-4](../../records/0006_LAW-4-offline-by-default.md):
  *"Network code lives in the consumer's repo, not in the package"*). A consumer
  can put anything in it today without touching the grammar.
- **The directory is already consumer-chosen.** `[sources.url] fetcher` names a
  path, and the fetcher dir is its parent — so *where* fux imports from is
  already a config key, not a constant.
- **The fence is the verb, not the name.** L4's two networked paths are
  `fux add <URL>` and `fux ingest`
  ([SR-CLI](../../records/0101_cli-surface.md) decision 16 — W-177 landed
  2026-09-15 and renamed the second one). Which fetcher file runs inside a
  fenced path does not move the fence.

**What actually changes** is that the *set of files that can be reached* goes
from two to "whatever is in the committed directory" — which is why §4 item 4's
doctor row is not optional. **A fetcher nobody can see is the risk; a fetcher
`doctor` names is not.**

## 7. Records to amend in the same change

| record | what changes |
|---|---|
| [SR-URL-LIST (0116)](../../records/0116_url-list.md) | `fetch=`'s grammar: a **name**, shape-validated, not an enum. §"the closed set of attributes" must be re-read as *closed keys, open values* — it currently reads as both |
| [SR-URL-INGEST (0107)](../../records/0107_url-ingest.md) | owns *what fetches a URL*; state that a name resolves to a file and that the set is open by construction |
| [SR-CDP-FETCHER (0118)](../../records/0118_cdp-fetcher.md) | decision 6, *"This fetcher is chosen by declaration"* — still true, now one of many rather than one of two |
| [SR-DECODE (0139)](../../records/0139_decode.md) | add the symmetry statement: fetchers and decoders are the **same consumer-plane pattern**, so a future change to one is a question about the other |
| [SR-DOCTOR (0152)](../../records/0152_doctor.md) | the new check row |
| [SR-LAW-4 (0006)](../../records/0006_LAW-4-offline-by-default.md) | ⚠ **only if §6 is judged wrong on review.** If §6 stands, L4 is untouched and this row is deleted rather than filled in with a no-op |

⚠ **`fux.toml`'s comments name the two fetchers** (*"Only `.fux/fetchers/cdp.py`
receives these"*). Those are per-table and stay correct; the section comment
above them should stop implying the set is two.

## 8. Tests

- Grammar: `fetch=glassbox` parses; `fetch=Glassbox`, `fetch=cdp.py`,
  `fetch=../evil`, `fetch=_shared` are each rejected **with the enum's kind of
  error** — naming what was wrong, not what was expected.
- Round-trip: `render_line` → `read_urls` is stable for a custom name.
- 🔴 **A regression test on the derived header**: `_urls_header()` contains no
  `<duration>` for a non-duration attribute. This is the one that would have
  caught W-140 row 18 the first time.
- Doctor: a line naming a missing fetcher produces a failing row, not a green run.
- Existing `http`/`cdp` lines are unchanged — every list valid today stays valid.

## 9. Open questions

1. **Is the placeholder a field on `Attribute` or a method?** §4 item 3 says
   field; a method would let `ttl` keep `<duration>` without a literal. Builder's
   call, but it must not be a branch in `setup.py`.
2. **Does `fux setup` grow a `--fetcher` scaffold** that writes a stub
   consumer fetcher with the contract docstring? ⚠ Out of scope here — filed as
   a question, not a task, because it is a new surface and SR-CLI owns it.
3. ✅ **W-177 interaction — RESOLVED, W-177 landed first** (2026-09-15).
   `_urls_header()`'s prose named `fux update`; it names `fux ingest` and
   `--refetch-all` now, and the attribute table it derives is unchanged, so this
   item inherits a correct header and touches none of it.
