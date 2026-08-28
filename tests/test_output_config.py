"""`.fux/output.toml` — three roots, one precedence chain, no silent fallback.

**What these tests guard is the boundary, not the parsing.** A rendering file
that can quietly change a ranking is the failure mode; every other assertion
here is in service of that one. Since 2026-08-28 (Arpit) there is a second
failure mode this file equally guards against: a key the file never set
silently returning a value nobody chose. **A file in effect must either say
what it wants, or the caller must be told it did not** — that is the
behavioural flip this whole file tests.
"""

from __future__ import annotations

import pytest

from fux.errors import FuxError
from fux.output_config import (
    BUILT_IN,
    CLI_VERBS,
    DEFAULT_OUTPUT,
    MCP_KEYS,
    OUTPUT_NAME,
    OutputDefaults,
    load,
    specimen,
)


def write(root, body: str):
    (root / ".fux").mkdir(parents=True, exist_ok=True)
    (root / OUTPUT_NAME).write_text(body, encoding="utf-8")
    return root


# --------------------------------------------------------------------------
# absent / empty / disabled
# --------------------------------------------------------------------------


def test_absent_file_raises_and_names_the_fix(tmp_path):
    with pytest.raises(FuxError, match="fux setup"):
        load(tmp_path)


def test_empty_file_loads_but_every_key_still_errors(tmp_path):
    write(tmp_path, "")
    cfg = load(tmp_path)
    assert not cfg.bypass
    with pytest.raises(FuxError, match="does not set `top`"):
        cfg.resolve("ask", "top", as_json=False)


def test_all_commented_is_the_same_as_empty(tmp_path):
    write(tmp_path, "# [cli]\n# top = 9\n")
    cfg = load(tmp_path)
    with pytest.raises(FuxError, match="does not set `top`"):
        cfg.resolve("ask", "top", as_json=False)


def test_disabled_does_not_read_the_file_and_never_raises(tmp_path):
    write(tmp_path, "not even valid toml [[[")
    cfg = load(tmp_path, enabled=False)
    assert cfg.bypass
    assert cfg.resolve("ask", "top") == BUILT_IN["top"]


def test_disabled_does_not_even_parse_a_broken_file(tmp_path):
    # `--no-output-config` has to work when the file is what is wrong; that is
    # the entire point of the switch.
    write(tmp_path, "this is not toml at all [[[")
    assert load(tmp_path, enabled=False).bypass


# --------------------------------------------------------------------------
# the precedence chain — flag > json-verb > json-shared > cli-verb > cli >
# bypass > error
# --------------------------------------------------------------------------


def _full_body() -> str:
    return (
        "[cli]\nband = true\ntop = 3\n\n"
        "[cli.ask]\nexplain = true\n\n"
        "[cli.path]\nhops = 4\n\n"
        "[cli.answer]\nno_refer = true\njournal = true\n\n"
        "[cli.json]\nenabled = false\n\n"
        "[mcp]\ntop = 9\n"
    )


def test_cli_shared_resolves_for_every_verb_that_declares_it(tmp_path):
    cfg = load(write(tmp_path, _full_body()))
    assert cfg.resolve("ask", "band", as_json=False) is True
    assert cfg.resolve("find", "band", as_json=False) is True
    assert cfg.resolve("ask", "top", as_json=False) == 3


def test_verb_subtable_beats_shared_table(tmp_path):
    write(tmp_path, "[cli]\nband = true\n\n[cli.find]\nband = false\n")
    cfg = load(tmp_path)
    assert cfg.resolve("ask", "band", as_json=False) is True
    assert cfg.resolve("find", "band", as_json=False) is False


def test_cli_flag_beats_everything(tmp_path):
    cfg = load(write(tmp_path, _full_body()))
    assert cfg.resolve("ask", "top", cli_value=3, as_json=False) == 3
    assert cfg.resolve("ask", "top", cli_value=77, as_json=False) == 77


def test_none_means_the_flag_was_not_passed(tmp_path):
    write(tmp_path, "[cli]\nband = true\n\n[cli.json]\nenabled = false\n")
    cfg = load(tmp_path)
    assert cfg.resolve("ask", "band", cli_value=None, as_json=False) is True
    assert cfg.resolve("ask", "band", cli_value=False, as_json=False) is False


