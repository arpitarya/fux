"""The PII matcher — its grammar, its strictness, and its determinism.

Pure over data. No corpus, no network.
"""

from __future__ import annotations

import pytest

from fux.errors import FuxError
from fux.ingest import pii


def rules(*entries):
    return pii.parse({"rule": list(entries)}, origin="<test>")


EMAIL = {"name": "email", "pattern": r"[\w.+-]+@[\w-]+\.[\w.]+"}


# -- redaction --------------------------------------------------------------


def test_a_match_becomes_the_replacement():
    out, hits = pii.redact(rules(EMAIL), "write to a@b.com please")
    assert out == "write to [PII:email] please"
    assert hits == {"email": 1}


def test_the_default_replacement_names_the_RULE_not_a_generic_token():
    # A reader of a redacted index can see WHICH rule fired. One [REDACTED]
    # everywhere destroys that, and it costs nothing to keep.
    out, _ = pii.redact(rules(EMAIL), "a@b.com")
    assert out == "[PII:email]"


def test_a_declared_replacement_wins():
    out, _ = pii.redact(rules({**EMAIL, "replacement": "<gone>"}), "a@b.com")
    assert out == "<gone>"


def test_no_rules_returns_the_text_untouched_and_no_hits():
    assert pii.redact((), "a@b.com") == ("a@b.com", {})


def test_text_with_no_match_is_returned_unchanged():
    out, hits = pii.redact(rules(EMAIL), "nothing sensitive here")
    assert out == "nothing sensitive here" and hits == {}


def test_every_occurrence_is_replaced_not_just_the_first():
    out, hits = pii.redact(rules(EMAIL), "a@b.com and c@d.com")
    assert out.count("[PII:email]") == 2
    assert hits == {"email": 2}


# -- group, the context-preserving case -------------------------------------


def test_group_replaces_only_that_group_and_keeps_the_context():
    r = rules({
        "name": "card", "pattern": r"(?:ending )(\d{4})", "group": 1,
        "replacement": "[PII:card]",
    })
    out, hits = pii.redact(r, "the card ending 4242 was declined")
    assert out == "the card ending [PII:card] was declined"
    assert hits == {"card": 1}


def test_group_zero_is_the_whole_match():
    r = rules({**EMAIL, "group": 0})
    assert pii.redact(r, "a@b.com")[0] == "[PII:email]"


def test_a_group_beyond_the_pattern_is_refused_at_load():
    with pytest.raises(FuxError, match="group 3"):
        rules({"name": "x", "pattern": r"(a)(b)", "group": 3})


# -- determinism (L3) -------------------------------------------------------


def test_the_same_input_and_rules_give_the_same_bytes_every_time():
    r = rules(EMAIL, {"name": "pan", "pattern": r"\b[A-Z]{5}\d{4}[A-Z]\b"})
    text = "a@b.com ABCDE1234F c@d.com"
    first = pii.redact(r, text)[0]
    for _ in range(20):
        assert pii.redact(r, text)[0] == first


def test_rules_apply_in_FILE_order_and_the_order_is_observable():
    # Narrow-then-broad and broad-then-narrow give different output. This is
    # not a defect to fix -- it is why the order is the file's and not one fux
    # computes -- but it must be pinned so it cannot change silently.
    narrow = {"name": "jwt", "pattern": r"eyJ[A-Za-z0-9]+", "replacement": "[J]"}
    broad = {"name": "token", "pattern": r"\b\w{6,}\b", "replacement": "[T]"}
    text = "eyJabcdef here"
    assert pii.redact(rules(narrow, broad), text)[0] != pii.redact(rules(broad, narrow), text)[0]


def test_nothing_in_this_module_reads_a_clock_or_random():
    import inspect

    src = inspect.getsource(pii)
    for banned in ("import time", "import random", "datetime", "time.time"):
        assert banned not in src, f"{banned} in a module the index depends on"


# -- the digest, which is cache invalidation and not decoration -------------


def test_an_empty_ruleset_digests_to_the_empty_string():
    # A repo with no rules writes no state and behaves as before the feature.
    assert pii.digest(()) == ""


def test_changing_a_pattern_changes_the_digest():
    a = pii.digest(rules(EMAIL))
    b = pii.digest(rules({**EMAIL, "pattern": r"\S+@\S+"}))
    assert a != b


