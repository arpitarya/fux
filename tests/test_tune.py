"""`.fux/tune.toml` — the loader, the closed key set, and the two refusals.

[SR-TUNE](../records/0135_tuning.md) is the record. The boundary rule it
turns on — *changing any key here leaves `.fux/index/` byte-identical* — has
its own module, `tests/test_tune_boundary.py`, because it needs a built corpus
and these do not.
"""

from __future__ import annotations

from l12_fixtures import template_tune, tune_text, write_config
import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

from fux.errors import FuxError
from fux.tune import TUNE_NAME, Tune, load, specimen, template_text

ENGINE = Path(__file__).resolve().parents[1]


def _write(root, text: str):
    path = root / TUNE_NAME
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return root


def load_on(root) -> Tune:
    return load(root, enabled=True)


# -- absent, missing, and off (L12) -------------------------------------------


def test_no_file_is_an_error_that_names_the_file(tmp_path):
    """L12 decision 3: fux holds no copy of these values, so absent is loud."""
    with pytest.raises(FuxError, match=r"\.fux[/\\]tune\.toml is missing") as exc:
        load_on(tmp_path)
    assert "fux doctor --fix" in str(exc.value)


def test_a_missing_key_is_an_error_that_names_the_table_and_the_key(tmp_path):
    text = "\n".join(
        line for line in template_text().splitlines() if not line.startswith("mined_weight")
    )
    _write(tmp_path, text)
    with pytest.raises(FuxError, match=r"\[ranking\] mined_weight is missing") as exc:
        load_on(tmp_path)
    assert "fux doctor --fix" in str(exc.value), "a missing key names its remedy"


def test_an_empty_file_names_every_missing_key(tmp_path):
    _write(tmp_path, "")
    with pytest.raises(FuxError, match=r"\[bm25f\] k1 is missing") as exc:
        load_on(tmp_path)
    assert "more" in str(exc.value), "every key is missing, so the list is capped"


def test_the_template_loads_and_is_what_setup_writes(tmp_path):
    """What `fux setup` writes parses back to the template's own `Tune`."""
    _write(tmp_path, specimen())
    assert load_on(tmp_path) == template_tune()
    assert specimen() == template_text()


def test_no_tune_reads_the_template_and_never_the_file(tmp_path):
    """`--no-tune` is the "is it me or the config?" switch (decision 11).

    It must not merely ignore the values — a file that cannot be parsed must
    not error either, or the flag would be useless in exactly the situation
    that makes someone reach for it. Since L12 it reads the template `fux setup`
    writes, never a value in code (L12 decision 7).
    """
    _write(tmp_path, "this is not TOML at all {{{")
    assert load(tmp_path, enabled=False) == template_tune()
    with pytest.raises(FuxError):
        load_on(tmp_path)


# -- the closed key set -------------------------------------------------------


def test_an_unknown_table_is_a_loud_error(tmp_path):
    _write(tmp_path, "[rankings]\narchived_weight = 0.5\n")
    with pytest.raises(FuxError, match="unknown table"):
        load_on(tmp_path)


def test_an_unknown_key_is_a_loud_error_and_names_the_known_ones(tmp_path):
    _write(tmp_path, "[bm25f]\nk2 = 1.4\n")
    with pytest.raises(FuxError, match=r"unknown key.*k2") as exc:
        load_on(tmp_path)
    assert "k1" in str(exc.value), "the message must name what WAS available"


def test_a_bare_key_outside_a_table_is_refused(tmp_path):
    _write(tmp_path, "priority = 2\n")
    with pytest.raises(FuxError, match="must be a table"):
        load_on(tmp_path)


def test_priority_is_the_one_open_table(tmp_path):
    """Its keys are the consumer's own source entries; fux cannot know them."""
    _write(tmp_path, tune_text(priority={"anything/at/all": 2.0}))
    assert load_on(tmp_path).priority == (("anything/at/all", 2.0),)


# -- validation ---------------------------------------------------------------


def test_k1_must_be_positive(tmp_path):
    _write(tmp_path, tune_text(bm25f={"k1": 0}))
    with pytest.raises(FuxError, match="k1 must be greater than zero"):
        load_on(tmp_path)