def test_shared_table_reaches_a_verb_only_where_it_declares_the_key(tmp_path):
    write(tmp_path, "[cli]\nband = true\n\n[cli.json]\nenabled = false\n")
    cfg = load(tmp_path)
    assert cfg.resolve("ask", "band", as_json=False) is True
    with pytest.raises(FuxError, match="not an output key for `doctor`"):
        cfg.resolve("doctor", "band", as_json=False)


def test_json_branch_still_inherits_cli_shared_and_verb_tables(tmp_path):
    # decision 3: `[cli.json]` DOES inherit from `[cli]` — only `enabled`
    # itself does not fall back to `[cli]` (there is no `[cli] json` at all).
    write(tmp_path, "[cli]\nband = true\ntop = 9\n\n[cli.ask]\nexplain = true\n\n[cli.json]\nenabled = true\n")
    cfg = load(tmp_path)
    assert cfg.resolve("ask", "band", as_json=True) is True
    assert cfg.resolve("ask", "top", as_json=True) == 9
    assert cfg.resolve("ask", "explain", as_json=True) is True


def test_json_verb_beats_json_shared_beats_cli(tmp_path):
    write(
        tmp_path,
        "[cli]\ntop = 5\n\n[cli.json]\ntop = 7\n\n[cli.json.ask]\ntop = 9\n",
    )
    cfg = load(tmp_path)
    assert cfg.resolve("ask", "top", as_json=True) == 9
    assert cfg.resolve("find", "top", as_json=True) == 7
    assert cfg.resolve("ask", "top", as_json=False) == 5


def test_json_off_never_consults_the_json_tables(tmp_path):
    write(tmp_path, "[cli]\ntop = 5\n\n[cli.json]\ntop = 999\n")
    cfg = load(tmp_path)
    assert cfg.resolve("ask", "top", as_json=False) == 5


# --------------------------------------------------------------------------
# `resolve_json` — the first pass
# --------------------------------------------------------------------------


def test_resolve_json_flag_beats_everything(tmp_path):
    write(tmp_path, "[cli.json]\nenabled = false\n")
    cfg = load(tmp_path)
    assert cfg.resolve_json("ask", True) is True
    assert cfg.resolve_json("ask", False) is False


def test_resolve_json_enabled_turns_json_on_globally(tmp_path):
    write(tmp_path, "[cli.json]\nenabled = true\n")
    assert load(tmp_path).resolve_json("ask") is True


def test_resolve_json_per_verb_overrides_global(tmp_path):
    write(tmp_path, "[cli.json]\nenabled = false\n\n[cli.json.find]\nenabled = true\n")
    cfg = load(tmp_path)
    assert cfg.resolve_json("ask") is False
    assert cfg.resolve_json("find") is True


def test_resolve_json_raises_when_unset(tmp_path):
    write(tmp_path, "[cli]\nband = true\n")
    with pytest.raises(FuxError, match="does not set `enabled`"):
        load(tmp_path).resolve_json("ask")


def test_resolve_json_rejects_an_unknown_verb(tmp_path):
    write(tmp_path, "[cli.json]\nenabled = false\n")
    with pytest.raises(FuxError, match="no output defaults are declared"):
        load(tmp_path).resolve_json("nosuchverb")


# --------------------------------------------------------------------------
# the closed key set — a typo must be loud
# --------------------------------------------------------------------------


def test_unknown_table_is_loud(tmp_path):
    write(tmp_path, "[asssk]\ntop = 3\n")
    with pytest.raises(FuxError, match="unknown table"):
        load(tmp_path)


def test_unknown_verb_subtable_is_loud(tmp_path):
    write(tmp_path, "[cli.asssk]\ntop = 3\n")
    with pytest.raises(FuxError, match="not a known verb"):
        load(tmp_path)


def test_unknown_key_is_loud(tmp_path):
    write(tmp_path, "[cli.ask]\ncolour = true\n")
    with pytest.raises(FuxError, match="unknown key `colour`"):
        load(tmp_path)


