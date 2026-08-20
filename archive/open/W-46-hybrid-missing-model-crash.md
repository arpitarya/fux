# W-46 — `ask --hybrid` crashes on a source install

**Status:** OPEN (Lane A — agent-executable) · **Filed:** 2026-08-18
**Blocked by:** — · **Model:** Sonnet (a written definition of done, a test to
verify it, three lines of code)

## The defect

`fux ask <q> --hybrid` raises an unhandled `AttributeError` and prints a
traceback when the bundled embedding model is absent:

```
File "src/fux/query/hybrid.py", line 97, in _dense_ids
    vec = get_model().embed(query)
AttributeError: 'NoneType' object has no attribute 'embed'
```

This breaches the error contract twice over: a traceback reaches the user, and
a documented, supported state produces a crash instead of the fallback that was
written for it.

## Why it is real

`get_model()` returns **`None` when the bundle isn't shipped (source
installs)** — its own docstring. `_dense_ids` already guards the case:

```python
    except (FuxError, ImportError, FileNotFoundError):
        return []  # no bundled model in this install; lexical still answers
```

The guard is correct in intent and dead in practice: `None.embed(...)` raises
`AttributeError`, which is not in the tuple.

**Reachable, verified** on the 2026-08-18 fixture with the bundle removed —
`dense codes loaded: 3`, `get_model() -> None`. Dense codes derive from the
committed index and build without the model, so the early `if not codes:
return []` does not save it.

It has gone unnoticed because it cannot reproduce where `model.bin` is present,
which is every development machine, and `--hybrid` is default-off so nothing
routine exercises it.

## Definition of done

1. `src/fux/query/hybrid.py::_dense_ids` handles `None` explicitly — **not** by
   widening the `except` to `AttributeError`, which would swallow real bugs
   inside `embed()`:

   ```python
   model = get_model()
   if model is None:
       return []          # no bundled model in this install; lexical still answers
   vec = model.embed(query)
   ```

2. A regression test in `tests/query/` monkeypatches `get_model` to return
   `None` and asserts `ask --hybrid` still answers from the lexical lane at
   exit 0 — the behaviour the dead guard intended.
3. `CHANGELOG.md` under `[Unreleased] → Fixed`.
4. [ADR-CLI](../../docs/adr/0002_cli-surface.md) §Consequences: strike the
   "we now owe a regression test" line; the known-defect note under
   `ask --hybrid` becomes a fixed-in reference.
5. This file and its OPEN-WORK row **deleted**, with the outcome recorded in
   [`../IMPLEMENTATION.md`](../IMPLEMENTATION.md).

## Hazards

- **Do not fix by making `get_model()` raise.** It is called on lexical-only
  paths where `None` is the cheap, correct answer; raising would put a
  try/except on the hot path.
- **Do not ship the model bundle to make this go away.** Source installs
  without it are supported by design (law L1 — the runtime is stdlib-only and
  the bundle is optional).

## Evidence

[`../regression/2026-08-18-cli-surface/ANALYSIS.md`](../regression/2026-08-18-cli-surface/ANALYSIS.md)
§Finding 1 — diagnosis, the reachability proof, and the reproduce fixture.