def test_b_is_a_fraction_and_the_message_says_what_the_ends_mean(tmp_path):
    _write(tmp_path, tune_text(bm25f={"b": 1.5}))
    with pytest.raises(FuxError, match="0 turns the effect off") as exc:
        load_on(tmp_path)
    assert "between 0 and 1" in str(exc.value)


def test_a_field_weight_of_zero_is_legal_and_means_ignore_the_field(tmp_path):
    """Distinct from a `[priority]` zero, which is exclusion and is refused."""
    _write(tmp_path, tune_text(bm25f={"heading": 0}))
    assert load_on(tmp_path).field_weights[1] == 0.0


def test_a_non_integer_field_weight_is_legal(tmp_path):
    """The record refused this, on a premise W-76 Phase 1 removed.

    Decision 9a called a fractional `heading` weight an error because it
    "breaks the accelerator's u32 block maximum". The block extrema are stored
    per field and RAW since W-76 Phase 1, and `block_bound` recombines them in
    float at query time, so nothing integral is stored any more. Amended in the
    record rather than carried as folklore.
    """
    _write(tmp_path, tune_text(bm25f={"heading": 2.5}))
    assert load_on(tmp_path).field_weights[1] == 2.5


def test_min_passage_must_be_below_max_passage(tmp_path):
    _write(tmp_path, tune_text(refer={"min_passage_bytes": 5000, "max_passage_bytes": 100}))
    with pytest.raises(FuxError, match="must be smaller than"):
        load_on(tmp_path)


def test_a_bool_is_not_a_number(tmp_path):
    """`bool` is an `int` subclass in Python — `true` is not a weight."""
    _write(tmp_path, tune_text(ranking={"rerank_weight": True}))
    with pytest.raises(FuxError, match="must be a number"):
        load_on(tmp_path)


def test_semantic_errors_are_reported_together(tmp_path):
    """One at a time turns a hand-edited file into a guessing game (decision 10b)."""
    _write(tmp_path, tune_text(bm25f={"k1": -1, "b": 9}, graph={"iterations": 0}))
    with pytest.raises(FuxError) as exc:
        load_on(tmp_path)
    message = str(exc.value)
    assert "k1" in message and "b" in message and "iterations" in message


def test_the_error_list_is_capped(tmp_path):
    """An unbounded list buries the first error, which is usually the cause."""
    _write(tmp_path, tune_text(priority={f"entry-{i}": -1 for i in range(25)}))
    with pytest.raises(FuxError, match="and 15 more"):
        load_on(tmp_path)


# -- the two refusals (decision 9a) -------------------------------------------


def test_a_negative_priority_is_refused_as_broken_not_as_aggressive(tmp_path):
    _write(tmp_path, tune_text(priority={"docs/": -2.0}))
    with pytest.raises(FuxError, match="inverts the ordering"):
        load_on(tmp_path)


def test_a_zero_priority_is_refused_and_names_the_exclusion_prefix(tmp_path):
    """Zero means exclude, and exclusion already has exactly one home."""
    _write(tmp_path, tune_text(priority={"vendor/": 0}))
    with pytest.raises(FuxError, match=r"prefix the entry with `!`"):
        load_on(tmp_path)


def test_a_large_priority_is_allowed_and_not_clamped(tmp_path):
    """Both directions are the consumer's call; fux states the cost, not a limit."""
    _write(tmp_path, tune_text(priority={"docs/": 50.0, "vendor/": 0.01}))
    tune = load_on(tmp_path)
    assert dict(tune.priority) == {"docs/": 50.0, "vendor/": 0.01}


# -- the two built-in failure modes (decision 10c) ----------------------------


def test_a_merge_conflict_gets_its_own_message(tmp_path):
    _write(
        tmp_path,
        "[bm25f]\n<<<<<<< HEAD\nk1 = 1.2\n=======\nk1 = 1.5\n>>>>>>> theirs\n",
    )
    with pytest.raises(FuxError, match="unresolved merge conflict"):
        load_on(tmp_path)