def test_a_key_on_the_wrong_verb_names_the_right_one(tmp_path):
    write(tmp_path, "[cli.find]\nexplain = true\n")
    with pytest.raises(FuxError, match="is a key of ask, not of `find`"):
        load(tmp_path)


def test_a_single_verb_key_is_refused_at_the_shared_level(tmp_path):
    write(tmp_path, "[cli]\nhops = 4\n")
    with pytest.raises(FuxError, match=r"belongs to one verb only \(path\)"):
        load(tmp_path)


def test_a_bare_known_key_names_the_table_it_belongs_in(tmp_path):
    # tomllib parses this as a top-level KEY. Reported as an unknown *table*
    # it sends a reader hunting for a section they never wrote.
    write(tmp_path, "band = true\n")
    with pytest.raises(FuxError, match=r"`band` is a key, not a table"):
        load(tmp_path)


def test_a_bare_unknown_key_says_so(tmp_path):
    write(tmp_path, "colour = true\n")
    with pytest.raises(FuxError, match="not a known key at all"):
        load(tmp_path)


def test_a_root_name_used_as_a_scalar_is_loud(tmp_path):
    write(tmp_path, "cli = 5\n")
    with pytest.raises(FuxError, match="must be a table"):
        load(tmp_path)


def test_errors_are_collected_not_reported_one_at_a_time(tmp_path):
    write(tmp_path, "[cli.ask]\ncolour = true\nshape = 2\nzoom = 9\n")
    with pytest.raises(FuxError) as exc:
        load(tmp_path)
    for key in ("colour", "shape", "zoom"):
        assert key in str(exc.value)


# --------------------------------------------------------------------------
# the old flat layout — named, not shrugged at
# --------------------------------------------------------------------------


def test_old_defaults_table_is_named_as_the_old_layout(tmp_path):
    write(tmp_path, "[defaults]\nband = true\n")
    with pytest.raises(FuxError, match="old layout"):
        load(tmp_path)


def test_old_bare_verb_table_is_named_as_the_old_layout(tmp_path):
    write(tmp_path, "[ask]\ntop = 5\n")
    with pytest.raises(FuxError, match=r"\[ask\] at the top level is the old layout"):
        load(tmp_path)


# --------------------------------------------------------------------------
# types — the bool/int trap is the one that would bite silently
# --------------------------------------------------------------------------


def test_top_true_is_refused_and_does_not_mean_one(tmp_path):
    write(tmp_path, "[cli]\ntop = true\n")
    with pytest.raises(FuxError, match="must be a whole number"):
        load(tmp_path)


def test_band_one_is_refused(tmp_path):
    write(tmp_path, "[cli.ask]\nband = 1\n")
    with pytest.raises(FuxError, match="must be true or false"):
        load(tmp_path)


def test_top_zero_is_refused_as_broken_not_aggressive(tmp_path):
    write(tmp_path, "[cli]\ntop = 0\n")
    with pytest.raises(FuxError, match="at least 1"):
        load(tmp_path)


def test_top_float_is_refused(tmp_path):
    write(tmp_path, "[cli]\ntop = 5.5\n")
    with pytest.raises(FuxError, match="must be a whole number"):
        load(tmp_path)


def test_a_large_top_is_allowed_because_it_is_strong_not_broken(tmp_path):
    write(tmp_path, "[cli]\ntop = 500\n\n[cli.json]\nenabled = false\n")
    assert load(tmp_path).resolve("ask", "top", as_json=False) == 500


def test_enabled_wrong_type_is_refused(tmp_path):
    write(tmp_path, "[cli.json]\nenabled = 1\n")
    with pytest.raises(FuxError, match="must be true or false"):
        load(tmp_path)


def test_enabled_outside_json_is_refused(tmp_path):
    write(tmp_path, "[cli]\nenabled = true\n")
    with pytest.raises(FuxError, match="only applies inside `\\[cli.json\\]`"):
        load(tmp_path)


# --------------------------------------------------------------------------
# refusals by name — each states its reason
# --------------------------------------------------------------------------


