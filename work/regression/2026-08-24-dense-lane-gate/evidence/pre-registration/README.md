# The frozen pre-registration, mirrored

**Why this directory exists.** [`../../VERDICT.md`](../../VERDICT.md) names its
frozen threshold as `src/fux/query/dense.py` — the bar lived in the module's
own docstring, which is where W-76 Phase 7 put it. **That module was deleted**
when the dense lane and the embedding model were removed (2026-08-25, Arpit).

A verdict is never edited, so `pre_registration:` still reads
`src/fux/query/dense.py`. The file it names is preserved here **byte for byte
as it stood when the verdict was ruled** — verified unchanged between the
commit that filed the verdict (`d3cd187`) and the commit that deleted it.

**The general rule this establishes**, and it is not a one-off: when a
pre-registration's live path is removed, the run carries a mirror of it under
`evidence/pre-registration/<the original path>`, and
[`tests/test_regression_runs.py`](../../../../../tests/test_regression_runs.py)
resolves the pointer here when the live path is gone. **The measurement stays
citable after the code it measured stops existing**, which is the whole reason
`work/regression/` is not allowed to be edited in the first place.

⚠ **This is a mirror, not a live file.** Nothing imports it, nothing runs it,
and it is not the archive: `archive/` holds superseded *decisions*, while this
holds the frozen *threshold* a filed measurement was ruled against.
Archive-is-not-evidence does not apply, because this is the evidence.
