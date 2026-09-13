"""`fux.api` — the importable read surface (SR-API).

Four things are asserted here and each is a promise the record makes:

1. **`from fux import open` resolves.** The record and `.fux/README.md` both
   document that spelling, and nothing but the re-export in
   `src/fux/__init__.py` makes it true — a file SR-LAWS owns, which is why the
   register carries a `describes` row pointing at this record.
2. **The gate fires here too.** `open()` outside a root, and `open()` in a repo
   with no `.fux/pii.toml`, both raise `FuxError`. A library caller that
   bypassed the gate would be reading a promise the CLI does not make
   (SR-PII decision 17; W-107 O1 answered the same way for Node).
3. **The gate costs a STAT, not an import.** `from .ingest import pii` pulls in
   every decoder — measured 2026-09-12 at **50 ms on a warm `fux.open(".")`**,
   against 2.6 ms after. `cli.py` spells the path inline for exactly this
   reason and `tests/test_cli.py` holds the copies equal.
4. **`as_dict()` is the `--json` payload**, validated against
   `query/output.schema.json` — the one public shape fux has, and now the
   contract for three readers rather than one.
"""

from __future__ import annotations

import sys

import pytest

from fux.errors import FuxError
from fux.output_config import OUTPUT_NAME, specimen
from fux.schema import load as load_schema
from fux.store import TF_FIELDS, term_hash, write_index

BODY = TF_FIELDS.index("body")


def _rec(doc_id: str, title: str, word: str, *, phrases=(), mtime=None) -> dict:
    tf = [0] * len(TF_FIELDS)
    tf[BODY] = 5
    flen = [0] * len(TF_FIELDS)
    flen[BODY] = 40
    record = {
        "id": doc_id, "src": "git", "loc": doc_id.removeprefix("file:"),
        "mode": "extracted", "meta": "plain", "title": title,
        "phrases": list(phrases), "terms": {term_hash(word): tf},
        "flen": flen, "sha": "a" * 40, "edges": [],
    }
    if mtime is not None:
        record["mtime"] = mtime
    return record


@pytest.fixture
def repo(tmp_path):
    (tmp_path / ".git").mkdir()
    (tmp_path / ".fux").mkdir()
    # CLAUDE.md §Build & test: a test that builds a repo by hand writes
    # `.fux/pii.toml`, or every verb refuses (SR-PII decision 17).
    (tmp_path / ".fux" / "pii.toml").write_text("", encoding="utf-8")
    (tmp_path / OUTPUT_NAME).write_text(specimen(), encoding="utf-8")
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "retry.md").write_text(
        "# Retry\n\nline three\nline four\n", encoding="utf-8"
    )
    write_index(
        tmp_path,
        [
            _rec("file:docs/retry.md", "Retry policy", "rollback",
                 phrases=["Rollback procedure"], mtime=1788330315),
            # No `mtime`: a document outside git history, which is what a corpus
            # copied OUT of its repository produces for every one of its files.
            _rec("file:docs/new.md", "New decision", "rollback", phrases=["Scope"]),
        ],
    )
    return tmp_path


# -- 1. the spelling the record documents -----------------------------------


def test_from_fux_import_open_resolves():
    from fux import open as fux_open
    from fux.api import open as api_open

    assert fux_open is api_open


def test_the_package_exports_nothing_that_writes():
    """SR-API: the read plane, and the same cut the Node reader makes.

    ⚠ Asserted on the package's OWN names, never on `hasattr` — importing
    `fux.setup` anywhere in the suite binds it as an attribute of `fux`, so a
    `hasattr` check here would pass or fail on test ordering.
    """
    from types import ModuleType

    import fux

    assert set(fux.__all__) == {"__version__", "open"}
    exported = {
        name for name, value in vars(fux).items()
        if not name.startswith("_") and not isinstance(value, ModuleType)
    }
    assert exported == {"open"}, f"fux exports more than the read surface: {exported}"


# -- 2. the two refusals ----------------------------------------------------