@pytest.mark.parametrize("key", ["no_tune", "tune", "fast", "scan", "no_progress", "no_output_config"])
def test_refused_keys_are_named_not_reported_as_unknown(tmp_path, key):
    write(tmp_path, f"[cli.ask]\n{key} = true\n")
    with pytest.raises(FuxError) as exc:
        load(tmp_path)
    message = str(exc.value)
    assert f"`{key}` is refused" in message
    assert "unknown key" not in message


def test_json_key_is_refused_and_explains_the_rename(tmp_path):
    write(tmp_path, "[cli]\njson = true\n")
    with pytest.raises(FuxError, match="is spelled `enabled`"):
        load(tmp_path)


def test_no_tune_refusal_explains_the_loop(tmp_path):
    write(tmp_path, "[cli]\nno_tune = true\n")
    with pytest.raises(FuxError, match=r"is it me or the config"):
        load(tmp_path)


def test_scan_refusal_names_bug_reproduction(tmp_path):
    write(tmp_path, "[cli.ask]\nscan = true\n")
    with pytest.raises(FuxError, match="reproduced explicitly"):
        load(tmp_path)


def test_mcp_band_is_refused_by_name_with_the_reason(tmp_path):
    write(tmp_path, "[mcp]\nband = false\n")
    with pytest.raises(FuxError, match="UNCONDITIONAL"):
        load(tmp_path)


def test_mcp_json_is_refused_by_name(tmp_path):
    write(tmp_path, "[mcp]\njson = true\n")
    with pytest.raises(FuxError, match="always JSON"):
        load(tmp_path)


# --------------------------------------------------------------------------
# hostile files — this one is committed, so it arrives from a pull
# --------------------------------------------------------------------------


def test_merge_conflict_markers_are_named(tmp_path):
    write(tmp_path, "[cli]\n<<<<<<< HEAD\ntop = 5\n=======\ntop = 9\n>>>>>>> branch\n")
    with pytest.raises(FuxError, match="merge conflict"):
        load(tmp_path)


def test_utf8_bom_is_stripped_not_diagnosed(tmp_path):
    (tmp_path / ".fux").mkdir(parents=True, exist_ok=True)
    (tmp_path / OUTPUT_NAME).write_bytes(b"\xef\xbb\xbf[cli]\ntop = 7\n")
    assert load(tmp_path).resolve("ask", "top", as_json=False) == 7


def test_invalid_toml_names_the_file(tmp_path):
    write(tmp_path, "[cli\ntop = 3\n")
    with pytest.raises(FuxError, match="invalid TOML"):
        load(tmp_path)


# --------------------------------------------------------------------------
# the contract between the schema, the built-ins, and the shipped specimen
# --------------------------------------------------------------------------


def test_every_cli_verb_key_has_a_built_in():
    for verb, keys in CLI_VERBS.items():
        for key in keys:
            assert key in BUILT_IN, f"{verb}.{key} has no built-in default"


def test_every_built_in_is_reachable_from_some_verb_or_is_the_json_switch():
    reachable = {k for keys in CLI_VERBS.values() for k in keys}
    assert set(BUILT_IN) == reachable | {"json"}


def test_mcp_has_no_json_key_because_an_mcp_result_is_always_json():
    assert "json" not in MCP_KEYS


def test_mcp_has_no_band_key_because_the_mcp_block_is_unconditional():
    assert "band" not in MCP_KEYS


def test_mcp_is_in_the_schema_at_all():
    # It is the one surface with no flags, so this tuple is its only knob.
    # If it is ever emptied, MCP silently becomes unconfigurable again.
    assert MCP_KEYS


def test_the_specimen_as_shipped_matches_built_in_for_every_key(tmp_path):
    write(tmp_path, specimen())
    cfg = load(tmp_path)
    for verb, keys in CLI_VERBS.items():
        as_json = cfg.resolve_json(verb)
        assert as_json == BUILT_IN["json"]
        for key in keys:
            assert cfg.resolve(verb, key, as_json=as_json) == BUILT_IN[key], (verb, key)
    assert cfg.resolve_mcp("top") == BUILT_IN["top"]


