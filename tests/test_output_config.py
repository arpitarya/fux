"""`.fux/output.toml` — the loader, the closed key set, and the precedence chain.

**What these tests guard is the boundary, not the parsing.** A rendering file
that can quietly change a ranking is the failure mode; every other assertion
here is in service of that one.
"""

from __future__ import annotations

import pytest

from fux.errors import FuxError
from fux.output_config import (
    BUILT_IN,
    DEFAULT_OUTPUT,
    OUTPUT_NAME,
    SCHEMA,
    OutputDefaults,
    load,
    specimen,
)


def write(root, body: str):
    (root / ".fux").mkdir(parents=True, exist_ok=True)
    (root / OUTPUT_NAME).write_text(body, encoding="utf-8")
    return root


# --------------------------------------------------------------------------
# absent / empty / disabled — the file is optional and must stay optional
# --------------------------------------------------------------------------


def test_absent_file_is_every_default(tmp_path):
    assert load(tmp_path) == DEFAULT_OUTPUT
    assert load(tmp_path).trivial


def test_empty_file_is_every_default(tmp_path):
    write(tmp_path, "")
    assert load(tmp_path).trivial


def test_all_commented_is_every_default(tmp_path):
    write(tmp_path, "# [ask]\n# top = 9\n")
    assert load(tmp_path).trivial


def test_disabled_does_not_read_the_file(tmp_path):
    write(tmp_path, "[ask]\ntop = 99\n")
    assert load(tmp_path, enabled=False).trivial


def test_disabled_does_not_even_parse_a_broken_file(tmp_path):
    # `--no-output-config` has to work when the file is what is wrong; that is
    # the entire point of the switch.
    write(tmp_path, "this is not toml at all [[[")
    assert load(tmp_path, enabled=False).trivial


# --------------------------------------------------------------------------
# the precedence chain — flag > [verb] > [defaults] > built-in
# --------------------------------------------------------------------------


def test_built_in_when_nothing_is_set(tmp_path):
    cfg = load(tmp_path)
    assert cfg.resolve("ask", "top") == 5
    assert cfg.resolve("ask", "band") is False
    assert cfg.resolve("path", "hops") == 2


def test_defaults_table_beats_built_in(tmp_path):
    write(tmp_path, "[defaults]\nband = true\n")
    assert load(tmp_path).resolve("ask", "band") is True


def test_verb_table_beats_defaults_table(tmp_path):
    write(tmp_path, "[defaults]\nband = true\n\n[find]\nband = false\n")
    cfg = load(tmp_path)
    assert cfg.resolve("ask", "band") is True
    assert cfg.resolve("find", "band") is False


def test_cli_value_beats_everything(tmp_path):
    write(tmp_path, "[defaults]\ntop = 50\n\n[ask]\ntop = 20\n")
    cfg = load(tmp_path)
    assert cfg.resolve("ask", "top") == 20
    assert cfg.resolve("ask", "top", cli_value=3) == 3


def test_none_means_the_flag_was_not_passed(tmp_path):
    # The whole reason a gated `store_true` must be declared `default=None`:
    # an explicit `--band` and an absent one are otherwise the same value.
    write(tmp_path, "[ask]\nband = true\n")
    cfg = load(tmp_path)
    assert cfg.resolve("ask", "band", cli_value=None) is True
    assert cfg.resolve("ask", "band", cli_value=False) is False


def test_defaults_reaches_a_verb_only_where_the_verb_declares_the_key(tmp_path):
    write(tmp_path, "[defaults]\nband = true\n")
    cfg = load(tmp_path)
    assert cfg.resolve("ask", "band") is True
    # `doctor` has no band concept, so asking for one is a caller error rather
    # than a silently-inherited True.
    with pytest.raises(FuxError, match="not an output key for `doctor`"):
        cfg.resolve("doctor", "band")


# --------------------------------------------------------------------------
# the closed key set — a typo must be loud
# --------------------------------------------------------------------------


def test_unknown_table_is_loud(tmp_path):
    write(tmp_path, "[asssk]\ntop = 3\n")
    with pytest.raises(FuxError, match="unknown table"):
        load(tmp_path)


