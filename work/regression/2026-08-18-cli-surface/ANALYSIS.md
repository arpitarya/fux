# ANALYSIS — 2026-08-18 CLI surface capture

Two findings. One is a defect with a one-line fix; the other is a naming
hazard that costs nothing to leave alone and would cost a release to change.

---

## Finding 1 — `ask --hybrid` crashes on a source install (defect)

**What happens.** `fux ask <q> --hybrid` raises an unhandled `AttributeError`
and prints a traceback when the bundled model is absent:

```
File ".../fux/query/hybrid.py", line 97, in _dense_ids
    vec = get_model().embed(query)
AttributeError: 'NoneType' object has no attribute 'embed'
```

**Why it is a real defect and not a fixture artifact.** The graceful path was
*written and is dead*. `_dense_ids` already guards this exact case —

```python
    try:
        from ..embed import get_model, quantize
        vec = get_model().embed(query)
    except (FuxError, ImportError, FileNotFoundError):
        return []  # no bundled model in this install; lexical still answers
```

— and `get_model()`'s own docstring says it returns **`None` when the bundle
isn't shipped (source installs)**. Returning `None` is a documented, supported
state. The `except` tuple simply does not include the exception that state
actually produces, so the intended fallback never runs.

**It is reachable.** Verified directly on the fixture with the bundle removed:

```
dense codes loaded: 3
get_model() -> None
```

The dense codes are derived from the committed index and build **without** the
model, so `_dense_ids` gets past its `if not codes: return []` early exit and
straight into the crash. A source install — `pip install -e .`, a git checkout,
any environment where `src/fux/embed/data/model.bin` was not packaged — has
everything it needs to hit this.

**Why it was not caught.** It cannot reproduce on a machine where the bundle is
present, which is every machine this engine has been developed on. `--hybrid`
is also default-off, so nothing in the ordinary path exercises it.

**The irony worth recording.** The docstring immediately above the broken guard
warns against *"a silent degradation that looks like a working feature — exactly
the failure mode this engine keeps writing tests against."* The author saw the
hazard, wrote the guard, and the guard catches the wrong exceptions.

**Fix.** Handle `None` explicitly rather than widening the `except` — a bare
`except AttributeError` would swallow real bugs inside `embed()`:

```python
    model = get_model()
    if model is None:
        return []          # no bundled model in this install; lexical still answers
    vec = model.embed(query)
```

**Test.** `tests/query/` has no coverage for the missing-bundle path. The
regression test monkeypatches `get_model` to return `None` and asserts
`ask --hybrid` still answers from the lexical lane, exit 0.

**Filed as [W-46](../../open/W-46-hybrid-missing-model-crash.md).** Not fixed
here: this session's mandate is documentation, and a code change belongs in its
own commit with its own test.

---

## Finding 2 — exit code 2 is defined and never produced

`FuxError` carries an `exit_code` defaulting to 1, and CLAUDE.md's error
contract reserves **`2` for blocking (strict)**. Across 48 `raise FuxError`
sites in `src/`, **not one passes `exit_code=2`**:

```console
$ grep -rn 'exit_code' src/ --include='*.py'
src/fux/cli.py:119:        return exc.exit_code
src/fux/errors.py:20:        self.exit_code = exit_code
```

So the current surface produces only `0`, `1`, and `130`.

**This is not a defect, and the recommendation is to leave it.** Exit codes are
API: a script that today treats "not 0" as failure keeps working, and a `2` that
appears later is a *narrowing*, which is a compatible change. Removing `2` from
the contract now, then needing it when the strict-mode hooks arrive at M5, would
be the expensive direction.

**What is worth doing** is saying so out loud rather than letting a reader infer
that `2` is live. Recorded in [ADR-CLI](../../../docs/adr/0002_cli-surface.md)
§Decision: `2` is **reserved, not yet produced**.

---

## What this capture does not establish

- **Nothing about ranking quality.** Three documents, hand-written to be
  distinguishable. Every score here is a property of the fixture.
- **Nothing about the differential law.** `--scan` and the accelerator agreed
  on this corpus, which is necessary and nowhere near sufficient; the law's
  evidence is the [M2 run](../2026-08-12-m2-accelerator/report.md) and its
  6 088 comparisons.
- **Nothing about performance.** No timings were taken, and wall-clock from
  the cloud container is not comparable to any other surface
  ([`../../MACHINE.md`](../../MACHINE.md)).