def test_the_specimen_mentions_every_root(tmp_path):
    text = specimen()
    for root in ("[cli]", "[cli.json]", "[mcp]"):
        assert root in text, f"the specimen never shows {root}"


def test_the_specimen_is_not_commented_out(tmp_path):
    # ⚠ Decision 14, and load-bearing since 2026-08-28: a fully-commented
    # specimen would break every verb the moment `fux setup` wrote it.
    load(write(tmp_path, specimen()))  # must not raise on load
    assert load(tmp_path).resolve("ask", "band", as_json=False) is False


def test_the_specimen_warns_that_top_bounds_a_reported_signal():
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
        DEFAULT_OUTPUT.resolve("nosuchverb", "top", as_json=False)


def test_resolve_mcp_rejects_an_unknown_key():
    with pytest.raises(FuxError, match="not an output key for `mcp`"):
        DEFAULT_OUTPUT.resolve_mcp("band")


def test_output_defaults_is_frozen():
    with pytest.raises(Exception):
        DEFAULT_OUTPUT.mcp = {}  # type: ignore[misc]


def test_two_loads_of_the_same_file_are_equal(tmp_path):
    write(tmp_path, "[cli]\nband = true\ntop = 9\n\n[cli.json]\nenabled = false\n")
    assert load(tmp_path) == load(tmp_path)
    assert isinstance(load(tmp_path), OutputDefaults)


def test_bypass_resolves_every_verb_and_mcp_key_to_built_in():
    for verb, keys in CLI_VERBS.items():
        assert DEFAULT_OUTPUT.resolve_json(verb) == BUILT_IN["json"]
        for key in keys:
            assert DEFAULT_OUTPUT.resolve(verb, key, as_json=False) == BUILT_IN[key]
    assert DEFAULT_OUTPUT.resolve_mcp("top") == BUILT_IN["top"]


# --------------------------------------------------------------------------
# the CLI seam — found by RUNNING it, so it is gated (CLAUDE.md two strikes)
# --------------------------------------------------------------------------


def test_apply_output_defaults_resolves_against_a_real_repo(tmp_path, monkeypatch):
    """⚠ **This test exists because the first build shipped a broken import.**

    `cli._apply_output_defaults` imported `find_root` from `store.fuxdir`,
    where it does not live — it is in `config`. Every unit test passed,
    because they monkeypatch `fux.query.find_root` and never reach `cli`'s
    own import; the failure only appeared on `python -m fux ask` in a real
    repo, as an `ImportError` on every single verb.

    The guard is to exercise the seam with NO monkeypatching at all.
    """
    from fux.cli import _apply_output_defaults, build_parser

    (tmp_path / "fux.toml").write_text("[fux]\nversion = 1\n", encoding="utf-8")
    write(
        tmp_path,
        "[cli]\nband = true\ntop = 3\n\n[cli.ask]\nexplain = false\n\n[cli.json]\nenabled = false\n",
    )
    monkeypatch.chdir(tmp_path)

    args = build_parser().parse_args(["ask", "rollback"])
    assert args.top is None and args.band is None, "argparse must hand over None"
    _apply_output_defaults(args)
    assert args.top == 3, "[cli] top"
    assert args.band is True, "[cli] band"
    assert args.json is False, "[cli.json] enabled"


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
    write(tmp_path, "[cli]\ntop = true\n")
    monkeypatch.chdir(tmp_path)

    args = build_parser().parse_args(["ask", "rollback"])
    with pytest.raises(FuxError, match="must be a whole number"):
        _apply_output_defaults(args)


def test_apply_output_defaults_raises_when_the_file_is_incomplete(tmp_path, monkeypatch):
    """⚠ **The behaviour Arpit's 2026-08-28 ruling exists to produce.** A
    `.fux/output.toml` that is present, parses, and simply never set a key
    `ask` needs is not silently filled from `BUILT_IN` any more."""
    from fux.cli import _apply_output_defaults, build_parser

    (tmp_path / "fux.toml").write_text("[fux]\nversion = 1\n", encoding="utf-8")
    write(tmp_path, "[cli]\nband = true\n\n[cli.json]\nenabled = false\n")  # no `top`
    monkeypatch.chdir(tmp_path)

    args = build_parser().parse_args(["ask", "rollback"])
    with pytest.raises(FuxError, match="does not set `top`"):
        _apply_output_defaults(args)