def test_unknown_key_is_loud(tmp_path):
    write(tmp_path, "[ask]\ncolour = true\n")
    with pytest.raises(FuxError, match="unknown key `colour`"):
        load(tmp_path)


def test_a_key_on_the_wrong_verb_names_the_right_one(tmp_path):
    write(tmp_path, "[find]\nexplain = true\n")
    with pytest.raises(FuxError, match="it is a key of ask, not of `find`"):
        load(tmp_path)


def test_a_single_verb_key_is_refused_in_defaults(tmp_path):
    write(tmp_path, "[defaults]\nhops = 4\n")
    with pytest.raises(FuxError, match=r"belongs to one verb only \(path\)"):
        load(tmp_path)


def test_a_bare_known_key_names_the_section_it_belongs_in(tmp_path):
    # tomllib parses this as a top-level KEY. Reported as an unknown *table*
    # it sends a reader hunting for a section they never wrote.
    write(tmp_path, "band = true\n")
    with pytest.raises(FuxError, match=r"`band` is a key, not a table"):
        load(tmp_path)


def test_a_bare_unknown_key_says_so(tmp_path):
    write(tmp_path, "colour = true\n")
    with pytest.raises(FuxError, match="not a known key at all"):
        load(tmp_path)


def test_a_verb_name_used_as_a_scalar_is_loud(tmp_path):
    write(tmp_path, "ask = 5\n")
    with pytest.raises(FuxError, match="must be a table"):
        load(tmp_path)


def test_errors_are_collected_not_reported_one_at_a_time(tmp_path):
    write(tmp_path, "[ask]\ncolour = true\nshape = 2\nzoom = 9\n")
    with pytest.raises(FuxError) as exc:
        load(tmp_path)
    for key in ("colour", "shape", "zoom"):
        assert key in str(exc.value)


# --------------------------------------------------------------------------
# types — the bool/int trap is the one that would bite silently
# --------------------------------------------------------------------------


def test_top_true_is_refused_and_does_not_mean_one(tmp_path):
    # `isinstance(True, int)` is True in Python. Accepted, this would truncate
    # every result list to a single document and look like a ranking bug.
    write(tmp_path, "[ask]\ntop = true\n")
    with pytest.raises(FuxError, match="must be a whole number"):
        load(tmp_path)


def test_band_one_is_refused(tmp_path):
    write(tmp_path, "[ask]\nband = 1\n")
    with pytest.raises(FuxError, match="must be true or false"):
        load(tmp_path)


def test_top_zero_is_refused_as_broken_not_aggressive(tmp_path):
    write(tmp_path, "[ask]\ntop = 0\n")
    with pytest.raises(FuxError, match="at least 1"):
        load(tmp_path)


def test_top_float_is_refused(tmp_path):
    write(tmp_path, "[ask]\ntop = 5.5\n")
    with pytest.raises(FuxError, match="must be a whole number"):
        load(tmp_path)


def test_a_large_top_is_allowed_because_it_is_strong_not_broken(tmp_path):
    # Arpit's standing rule: refuse only what is broken or duplicates a tool.
    write(tmp_path, "[ask]\ntop = 500\n")
    assert load(tmp_path).resolve("ask", "top") == 500


# --------------------------------------------------------------------------
# refusals by name — each states its reason
# --------------------------------------------------------------------------


@pytest.mark.parametrize("key", ["no_tune", "tune", "fast", "scan", "no_progress", "no_output_config"])
def test_refused_keys_are_named_not_reported_as_unknown(tmp_path, key):
    write(tmp_path, f"[ask]\n{key} = true\n")
    with pytest.raises(FuxError) as exc:
        load(tmp_path)
    message = str(exc.value)
    assert f"`{key}` is refused" in message
    assert "unknown key" not in message


def test_no_tune_refusal_explains_the_loop(tmp_path):
    write(tmp_path, "[defaults]\nno_tune = true\n")
    with pytest.raises(FuxError, match=r"is it me or the config"):
        load(tmp_path)


