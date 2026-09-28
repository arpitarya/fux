"""W-233 — identifier families: the grammar, the guard, the matcher, the file.

🔴 **One fixture, two readers.** [`identifiers-fixture.json`](identifiers-fixture.json)
is read by this file and by `node/test/identifiers.test.mjs`. Its values are
committed literals, reviewed once against the
[fixture run](../../work/regression/2026-09-28-identifier-fixture/report.md);
if a row moves, the question is *"was that intended?"*, and the item that moved
it names the row.

The properties below are the ones the compare doc's S1–S8 rest on, each pinned
so a later change has to break a test to break the design.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from fux.errors import FuxError
from fux.query import identifiers as ids_mod
from fux.query.analyzer import analyze, analyze_pairs
from fux.query.identifiers import EMPTY, build, check_regex, parse, parse_template
from fux.query.stem import stem

FIXTURE = json.loads((Path(__file__).parent / "identifiers-fixture.json").read_text("utf-8"))
FAM = FIXTURE["families"]
RULES = build(FAM["templates"], [], [], FAM["regex"])


@pytest.mark.parametrize("case", FIXTURE["analysis"], ids=lambda c: c["text"] or "<empty>")
def test_analysis_matches_the_fixture(case):
    assert analyze(case["text"], RULES) == case["terms"]


@pytest.mark.parametrize("case", FIXTURE["analysis"], ids=lambda c: c["text"] or "<empty>")
def test_pairs_agree_with_analyze_under_families(case):
    assert [a for _, a in analyze_pairs(case["text"], RULES)] == analyze(case["text"], RULES)


@pytest.mark.parametrize("src", FIXTURE["templates_accepted"])
def test_template_accepted(src):
    assert parse_template(src).kind == "template"


@pytest.mark.parametrize("src", FIXTURE["templates_refused"])
def test_template_refused(src):
    with pytest.raises(FuxError):
        parse_template(src)


@pytest.mark.parametrize("row", FIXTURE["regex_accepted"], ids=lambda r: r["regex"])
def test_regex_accepted_and_normalised(row):
    assert check_regex(row["regex"]) == row["normalised"]


@pytest.mark.parametrize("src", FIXTURE["regex_refused"])
def test_regex_refused(src):
    with pytest.raises(FuxError):
        check_regex(src)


# ---- the design properties ---------------------------------------------------

SAMPLES = [c["text"] for c in FIXTURE["analysis"]] + [
    "The RF-118 fryer, ADR-0004 and `src/fux/query/bm25f.py` — see v2.3.1.",
    "getUserName HTTPServer snake_case kebab-case 10–12 dates 2026-09-28",
]


@pytest.mark.parametrize("text", SAMPLES)
def test_no_families_is_v3_byte_for_byte(text):
    """G3 at unit level: an empty rule set is the rollback."""
    assert analyze(text, EMPTY) == analyze(text)
    assert analyze(text, build([], [], [], [])) == analyze(text)
    assert analyze_pairs(text, EMPTY) == analyze_pairs(text)


@pytest.mark.parametrize("text", SAMPLES)
def test_families_only_ADD_terms(text):
    """S1: v3's terms survive in order; a family inserts, never removes."""
    base = analyze(text)
    it = iter(analyze(text, RULES))
    assert all(any(t == u for u in it) for t in base)


def test_a_canonical_term_is_never_stemmed():
    """F4: the whole form stays as written. A regex canonical can be all letters."""
    rules = build([], [], [], ["[A-Z]{3}ING"])
    assert "abcing" in analyze("see ABCING now", rules)
    assert stem("abcing") != "abcing"


def test_plainly_written_id_costs_nothing():
    assert analyze("RF-118", RULES) == analyze("RF-118")


def test_drop_beats_keep_and_detected():
    r = build(["RF-{n}"], ["RF-{n}", "ADR-{n}"], ["RF-{n}"], [])
    assert [x.source for x in r.rules] == ["ADR-{n}"]


def test_a_drop_entry_must_itself_parse():
    with pytest.raises(FuxError):
        build([], [], ["{X}-{n}"], [])


def test_digest_is_of_the_effective_rules():
    a = build(["RF-{n}", "ADR-{n}"], [], [], [])
    b = build(["ADR-{n}"], ["RF-{n}"], [], [])
    assert a.digest == b.digest != ""
    assert build([], [], [], []).digest == ""


def _write(tmp_path, text):
    (tmp_path / ".fux").mkdir(exist_ok=True)
    (tmp_path / ids_mod.FILE).write_text(text, encoding="utf-8")