def test_apply_output_defaults_raises_when_the_file_is_missing_entirely(tmp_path, monkeypatch):
    from fux.cli import _apply_output_defaults, build_parser

    (tmp_path / "fux.toml").write_text("[fux]\nversion = 1\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    args = build_parser().parse_args(["doctor"])
    with pytest.raises(FuxError, match="fux setup"):
        _apply_output_defaults(args)


def test_no_output_config_bypasses_an_incomplete_file(tmp_path, monkeypatch):
    from fux.cli import _apply_output_defaults, build_parser

    (tmp_path / "fux.toml").write_text("[fux]\nversion = 1\n", encoding="utf-8")
    write(tmp_path, "[cli]\nband = true\n")  # no `top`, no `[cli.json]`
    monkeypatch.chdir(tmp_path)

    args = build_parser().parse_args(["ask", "rollback", "--no-output-config"])
    _apply_output_defaults(args)
    assert args.top == BUILT_IN["top"]
    assert args.json is False


def test_every_gated_flag_is_declared_default_none():
    """ADR-OUTPUT decision 10, and veto condition 4.

    ⚠ **The one defect in this feature that nothing else can see.** A gated
    `store_true` left at `default=False` makes `.fux/output.toml` silently
    never take effect for that key: the loader works, every other test
    passes, and the feature just does not exist. Assert it structurally.
    """
    from fux.cli import build_parser
    from fux.output_config import CLI_VERBS

    parser = build_parser()
    sub = [a for a in parser._subparsers._group_actions if a.dest == "command"][0]
    for verb, keys in CLI_VERBS.items():
        if verb not in sub.choices:
            continue
        gated = set(keys) | {"json"}  # `json`/`enabled` is gated too
        for action in sub.choices[verb]._actions:
            if action.dest in gated:
                assert action.default is None, (
                    f"`fux {verb} --{action.dest.replace('_', '-')}` is declared "
                    f"default={action.default!r}; ADR-OUTPUT decision 10 requires "
                    "default=None, or the config can never take effect"
                )


def test_mcp_verb_has_no_gated_flags_of_its_own():
    """`mcp` is not in `CLI_VERBS` at all — its only knob, `[mcp] top`, has
    no CLI flag, so there is nothing on `p_mcp` decision 10 could apply to."""
    from fux.output_config import CLI_VERBS

    assert "mcp" not in CLI_VERBS


def test_every_verb_that_reads_the_file_can_bisect_it():
    """ADR-OUTPUT decision 15, asserted structurally rather than trusted.

    ⚠ **This is the exact class of bug the 2026-08-28 no-fallback ruling made
    load-bearing.** Before that ruling an unset key silently fell through to
    `BUILT_IN`, so a verb missing `--no-output-config` merely could not be
    bisected on purpose. Now that a repo-in-effect file that omits a key is a
    hard `FuxError`, the same missing flag makes that verb **impossible to
    run at all** once `.fux/output.toml` exists and is incomplete — `doctor`,
    the one verb you would reach for to diagnose that, included. Every verb
    `CLI_VERBS` declares (even an empty key tuple — `doctor`, `explain`,
    `graph`, `hooks`, `daemon` still resolve `json`) must carry the flag, and
    so must `mcp`, which reads `[mcp]` outside `CLI_VERBS` entirely.
    """
    from fux.cli import build_parser
    from fux.output_config import CLI_VERBS

    parser = build_parser()
    sub = [a for a in parser._subparsers._group_actions if a.dest == "command"][0]
    for verb in (*CLI_VERBS, "mcp"):
        assert verb in sub.choices, f"`fux {verb}` is not a registered verb"
        dests = {action.dest for action in sub.choices[verb]._actions}
        assert "no_output_config" in dests, (
            f"`fux {verb}` reads {OUTPUT_NAME} but has no `--no-output-config` "
            "escape hatch — ADR-OUTPUT decision 15"
        )