def test_a_utf8_bom_is_stripped_rather_than_diagnosed(tmp_path):
    """Windows editors write them; Windows-first fleets are in the litmus."""
    path = tmp_path / TUNE_NAME
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"\xef\xbb\xbf" + tune_text(bm25f={"k1": 1.5}).encode("utf-8"))
    assert load_on(tmp_path).k1 == 1.5


def test_invalid_toml_says_so(tmp_path):
    _write(tmp_path, "[bm25f\nk1 = 1.2\n")
    with pytest.raises(FuxError, match="invalid TOML"):
        load_on(tmp_path)


# -- resolution ---------------------------------------------------------------


def test_scoring_carries_k1_b_and_the_weights_as_one_object(tmp_path):
    _write(tmp_path, tune_text(bm25f={"k1": 1.5, "b": 0.4, "title": 9}))
    scoring = load_on(tmp_path).scoring
    assert (scoring.k1, scoring.b) == (1.5, 0.4)
    assert scoring.weights[2] == 9.0


def test_priority_is_sorted_longest_key_first(tmp_path):
    """Longest-match-wins is implemented by ordering, so the order is the contract."""
    _write(tmp_path, tune_text(priority={"a/": 2.0, "a/b/c/": 4.0, "a/b/": 3.0}))
    assert [entry for entry, _ in load_on(tmp_path).priority] == ["a/b/c/", "a/b/", "a/"]


def test_changing_one_key_changes_exactly_that_key(tmp_path):
    """Edit a line and exactly that line changes."""
    _write(tmp_path, tune_text(bm25f={"k1": 1.9}))
    tune = load_on(tmp_path)
    assert tune.k1 == 1.9
    assert tune.b == template_tune().b
    assert tune.field_weights == template_tune().field_weights
    assert tune.budget == template_tune().budget


def test_tune_is_frozen(tmp_path):
    """Two code paths must never be handed a policy that drifted between them."""
    with pytest.raises(Exception):
        template_tune().k1 = 2.0  # type: ignore[misc]


def test_every_specimen_table_is_in_the_schema():
    """The file `fux setup` writes cannot contain a table the loader refuses."""
    from fux.tune import _SCHEMA

    tables = [
        line.strip().strip("[]").split("]")[0]
        for line in specimen().splitlines()
        if line.startswith("[")
    ]
    assert tables, "the specimen must actually declare tables"
    assert set(tables) == set(_SCHEMA), (set(tables), set(_SCHEMA))


def test_every_schema_key_appears_in_the_specimen():
    """A key nobody can discover is a key nobody uses (decision 4).

    ⚠ **This matched `#key` only until 2026-08-27**, because the specimen used
    to be nothing but comments. Arpit's ruling that day made every tunable a
    LIVE line (`specimen()`'s own docstring records it), so the old matcher
    demanded a comment marker on keys that are now real declarations and went
    red on all seventeen of them -- **the test failed for the reason the change
    was made.**

    What discoverability actually needs is that the key is *declared*, live or
    commented (`[priority]` stays commented on purpose, and that is not an
    inconsistency -- its keys are the consumer's own source entries, not
    tunables with defaults). So the check is now on a declaration, either way.
    """
    from fux.tune import _SCHEMA

    text = specimen()
    missing = [
        f"[{table}] {key}"
        for table, keys in _SCHEMA.items()
        for key in keys
        if not re.search(rf"(?m)^#?\s*{re.escape(key)}\s*=", text)
    ]
    assert not missing, missing


def test_a_retired_dense_table_names_its_removal_rather_than_reading_as_a_typo(tmp_path):
    """`[dense]` went with the model on 2026-08-25.

    A consumer who configured the lane has this table in their file. The closed
    key set would call it an unknown table, which reads as a typo; they need to
    be told it was removed, and that their ranking has not moved because `mode`
    defaulted to `off` anyway.
    """
    _write(tmp_path, '[dense]\nmode = "always"\n')
    with pytest.raises(FuxError, match="REMOVED on 2026-08-25"):
        load_on(tmp_path)