def test_scan_refusal_names_bug_reproduction(tmp_path):
    write(tmp_path, "[ask]\nscan = true\n")
    with pytest.raises(FuxError, match="reproduced explicitly"):
        load(tmp_path)


# --------------------------------------------------------------------------
# hostile files — this one is committed, so it arrives from a pull
# --------------------------------------------------------------------------


def test_merge_conflict_markers_are_named(tmp_path):
    write(tmp_path, "[ask]\n<<<<<<< HEAD\ntop = 5\n=======\ntop = 9\n>>>>>>> branch\n")
    with pytest.raises(FuxError, match="merge conflict"):
        load(tmp_path)


def test_utf8_bom_is_stripped_not_diagnosed(tmp_path):
    (tmp_path / ".fux").mkdir(parents=True, exist_ok=True)
    (tmp_path / OUTPUT_NAME).write_bytes(b"\xef\xbb\xbf[ask]\ntop = 7\n")
    assert load(tmp_path).resolve("ask", "top") == 7


def test_invalid_toml_names_the_file(tmp_path):
    write(tmp_path, "[ask\ntop = 3\n")
    with pytest.raises(FuxError, match="invalid TOML"):
        load(tmp_path)


# --------------------------------------------------------------------------
# the contract between the schema, the built-ins, and the shipped specimen
# --------------------------------------------------------------------------


def test_every_schema_key_has_a_built_in():
    for verb, keys in SCHEMA.items():
        for key in keys:
            assert key in BUILT_IN, f"{verb}.{key} has no built-in default"


def test_every_built_in_is_reachable_from_some_verb():
    reachable = {k for keys in SCHEMA.values() for k in keys}
    assert set(BUILT_IN) == reachable


def test_mcp_has_no_json_key_because_an_mcp_result_is_always_json():
    assert "json" not in SCHEMA["mcp"]


def test_mcp_has_no_band_key_because_the_mcp_block_is_unconditional():
    # Found by BUILDING this: the first draft of ADR-OUTPUT put `band` here,
    # which would have let a config re-blind the one surface the record exists
    # to serve. ADR-CONFIDENCE decision 11 makes it unconditional over MCP.
    assert "band" not in SCHEMA["mcp"]


def test_mcp_band_is_refused_by_name_with_the_reason(tmp_path):
    write(tmp_path, "[mcp]\nband = false\n")
    with pytest.raises(FuxError, match="UNCONDITIONAL"):
        load(tmp_path)


def test_mcp_is_in_the_schema_at_all():
    # It is the one surface with no flags, so this table is its only knob.
    # If this row is ever dropped, MCP silently becomes unconfigurable again.
    assert SCHEMA["mcp"]


def test_the_specimen_parses_and_is_entirely_commented_out(tmp_path):
    write(tmp_path, specimen())
    assert load(tmp_path).trivial


def test_the_specimen_mentions_every_table(tmp_path):
    text = specimen()
    for verb in SCHEMA:
        assert f"[{verb}]" in text, f"the specimen never shows [{verb}]"


def test_the_specimen_uncommented_still_validates(tmp_path):
    # Every commented line must be a line that would actually LOAD. A specimen
    # carrying a key the loader rejects is worse than no specimen.
    body = "\n".join(
        line.lstrip("#") if line.startswith("#") and "=" in line else line
        for line in specimen().splitlines()
        if not line.startswith("# ")
    )
    load(write(tmp_path, body))


def test_the_specimen_warns_that_top_bounds_a_reported_signal():
    # The one honest boundary case in the whole file. If this warning is ever
    # dropped, `top` reads as pure presentation and it is not.
    assert "confidence.support" in specimen()


# --------------------------------------------------------------------------
# L3 — nothing on the maintenance path may read this file
# --------------------------------------------------------------------------


def test_the_module_imports_nothing_from_the_maintenance_path():
    import fux.output_config as mod
    from pathlib import Path as _P

    source = _P(mod.__file__).read_text(encoding="utf-8")
    body = "\n".join(
        line for line in source.splitlines() if line.startswith(("import ", "from "))
    )
    for banned in ("ingest", "derive", "maintain", "store"):
        assert banned not in body, f"output_config imports from {banned} — L3 fence"