def test_missing_file_is_a_hard_error(tmp_path):
    with pytest.raises(FuxError, match="identifiers.toml is missing"):
        ids_mod.load(tmp_path)


def test_empty_sections_are_valid(tmp_path):
    _write(tmp_path, "[user]\nkeep = []\n\n[detected]\nfamilies = []\n")
    assert ids_mod.load(tmp_path).empty


def test_user_only_file_is_valid(tmp_path):
    _write(tmp_path, '[user]\nkeep = ["RF-{n}"]\n')
    assert [r.source for r in ids_mod.load(tmp_path).rules] == ["RF-{n}"]


def test_a_comment_edit_does_not_move_the_digest(tmp_path):
    _write(tmp_path, '[user]\nkeep = ["RF-{n}"]\n')
    first = ids_mod.load(tmp_path).digest
    _write(tmp_path, '# a note\n[user]\nkeep = ["RF-{n}"]  # the fryer ids\n')
    assert ids_mod.load(tmp_path).digest == first


@pytest.mark.parametrize("text", ["[users]\n", '[user]\nkeeps = ["RF-{n}"]\n', "[detected]\nfamily = []\n",
                                  '[user]\nkeep = "RF-{n}"\n'])
def test_unknown_or_malformed_keys_are_refused(tmp_path, text):
    _write(tmp_path, text)
    with pytest.raises(FuxError):
        ids_mod.load(tmp_path)


def test_correct_normalise_takes_no_families():
    """S4: a stored correction's key must not move when the families do."""
    from fux.correct import normalise

    assert normalise("what is RF 118") == normalise("what is RF 118")
    assert "rf-118" not in normalise("what is RF 118")


def test_parse_origin_is_named():
    with pytest.raises(FuxError, match="here.toml"):
        parse({"bogus": {}}, origin="here.toml")


# ---- the regex parity check and the [detected] writer --------------------------


def test_regex_parity_agrees_across_astral_and_unicode_text():
    """Python and V8 find the same spans, offsets compared in UTF-16 units."""
    import shutil

    from fux.inspect.idfamilies import regex_parity

    if shutil.which("node") is None:
        pytest.skip("node is not installed")
    rules = build(["RF-{n}"], [], [], ["#\\d{3,6}", "JIRA:[A-Z]+-\\d+"])
    texts = [("a", "😀 RF–118 and #1234 then 😀😀 JIRA:PROJ-7"), ("b", "no ids"), ("c", "RF 9 / rf10")]
    parity = regex_parity(rules, texts)
    assert parity.ran and parity.agree, parity.diff
    assert parity.matches == 5


def test_rewrite_replaces_only_detected():
    from fux.identifiers_cmd import rewrite
    from fux.inspect.idfamilies import Family

    fam = [Family(template="RF-{n}", values=4, docs=2, examples=())]
    text = '# head\n[user]\nkeep = ["ADR-{n}"]  # mine\n\n[detected]\nfamilies = ["OLD-{n}"]\n'
    out = rewrite(text, fam)
    assert out.startswith('# head\n[user]\nkeep = ["ADR-{n}"]  # mine\n\n[detected]\n')
    assert '"RF-{n}",  # 4 values in 2 documents' in out and "OLD-{n}" not in out
    assert rewrite('[user]\nkeep = []\n', fam).startswith('[user]\nkeep = []\n\n[detected]')
    # [detected] before [user]: only its own block is replaced
    out = rewrite('[detected]\nfamilies = []\n\n[user]\ndrop = ["X-{n}"]\n', fam)
    assert out.endswith('[user]\ndrop = ["X-{n}"]\n') and '"RF-{n}"' in out


def test_the_lens_finds_ids_and_not_file_names_decimals_or_ranges():
    """S8 rule 1, as tightened on fux's own prose after the run (the ladder's
    families were verified identical under both rules)."""
    from fux.inspect.idfamilies import detect

    docs = [
        ("a", "RF-117 and RF-118 · W-104-enrich.md · anchor-0.5 · A.13 · L0-L12 · v2.3.1"),
        ("b", "RF-119 · W-105-cdp.md · anchor-1.0 · A.14 · L1-L10 · v2.4.0"),
        ("c", "RF-120 · W-106-x.md · anchor-2.0 · A.15 · L2-L9 · v3.0.0"),
    ]
    found = [f.template for f in detect(docs, min_values=3, min_docs=2, examples=0).families]
    assert found == ["RF-{n}"]