def test_a_removed_ranking_key_names_its_removal_rather_than_reading_as_a_typo(tmp_path):
    """🔴 `superseded_weight` went on 2026-09-13 (W-151), and `fux setup` had
    WRITTEN it into every `.fux/tune.toml` it ever created.

    So the generic *"unknown key"* would send a consumer hunting for a typo in a
    line fux typed for them. The error has to name the removal, its date, and
    that their ranking has not moved — it shipped at `1.0`.
    """
    _write(tmp_path, "[ranking]\nsuperseded_weight = 0.5\n")
    with pytest.raises(FuxError, match="REMOVED on 2026-09-13"):
        load_on(tmp_path)


def test_a_removed_key_is_named_even_beside_a_genuine_typo(tmp_path):
    """The removal is the finding; an unknown key beside it must not mask it."""
    _write(tmp_path, "[ranking]\nsuperseded_weight = 0.5\nnot_a_key = 1\n")
    with pytest.raises(FuxError, match="REMOVED on 2026-09-13"):
        load_on(tmp_path)


def test_rm3_weight_is_accepted_again_by_both_readers_and_ships_off(tmp_path):
    """W-237: RM3 returned behind a `grounded`-only gate (Arpit, 2026-09-30,
    R1 · G3), so `rm3_weight` left `_REMOVED_KEYS` and is a live key again
    (SR-TUNE decision 18). It ships at `0.0`, and both readers read the same
    value from the same file — one refusing a line the other accepts is the
    asymmetry the differential law forbids.
    """
    from fux.tune import _REMOVED_KEYS

    assert ("ranking", "rm3_weight") not in _REMOVED_KEYS
    assert template_tune().rm3_weight == 0.0
    assert re.search(r"^rm3_weight\s*=\s*0\.0$", specimen(), re.M)
    _write(tmp_path, tune_text(ranking={"rm3_weight": 0.3}))
    assert load_on(tmp_path).rm3_weight == 0.3

    if shutil.which("node") is None:
        pytest.skip("node is not on PATH")
    script = (
        f"import {{ loadTune }} from {json.dumps((ENGINE / 'node/src/config/tune.mjs').as_uri())};"
        f"console.log(loadTune({json.dumps(str(tmp_path))}, {{ enabled: true }}).rm3Weight);"
    )
    out = subprocess.run(["node", "--input-type=module", "-e", script], capture_output=True, text=True)
    assert out.stdout.strip() == "0.3", out.stdout + out.stderr


def test_a_removed_key_is_gone_from_the_closed_key_set(tmp_path):
    """Schema and refusal table move together, or the removal is a trap."""
    from fux.tune import _REMOVED_KEYS, _SCHEMA

    for table, key in _REMOVED_KEYS:
        assert key not in _SCHEMA[table], f"{table}.{key} is both removed and live"


def test_a_tune_has_no_default_to_construct_from(tmp_path):
    """L12: every field is read from a file; the dataclass supplies none."""
    with pytest.raises(TypeError):
        Tune()  # type: ignore[call-arg]


def test_a_confidence_floor_must_be_a_fraction_and_the_message_says_why(tmp_path):
    """Both floors gate a value already clamped to [0,1]; outside it they are
    either dead (>1 for separation is unreachable) or meaningless."""
    _write(tmp_path, tune_text(confidence={"separation_floor": 1.4}))
    with pytest.raises(FuxError) as e:
        load_on(tmp_path)
    assert "separation_floor" in str(e.value)
    assert "between 0 and 1" in str(e.value)


def test_both_confidence_floors_load_and_neither_is_clamped(tmp_path):
    """The standing rule on knobs: refuse what is broken, state the cost of
    what is merely strong. `0.0` turns the `weak` band off and `1.0` makes the
    doc-coverage gate structural — both legal, both loud in the specimen."""
    _write(tmp_path, tune_text(confidence={"separation_floor": 0.0, "doc_coverage_floor": 1.0}))
    tune = load_on(tmp_path)
    assert tune.separation_floor == 0.0
    assert tune.doc_coverage_floor == 1.0


def test_the_template_ships_the_confidence_floors_its_comment_describes(tmp_path):
    """0.1 provisional (R10), 0.0 = the clause is off — the measured ruling."""
    tune = template_tune()
    assert tune.separation_floor == 0.1
    assert tune.doc_coverage_floor == 0.0