def test_resolve_rejects_an_unknown_verb():
    with pytest.raises(FuxError, match="no output defaults are declared"):
        DEFAULT_OUTPUT.resolve("nosuchverb", "json")


def test_output_defaults_is_frozen():
    with pytest.raises(Exception):
        DEFAULT_OUTPUT.per_verb = {}  # type: ignore[misc]


def test_two_loads_of_the_same_file_are_equal(tmp_path):
    write(tmp_path, "[defaults]\nband = true\n\n[ask]\ntop = 9\n")
    assert load(tmp_path) == load(tmp_path)
    assert isinstance(load(tmp_path), OutputDefaults)


# --------------------------------------------------------------------------
# the CLI seam — found by RUNNING it, so it is gated (CLAUDE.md two strikes)
# --------------------------------------------------------------------------


def test_apply_output_defaults_resolves_against_a_real_repo(tmp_path, monkeypatch):
    """⚠ **This test exists because the first build shipped a broken import.**

    `cli._apply_output_defaults` imported `find_root` from `store.fuxdir`,
    where it does not live — it is in `config`. Every unit test passed, because
    they monkeypatch `fux.query.find_root` and never reach `cli`'s own import;
    the failure only appeared on `python -m fux ask` in a real repo, as an
    `ImportError` on **every single verb**.

    The guard is to exercise the seam with NO monkeypatching at all.
    """
    from fux.cli import _apply_output_defaults, build_parser

    (tmp_path / "fux.toml").write_text("[fux]\nversion = 1\n", encoding="utf-8")
    write(tmp_path, "[defaults]\nband = true\n\n[ask]\ntop = 3\n")
    monkeypatch.chdir(tmp_path)

    args = build_parser().parse_args(["ask", "rollback"])
    assert args.top is None and args.band is None, "argparse must hand over None"
    _apply_output_defaults(args)
    assert args.top == 3, "[ask] top"
    assert args.band is True, "[defaults] band"
    assert args.json is False, "unset key falls through to the built-in"


def test_apply_output_defaults_survives_outside_a_repo(tmp_path, monkeypatch):
    # `--help`, `--version` and a run from anywhere at all must not be broken
    # by a config file that may not exist.
    from fux.cli import _apply_output_defaults, build_parser

    monkeypatch.chdir(tmp_path)
    args = build_parser().parse_args(["ask", "rollback"])
    _apply_output_defaults(args)
    assert args.top == BUILT_IN["top"]
    assert args.band is False


def test_a_malformed_file_still_raises_through_the_cli_seam(tmp_path, monkeypatch):
    from fux.cli import _apply_output_defaults, build_parser

    (tmp_path / "fux.toml").write_text("[fux]\nversion = 1\n", encoding="utf-8")
    write(tmp_path, "[ask]\ntop = true\n")
    monkeypatch.chdir(tmp_path)

    args = build_parser().parse_args(["ask", "rollback"])
    with pytest.raises(FuxError, match="must be a whole number"):
        _apply_output_defaults(args)


def test_every_gated_flag_is_declared_default_none():
    """ADR-OUTPUT decision 10, and veto condition 4.

    ⚠ **The one defect in this feature that nothing else can see.** A gated
    `store_true` left at `default=False` makes `.fux/output.toml` silently
    never take effect for that key: the loader works, every other test passes,
    and the feature just does not exist. Assert it structurally.
    """
    from fux.cli import build_parser
    from fux.output_config import SCHEMA

    parser = build_parser()
    sub = [a for a in parser._subparsers._group_actions if a.dest == "command"][0]
    for verb, keys in SCHEMA.items():
        if verb not in sub.choices:
            continue  # `mcp` has no flags at all — that is the point of it
        for action in sub.choices[verb]._actions:
            if action.dest in keys:
                assert action.default is None, (
                    f"`fux {verb} --{action.dest.replace('_', '-')}` is declared "
                    f"default={action.default!r}; ADR-OUTPUT decision 10 requires "
                    "default=None, or the config can never take effect"
                )