def test_changing_only_the_REPLACEMENT_changes_the_digest():
    # It lands in committed bytes, so it must invalidate reuse exactly as a
    # pattern change does. This is the one people forget.
    a = pii.digest(rules(EMAIL))
    b = pii.digest(rules({**EMAIL, "replacement": "<x>"}))
    assert a != b


def test_adding_a_rule_changes_the_digest():
    assert pii.digest(rules(EMAIL)) != pii.digest(rules(EMAIL, {"name": "b", "pattern": "z+"}))


def test_reordering_rules_changes_the_digest():
    # Order is observable in the output, so it must be observable in the digest.
    other = {"name": "b", "pattern": "z+"}
    assert pii.digest(rules(EMAIL, other)) != pii.digest(rules(other, EMAIL))


def test_the_digest_is_stable_across_calls():
    r = rules(EMAIL)
    assert pii.digest(r) == pii.digest(r)


# -- strictness -------------------------------------------------------------


def test_a_missing_file_is_silence_not_an_error(tmp_path):
    assert pii.load(tmp_path) == ()


def test_a_malformed_file_raises(tmp_path):
    (tmp_path / ".fux").mkdir()
    (tmp_path / ".fux" / "pii.toml").write_text("[[rule]\nname = 'x'\n")
    with pytest.raises(FuxError, match="invalid TOML"):
        pii.load(tmp_path)


def test_an_unknown_key_raises(tmp_path):
    with pytest.raises(FuxError, match="unknown key"):
        rules({**EMAIL, "patern": "typo"})


def test_an_unknown_flag_raises():
    with pytest.raises(FuxError, match="unknown flag"):
        rules({**EMAIL, "flags": ["ignorecse"]})


def test_a_known_flag_applies():
    r = rules({"name": "x", "pattern": "abc", "flags": ["ignorecase"]})
    assert pii.redact(r, "ABC")[0] == "[PII:x]"


def test_an_invalid_regex_raises_at_LOAD_not_mid_ingest():
    with pytest.raises(FuxError, match="invalid regex"):
        rules({"name": "x", "pattern": "([unclosed"})


def test_a_pattern_that_matches_the_empty_string_is_refused():
    # It would fire between every character of every document.
    with pytest.raises(FuxError, match="empty string"):
        rules({"name": "x", "pattern": r"\d*"})


def test_a_duplicate_rule_name_raises():
    with pytest.raises(FuxError, match="duplicate"):
        rules(EMAIL, EMAIL)


def test_a_missing_pattern_raises():
    with pytest.raises(FuxError, match="'pattern' is required"):
        rules({"name": "x"})


def test_an_unknown_top_level_key_raises():
    with pytest.raises(FuxError, match="unknown top-level key"):
        pii.parse({"rule": [EMAIL], "rules": []}, origin="<t>")


# -- the shipped starter ----------------------------------------------------


def _starter():
    from pathlib import Path

    template = (
        Path(__file__).resolve().parents[2]
        / "src" / "fux" / "templates" / "pii.toml.txt"
    )
    import tomllib

    return pii.parse(tomllib.loads(template.read_text(encoding="utf-8")), origin="<starter>")


def test_the_shipped_starter_loads():
    assert _starter()


def test_the_starter_catches_a_credential_and_an_email():
    out, hits = pii.redact(
        _starter(),
        "mail arpit@example.com key AKIAIOSFODNN7EXAMPLE pan ABCDE1234F",
    )
    assert "arpit@example.com" not in out
    assert "AKIAIOSFODNN7EXAMPLE" not in out
    assert "ABCDE1234F" not in out
    assert set(hits) == {"email", "aws-access-key", "pan"}


def test_the_starter_leaves_an_INTERNAL_IP_alone():
    """The risky rules ship commented out, and that is a decision, not an omission.

    An internal IP is often the most useful thing on a runbook page. Removing
    it makes the runbook useless while looking like the feature worked.
    """
    out, _ = pii.redact(_starter(), "deploy to 10.0.0.5 port 8080")
    assert "10.0.0.5" in out


def test_the_starter_leaves_a_bare_sixteen_digit_number_alone():
    # An order id, a tracking number, a hash prefix. Cards need a Luhn check
    # and a regex cannot compute one, so the card rule ships disabled.
    out, _ = pii.redact(_starter(), "order 4242424242424242 shipped")
    assert "4242424242424242" in out


def test_the_starter_leaves_ordinary_prose_completely_untouched():
    prose = "Roll forward, never back. The deploy runbook is in docs/adr."
    assert pii.redact(_starter(), prose) == (prose, {})