# -- [index]: the two keys that DO change the index (2026-09-11) ---------------


def test_index_limits_refuse_when_there_is_no_file(tmp_path):
    from fux.tune import index_limits

    with pytest.raises(FuxError, match=r"tune\.toml is missing"):
        index_limits(tmp_path)


def test_the_template_ships_the_measured_index_limits():
    assert "max_phrases    = 32" in template_text()
    assert "max_table_rows = 20000" in template_text()


def test_index_limits_are_read_from_the_index_table(tmp_path):
    from fux.tune import index_limits

    _write(tmp_path, tune_text(index={"max_phrases": 5, "max_table_rows": 250}))
    limits = index_limits(tmp_path)
    assert (limits.max_phrases, limits.max_table_rows) == (5, 250)


@pytest.mark.parametrize("key", ["max_phrases", "max_table_rows"])
@pytest.mark.parametrize("bad", ["0", "-1", '"all"', "true", "12.5"])
def test_a_nonsense_index_limit_refuses_on_both_readers(tmp_path, key, bad):
    """`fux ingest` and `fux ask` share one validator, so they cannot disagree."""
    from fux.tune import index_limits

    _write(tmp_path, tune_text(index={key: _raw(bad)}))
    with pytest.raises(FuxError, match=key):
        index_limits(tmp_path)
    with pytest.raises(FuxError, match=key):
        load_on(tmp_path)


def test_ingest_never_fails_on_a_bad_ranking_knob(tmp_path):
    """`index_limits` reads `[index]` alone — a typo elsewhere is `ask`'s to report."""
    from fux.tune import index_limits

    _write(tmp_path, tune_text(bm25f={"k1": -4}, index={"max_phrases": 7}))
    assert index_limits(tmp_path).max_phrases == 7
    with pytest.raises(FuxError, match="k1"):
        load_on(tmp_path)


def test_an_unknown_index_key_is_a_loud_error(tmp_path):
    from fux.tune import index_limits

    _write(tmp_path, "[index]\nmax_phrase = 7\n")
    with pytest.raises(FuxError, match="max_phrase"):
        index_limits(tmp_path)


def test_no_tune_does_not_reach_the_index_limits(tmp_path):
    """The index was built under these; `--no-tune` cannot un-build it."""
    from fux.tune import IndexLimits, index_limits

    _write(tmp_path, tune_text(index={"max_phrases": 7}))
    assert load(tmp_path, enabled=False) == template_tune()
    assert index_limits(tmp_path).max_phrases == 7
    assert not any(f in Tune.__dataclass_fields__ for f in IndexLimits.__dataclass_fields__)


def test_a_decoder_reads_the_configured_row_limit(tmp_path):
    """`decode/_limits.py`: a two-name decoder seeing committed config. The
    csv decoder also reads `[limits.csv]` from `.fux/formats.toml`, so the repo
    gets the rest of its config as `fux setup` writes it (W-225 stage 4a)."""
    from fux.decode import decode

    _write(tmp_path, tune_text(index={"max_table_rows": 3}))
    write_config(tmp_path)
    rows = b"col\n" + b"".join(b"value %d\n" % i for i in range(50))
    out = decode(rows, "a.csv", tmp_path)
    assert out.count("\n| value ") == 3
    assert "table truncated" in out


def test_the_row_limit_is_not_leaked_between_documents(tmp_path):
    from fux.decode import decode
    from fux.decode._limits import max_table_rows

    _write(tmp_path, tune_text(index={"max_table_rows": 3}))
    write_config(tmp_path)
    decode(b"col\nv1\nv2\nv3\nv4\nv5\n", "a.csv", tmp_path)
    with pytest.raises(FuxError, match="no repository in context"):
        max_table_rows()  # unbound again, and there is no default to fall back to


def _raw(text: str):
    """A TOML value spelled verbatim (`12.5`, `"all"`), parsed for `tune_text`."""
    import tomllib

    return tomllib.loads(f"v = {text}")["v"]
