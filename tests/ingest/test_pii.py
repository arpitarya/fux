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
    # An order id, a tracking number, a hash prefix. The card rule ships
    # disabled -- and stays disabled now that it carries `validate = "luhn"`,
    # because one random 16-digit run in ten passes Luhn. This one does.
    out, _ = pii.redact(_starter(), "order 4242424242424242 shipped")
    assert "4242424242424242" in out


def test_the_starter_leaves_ordinary_prose_completely_untouched():
    prose = "Roll forward, never back. The deploy runbook is in docs/adr."
    assert pii.redact(_starter(), prose) == (prose, {})


# -- checksum validators (ADR-PII decision 16) -------------------------------


def test_luhn_accepts_the_published_vectors_and_rejects_their_neighbours():
    # 79927398713 is the worked example in the Luhn algorithm's literature;
    # 4111... and 4242... are the card networks' documented test numbers.
    for valid in ("79927398713", "4111 1111 1111 1111", "4242-4242-4242-4242"):
        assert pii.luhn(valid), valid
    for invalid in ("79927398710", "4111 1111 1111 1112", "4242-4242-4242-4243"):
        assert not pii.luhn(invalid), invalid


def test_verhoeff_accepts_the_published_vectors_and_rejects_their_neighbours():
    # 236 -> check digit 3, and 12345 -> check digit 1: the worked examples
    # given for Verhoeff's scheme.
    assert pii.verhoeff("2363") and pii.verhoeff("123451")
    assert not pii.verhoeff("2364") and not pii.verhoeff("123452")


@pytest.mark.parametrize("check", [pii.luhn, pii.verhoeff], ids=["luhn", "verhoeff"])
def test_exactly_one_check_digit_completes_any_payload(check):
    # The defining property of a check-digit scheme. A table typo in Verhoeff
    # breaks it for some payload, so this sweeps a thousand of them.
    for payload in range(1000):
        passing = [d for d in "0123456789" if check(f"{payload:04d}{d}")]
        assert len(passing) == 1, (payload, passing)


@pytest.mark.parametrize(
    ("check", "number"),
    [(pii.luhn, "4111111111111111"), (pii.verhoeff, "234567890124")],
    ids=["luhn", "verhoeff"],
)
def test_every_single_digit_error_is_caught(check, number):
    assert check(number)
    for position, original in enumerate(number):
        for digit in "0123456789":
            if digit != original:
                typo = number[:position] + digit + number[position + 1 :]
                assert not check(typo), typo


def test_verhoeff_catches_the_09_90_transposition_that_luhn_cannot():
    # Why Aadhaar uses Verhoeff, pinned so the two schemes can never be
    # swapped behind their names: Luhn scores `09` and `90` identically.
    for payload in range(1000):
        for d in "0123456789":
            original = f"{payload:03d}09{d}"
            swapped = f"{payload:03d}90{d}"
            assert pii.luhn(original) == pii.luhn(swapped)
            if pii.verhoeff(original):
                assert not pii.verhoeff(swapped), original


def test_a_checksum_reads_ascii_digits_only():
    assert pii.luhn("4111-1111 1111.1111")  # separators drop out
    # A fullwidth digit is not a digit to either scheme -- `str.isdigit` says
    # otherwise, which is exactly why it is not what `_digits` uses.
    assert not pii.luhn("411111111111111\uff11")


def test_fewer_than_two_digits_is_never_valid():
    for text in ("", "0", "abc", "card 0"):
        assert not pii.luhn(text) and not pii.verhoeff(text), text


CARD = {
    "name": "card",
    "pattern": r"\b\d{4}[ -]\d{4}[ -]\d{4}[ -]\d{4}\b",
    "validate": "luhn",
}


def test_a_validated_rule_replaces_only_the_matches_that_pass():
    out, hits = pii.redact(
        rules(CARD), "card 4111 1111 1111 1111, order 4111 1111 1111 1112"
    )
    assert out == "card [PII:card], order 4111 1111 1111 1112"
    assert hits == {"card": 1}


def test_a_rule_whose_every_match_fails_reports_no_hit_at_all():
    # Absent, not zero -- the same shape every non-firing rule reports.
    assert pii.redact(rules(CARD), "order 4111 1111 1111 1112") == (
        "order 4111 1111 1111 1112",
        {},
    )


def test_the_checksum_runs_over_the_GROUP_not_the_whole_match():
    # The label carries a digit. Validating the whole match would read 17
    # digits and fail; validating group 2 reads the card and passes.
    text = "ref7-4111 1111 1111 1111"
    pattern = r"ref(\d)-(\d{4} \d{4} \d{4} \d{4})"
    grouped = rules({"name": "c", "pattern": pattern, "group": 2, "validate": "luhn"})
    whole = rules({"name": "c", "pattern": pattern, "validate": "luhn"})
    assert pii.redact(grouped, text) == ("ref7-[PII:c]", {"c": 1})
    assert pii.redact(whole, text) == (text, {})