def test_open_outside_any_root_raises(tmp_path):
    from fux import open as fux_open

    with pytest.raises(FuxError, match="no fux root at or above"):
        fux_open(tmp_path)


def test_open_without_pii_rules_raises(tmp_path):
    from fux import open as fux_open

    (tmp_path / ".git").mkdir()
    with pytest.raises(FuxError, match="pii.toml is missing"):
        fux_open(tmp_path)


# -- 3. the gate is a stat ---------------------------------------------------


def test_the_warm_gate_does_not_import_the_decoders(repo, monkeypatch):
    """⚠ The regression this exists for shipped once and was measured, not guessed.

    `fux.ingest` drags in every decoder. On the path where `pii.toml` is
    PRESENT nothing needs it, so importing it there costs ~47 ms per call for
    nothing. Asserting on `sys.modules` catches a re-introduction that a timing
    assertion would only catch on a fast enough machine.
    """
    from fux import open as fux_open

    for name in [m for m in sys.modules if m.startswith("fux.ingest")]:
        monkeypatch.delitem(sys.modules, name, raising=False)
    fux_open(repo)
    assert not [m for m in sys.modules if m.startswith("fux.ingest")], (
        "fux.open() imported fux.ingest on the warm path — the gate must be a "
        "stat, with the import only where it is about to raise"
    )


# -- 4. the shapes, against the contract -------------------------------------


def _validate(payload: dict, shape: str) -> None:
    load_schema("fux.query", "output.schema.json").shape(shape).validate(
        payload, label=f"api {shape}",
        conditions={"band_requested": lambda _p: "confidence" in payload},
    )


def test_find_returns_results_that_validate(repo):
    from fux import open as fux_open

    results = fux_open(repo).find("rollback", top=5)
    assert results and all(r.id.startswith("file:") for r in results)
    for result in results:
        _validate(result.as_dict(), "ask_result")


def test_the_hit_carries_mtime_and_null_is_a_CLAIM(repo):
    """W-153 — the committed date reaches a caller.

    🔴 **The key is on every hit, always.** An absent key cannot be told from an
    older fux (the W-48 trap), so `None` is what *this document carries no
    committed date* looks like — and that is a whole corpus, every time somebody
    copies one out of its repository.

    **It exposes a fact and orders nothing:** `mtime` reaches the sort only
    through the declared tie-break, at an equal score.
    """
    from fux import open as fux_open

    by_loc = {r.loc: r for r in fux_open(repo).find("rollback", top=5)}
    assert by_loc["docs/retry.md"].mtime == 1788330315
    assert by_loc["docs/new.md"].mtime is None
    # Present in the serialized shape too, in BOTH states — the dict is the
    # `--json` payload exactly (SR-API decision 1).
    for loc in ("docs/retry.md", "docs/new.md"):
        assert "mtime" in by_loc[loc].as_dict()


def test_find_under_narrows_by_path(repo):
    from fux import open as fux_open

    index = fux_open(repo)
    assert index.find("rollback", top=5, under="docs")
    assert index.find("rollback", top=5, under="nowhere") == []


def test_ask_carries_the_band_by_default_and_validates(repo):
    """`band=True` here and `False` on the CLI, deliberately — SR-API.

    A caller in Python has already decided to read the object; the block is the
    part that says whether to trust it.
    """
    from fux import open as fux_open

    answer = fux_open(repo).ask("rollback")
    assert answer.confidence is not None
    payload = answer.as_dict()
    for row in payload["results"]:
        _validate(row, "ask_result")
    _validate(payload["confidence"], "confidence")

    quiet = fux_open(repo).ask("rollback", band=False)
    assert quiet.confidence is None
    # SR-CONFIDENCE decision 11: absent means NOT ASKED FOR, never a claim.
    assert "confidence" not in quiet.as_dict()


def test_ask_with_extra_arms_reports_that_it_fused(repo):
    from fux import open as fux_open

    answer = fux_open(repo).ask("rollback", queries=["retry"])
    assert answer.fused is True
    assert answer.as_dict()["fused"] is True
