"""`fux doctor`'s provenance row, and the fence that keeps it off the hot path.

W-200's row answers the one question a plain `fux ingest` cannot fix: **a record
produced by a decoder the tree no longer carries at that version.** The reuse
key ([W-166](../archive/open/W-166-carry-forward-invalidation.md)) catches a decoder whose
digest *moved since the last run* and re-extracts its documents; it cannot catch
a record written before the binding existed, or one carried through a run where
the digest map could not be read. Those records agree with nothing and no delta
run looks at them again. `fux ingest --full` is the fix.

🔴 **Absent is not a finding, and that is the decision this file pins.** A repo
that has not ingested since W-200 landed has no ledger. Reporting that as a
problem would put a warning in front of every consumer on upgrade, for a file
that is advisory, derived, gitignored and one `fux ingest` from existing — which
is how a doctor row becomes one people learn to skip.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from fux import doctor
from fux.ingest import ingestlog as provenance

ROOT = Path(__file__).resolve().parents[1]


def _repo(tmp_path) -> Path:
    (tmp_path / "fux.toml").write_text("[sources]\n", encoding="utf-8")
    fux = tmp_path / ".fux"
    (fux / "sources").mkdir(parents=True, exist_ok=True)
    (fux / "sources" / "dirs").write_text("docs\n", encoding="utf-8")
    (fux / "pii.toml").write_text("", encoding="utf-8")
    (tmp_path / "docs").mkdir(exist_ok=True)
    return tmp_path


def _row(decoder: str) -> provenance.Row:
    return provenance.Row(
        id="file:docs/t.csv",
        kind="file",
        loc="docs/t.csv",
        outcome="reused",
        run_seq=0,
        decoder=decoder,
    )


def test_no_ledger_is_not_a_finding(tmp_path):
    check = doctor._provenance(_repo(tmp_path))
    assert check.ok, "a repo that has not ingested yet must not be warned at"
    assert check.level == "warn"
    assert "fux ingest" in check.detail, "it must say how to get one"


def test_a_stale_decoder_is_reported_and_names_the_full_flag(tmp_path, monkeypatch):
    """🔴 `--full` is named because a plain `fux ingest` genuinely will not fix
    this, and a row that names the wrong remedy is worse than none."""
    root = _repo(tmp_path)
    provenance.write(root, [_row("csv@sha:0000000000000000")])
    monkeypatch.setattr(
        "fux.ingest.decoderdigest.binding_digests",
        lambda r=None: {".csv": "csv@sha:1111111111111111"},
    )
    check = doctor._provenance(root)
    assert not check.ok
    assert check.level == "warn", "the index is not wrong, only possibly stale"
    assert "ingest --full" in check.detail


def test_a_current_ledger_is_clean(tmp_path, monkeypatch):
    root = _repo(tmp_path)
    provenance.write(root, [_row("csv@sha:1111111111111111")])
    monkeypatch.setattr(
        "fux.ingest.decoderdigest.binding_digests",
        lambda r=None: {".csv": "csv@sha:1111111111111111"},
    )
    check = doctor._provenance(root)
    assert check.ok and check.level == "error", "a clean row is an ordinary OK"
    assert "1 record" in check.detail


def test_the_json_block_distinguishes_unknown_from_clean(tmp_path, monkeypatch):
    """⚠ `{}` and `{"stale_decoders": 0}` say different things.

    A caller checking its index in CI and told `0` where nothing was checked
    has been told something false in the direction that matters.
    """
    root = _repo(tmp_path)
    assert doctor.provenance_counts(root) == {}, "no ledger is UNKNOWN, not clean"

    provenance.write(root, [_row("csv@sha:1111111111111111")])
    monkeypatch.setattr(
        "fux.ingest.decoderdigest.binding_digests",
        lambda r=None: {".csv": "csv@sha:1111111111111111"},
    )
    assert doctor.provenance_counts(root) == {"rows": 1, "stale_decoders": 0}


def test_the_row_is_registered_in_the_check_list(tmp_path):
    """A check function nothing calls is a function, not a check."""
    names = {c.name for c in doctor.run(_repo(tmp_path))}
    assert "provenance" in names


# --- the fence: nothing on the query path may read this ------------------


QUERY_PLANES = ("query", "refer", "derive")

#: 🔴 **W-200's spec called this module `ingest/provenance.py` and both that
#: name and its file were already taken.**
#:
#: - `fux.query.provenance` — SR-PROVENANCE's **answer receipts**: how an answer
#:   was produced, and a thing [L8](../records/0010_LAW-8-use-record.md)
#:   governs, because it records what somebody **asked**. Its journal is
#:   `.fux/runtime/provenance.jsonl`, written **only under explicit consent**.
#: - `fux.ingest.ingestlog` — W-200's ledger: what read each document, and a
#:   thing L8 does **not** reach, because it records nothing about a query.
#:   `.fux/runtime/ingest-log.jsonl`, written by every ingest.
#:
#: **The file collision was a defect, not a confusion**: writing this ledger to
#: the journal's path made every `fux ingest` create a file that requires
#: consent, and the e2e suite caught it with *"a journal appeared with no
#: consent of any kind"*. **L8 outranks a work item**, so both moved.
#:
#: The fence below matches the **fully qualified name**: a bare substring on
#: `"provenance"` would flag every query module that legitimately imports the
#: receipts, which is the same false positive
#: `test_golden_key_never_committed.py` hit on its first run.
_INGEST_LEDGER = frozenset(
    {
        "fux.ingest.ingestlog",
        "..ingest.ingestlog",
        "...ingest.ingestlog",
    }
)


def _imports(path: Path) -> set[str]:
    """Every module name a file imports, as `ast` sees it — never by executing."""
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (SyntaxError, OSError, UnicodeDecodeError):  # pragma: no cover
        return set()
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom):
            base = node.module or ""
            names.add(base)
            names.update(f"{base}.{a.name}" if base else a.name for a in node.names)
    return names


@pytest.mark.parametrize("plane", QUERY_PLANES)
def test_no_query_plane_module_imports_provenance(plane):
    """🔴 **Never on the hot path**, and asserted rather than intended.

    `docs.jsonl` is read on every `ask`; this ledger is read by `doctor` and by
    humans. The separation is the fourth of W-200's five decisions and it is the
    one that would rot first — a future *"while we're here, show which decoder
    produced this result"* is one import away, and it would put a per-document
    file read into every query.

    Checked with `ast` and **never by importing**, so the test itself cannot be
    the thing that creates the dependency.
    """
    offenders = [
        str(path.relative_to(ROOT))
        for path in sorted((ROOT / "src" / "fux" / plane).rglob("*.py"))
        if any(name in _INGEST_LEDGER for name in _imports(path))
    ]
    assert not offenders, (
        f"a module under src/fux/{plane}/ imports the provenance ledger:\n  "
        + "\n  ".join(offenders)
        + "\n\nIt is read by `doctor` and by humans, never at query time (W-200)."
    )
