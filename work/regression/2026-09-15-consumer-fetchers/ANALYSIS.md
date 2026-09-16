---
type: Analysis
name: consumer-fetchers-analysis
description: "What the W-178 capture grounds, the failure mode it measured rather than predicted (a typo takes the whole ingest down, not one line), and the message it fixed on the way."
---

# What the capture grounds, and the one thing it measured

## The definition of done, item by item

| DoD | shown by |
|---|---|
| 1 · `fetch` is typed | `fetch=glassbox` parses and ingests |
| 2 · shape-only validation, enum-shaped error | `Glassbox`, `cdp.py`, `../evil`, `_shared` each refused naming what was wrong (`tests/ingest/test_sourcelist.py`) |
| 3 · the header stops printing `<duration>` for everything | `fetch=<name>` beside `ttl=<duration>` in the generated `.fux/sources/urls` |
| 4 · a `fux doctor` row | `fetcher bindings`, both branches captured |
| 5 · the `Attribute` docstring no longer asserts the enum for `fetch` | `src/fux/ingest/sourcelist.py` |
| 6 · a consumer drops a file in and it works | `fux answer "pager rota"` returns `glassbox.py`'s bytes, cited |

---

## 🔴 What was measured rather than predicted

**W-178 §4 item 4 argued for the doctor row like this:** a name with no file is
*"discovered when the next person's ingest dies"*. That framing understates it,
and the capture is what makes the difference visible.

**A missing fetcher is not a per-line skip. It is a whole-run failure.**

```console
$ fux ingest
error: fetcher not found: .fux/fetchers/glasbox.py …
# exit 1
```

`load_fetcher` raises, and nothing catches it into the per-URL skip path — so
**one wrong character on one URL line indexes zero documents**, including every
directory in the corpus that has nothing to do with URLs. The transient-failure
guarantee ([SR-URL-INGEST](../../../records/0107_url-ingest.md) decision 3)
covers a fetch that *fails*; it does not cover a fetcher that cannot be
*loaded*, and that distinction was not written down anywhere before this run.

- **That is not a regression** — the same blast radius existed for a
  mistyped `[sources.url] fetcher` path long before W-178.
- **It is a bigger population now.** The enum meant a bad `fetch=` value was a
  parse error at read time; an open set means it is a runtime failure. The
  doctor row is what keeps the cost where it was, and the capture is why it
  reads as necessary rather than as tidiness.
- **Not escalated to an item.** Making a missing fetcher a per-line skip would
  mean a repo silently indexing a subset of its corpus — the opposite trade, and
  a worse one. Stated here so the next person does not rediscover it.

## Fixed on the way

**`load_fetcher`'s error named the wrong remedy for a custom name.** It said
*"run `fux setup` to write the shipped fetchers"*, which is correct when the
directory is empty and misleading when it holds `glassbox.py` and the line says
`glasbox`: `fux setup` writes two files and neither is the one being asked for.
It lists the sibling stems now — turning a typo into a one-character fix — and
falls back to the setup hint only when there is nothing beside it.

## What this run does NOT claim

- **Nothing about a real fetcher or a real network.** Local four-line modules.
- **Nothing about `fux add --fetch`.** No such flag exists, deliberately.
- **Nothing about decoders.** The symmetry claim is recorded in
  [SR-DECODE](../../../records/0139_decode.md); this run exercises one half.