def test_validate_changes_WHICH_values_go_and_never_WHAT_replaces_them():
    # The no-checksum path is `subn`, the checksum path is a callback; a
    # backreference in `replacement` must mean the same thing on both.
    entry = {
        "name": "c",
        "pattern": r"(\d{4}) \d{4} \d{4} (\d{4})",
        "replacement": r"\1-XXXX-XXXX-\2",
    }
    text = "pay 4111 1111 1111 1111"
    plain = pii.redact(rules(entry), text)
    checked = pii.redact(rules({**entry, "validate": "luhn"}), text)
    assert plain == checked == ("pay 4111-XXXX-XXXX-1111", {"c": 1})


def test_accepts_is_what_apply_uses():
    # `tools/pii-probe/` counts with `accepts`; if `apply` stopped using it,
    # the probe would report removals ingest never makes.
    import inspect

    assert "self.accepts(" in inspect.getsource(pii.Rule.apply)


def test_an_unknown_validator_raises_at_load():
    with pytest.raises(FuxError, match="unknown validator 'lunh'"):
        rules({**CARD, "validate": "lunh"})
    with pytest.raises(FuxError, match="unknown validator"):
        rules({**CARD, "validate": ["luhn"]})


def test_adding_a_validator_changes_the_digest():
    # It changes which values reach the committed index, so it must
    # invalidate extraction reuse exactly as a pattern edit does.
    without = {k: v for k, v in CARD.items() if k != "validate"}
    assert pii.digest(rules(without)) != pii.digest(rules(CARD))
    assert pii.digest(rules(CARD)) != pii.digest(rules({**CARD, "validate": "verhoeff"}))


def test_a_ruleset_without_validate_keeps_its_pre_checksum_digest():
    """Upgrading fux must not force a full re-extract nobody's edit caused.

    The literal was computed by the `digest()` that shipped before `validate`
    existed. If this fails, every consumer's next ingest after upgrading is a
    full one -- change the literal only if that cost is being chosen.
    """
    r = rules(
        {"name": "email", "pattern": r"[\w.+-]+@[\w-]+\.[\w.]+"},
        {
            "name": "card",
            "pattern": r"(\d{4}(?:[ -]?\d{4}){3})",
            "group": 1,
            "flags": ["ignorecase"],
            "replacement": "<c>",
        },
    )
    assert pii.digest(r) == "b63f1857745187c58b9711cae4a7363fface5063ebcce4f063973e109be2132c"


def test_the_starters_disabled_checksum_rules_are_valid_once_enabled():
    """They ship commented out, so nothing else here ever parses them.

    Uncomment exactly those two blocks and load the result, so a template edit
    cannot leave a consumer enabling a rule that refuses to load.
    """
    import re
    import tomllib
    from pathlib import Path

    template = (
        Path(__file__).resolve().parents[2] / "src" / "fux" / "templates" / "pii.toml.txt"
    ).read_text(encoding="utf-8")
    blocks = re.findall(r"^# \[\[rule\]\]\n(?:# \w+\s*=.*\n)+", template, re.MULTILINE)
    enabled = [b for b in blocks if 'validate' in b]
    assert len(enabled) == 2, "expected the aadhaar and card blocks"
    text = "".join(re.sub(r"^# ", "", b, flags=re.MULTILINE) + "\n" for b in enabled)
    loaded = pii.parse(tomllib.loads(text), origin="<enabled>")
    assert {(r.name, r.validate) for r in loaded} == {("aadhaar", "verhoeff"), ("card", "luhn")}

    out, hits = pii.redact(
        loaded,
        "uid 2345 6789 0124 not 2345 6789 0125; card 4111 1111 1111 1111 not 4111 1111 1111 1112",
    )
    assert out == "uid [PII:aadhaar] not 2345 6789 0125; card [PII:card] not 4111 1111 1111 1112"
    assert hits == {"aadhaar": 1, "card": 1}

    # A Luhn-valid card whose first twelve digits are ALSO Verhoeff-valid. The
    # aadhaar rule runs first; without its digit-group guards it takes those
    # twelve and leaves the card rule nothing to match.
    assert pii.verhoeff("4000 0000 0005") and pii.luhn("4000 0000 0005 0007")
    assert pii.redact(loaded, "card 4000 0000 0005 0007") == ("card [PII:card]", {"card": 1})
