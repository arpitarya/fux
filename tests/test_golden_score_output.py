"""L11 decision 13 — the scorer's output is an allow-list, and this pins it.

🔴 **Nothing here touches a real key, and nothing here needs one to exist.** The
row schema is asserted by calling `score_one` with a key dict invented in this
file; the two refusals are asserted by calling `main` with paths in a tmpdir. If
this test ever needs a real key to pass, it has been written wrong.

**What it defends.** L11's first sentence defines an *answer* as **answer text,
an evidence quote, a `relevant` or `primary` list, or an `answerable` flag**.
Decision 13 permits `tools/golden-score/score.py` to read a key only because none
of those four reaches what it writes. The containment is therefore a property of
the output schema, and a schema nobody checks is a schema that grows a field.

⚠ **One such field already existed.** `answerable_key` — the key's `answerable`
flag, verbatim, per question — was in every row until 2026-09-21. It was not
caught by review; it was caught by writing this test. That is the whole argument
for the test being here.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
SCORER = REPO / "tools" / "golden-score" / "score.py"

# The complete set of keys a scored row may carry. Adding one is an amendment to
# L11 decision 13, not a refactor.
ALLOWED_ROW_KEYS = {
    "id",
    "band",
    "said_unanswerable",
    "hit@1",
    "hit@5",
    "hit@10",
    "hit@20",
    "hit@50",
    "primary_rank",
    "abstain_correct",
    "abstain_wrong",
    "answered_unanswerable",
    "evidence_quoted",
    "answer_text_verdict",
    # decision 13b (Arpit, 2026-09-28, W-168 step 7): two counts, never a facet
    "facets_top5",
    "facets_key",
}

# Names that would mean an answer had reached the output. `answerable_key` is
# named explicitly because it was really there.
FORBIDDEN_ROW_KEYS = {
    "answerable_key",
    "answerable",
    "relevant",
    "primary",
    "evidence",
    "quote",
    "quotes",
    "answer",
    "answer_text",
    "key",
}


def _load():
    spec = importlib.util.spec_from_file_location("golden_score", SCORER)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def scorer():
    assert SCORER.is_file(), f"{SCORER} is missing — L11 decision 13 names it"
    return _load()


# A key that exists only in this file. Every distinctive string in it is
# something the output must never echo.
SYNTHETIC_KEY = {
    "id": "q001",
    "relevant": ["docs/ALPHA-SECRET.md", "docs/BETA-SECRET.md"],
    "primary": "docs/ALPHA-SECRET.md",
    "answerable": True,
    "evidence": [{"quote": "the quick brown fox jumps over the lazy dog"}],
}
SYNTHETIC_ROW = {
    "id": "q001",
    "ranked": ["docs/ALPHA-SECRET.md", "docs/other.md"],
    "band": "strong",
    "answerable": True,
    "answer_text": "the quick brown fox jumps over the lazy dog, apparently",
}


def test_row_carries_only_allow_listed_keys(scorer):
    out = scorer.score_one(SYNTHETIC_ROW, SYNTHETIC_KEY)
    extra = set(out) - ALLOWED_ROW_KEYS
    assert not extra, (
        f"the scored row grew {sorted(extra)}. L11 decision 13's allow-list is the "
        "carve-out's containment — adding a field is an amendment, not a refactor."
    )
    assert not (set(out) & FORBIDDEN_ROW_KEYS)


def test_row_echoes_no_string_from_the_key(scorer):
    """The strongest form: no key string survives into the output, at any depth."""
    blob = json.dumps(scorer.score_one(SYNTHETIC_ROW, SYNTHETIC_KEY))
    for secret in ("ALPHA-SECRET", "BETA-SECRET", "quick brown fox"):
        assert secret not in blob, (
            f"{secret!r} reached the scored output. That is a document name or an "
            "evidence quote — two of the four things L11 calls an answer."
        )


def test_answerable_key_stays_gone(scorer):
    """A named regression: this field was published per question until 2026-09-21."""
    assert "answerable_key" not in scorer.score_one(SYNTHETIC_ROW, SYNTHETIC_KEY)


def test_refuses_when_the_environment_looks_like_an_agent(scorer, tmp_path, monkeypatch, capsys):
    """Decision 13's permission is Arpit's HAND. A tripwire, never a guarantee."""
    monkeypatch.setenv("CLAUDECODE", "1")
    rc = scorer.main(
        [
            "--handoff", str(tmp_path / "h.jsonl"),
            "--key", str(tmp_path / "k.jsonl"),
            "--out", str(tmp_path / "o.json"),
            "--rung", "rung-00100", "--arm", "v1", "--set", "3",
        ]
    )
    assert rc == 2
    assert "L11 decision 13" in capsys.readouterr().err


def test_refuses_a_key_outside_the_one_permitted_directory(scorer, tmp_path, monkeypatch, capsys):
    """A key anywhere else is a breach to DECLARE — decision 3 — not an input."""
    monkeypatch.delenv("CLAUDECODE", raising=False)
    monkeypatch.delenv("CLAUDE_CODE_SESSION_ID", raising=False)
    rc = scorer.main(
        [
            "--handoff", str(tmp_path / "h.jsonl"),
            "--key", str(tmp_path / "scratch-key.jsonl"),
            "--out", str(tmp_path / "o.json"),
            "--rung", "rung-00100", "--arm", "v1", "--set", "3",
        ]
    )
    assert rc == 2
    assert "breach" in capsys.readouterr().err


def test_a_malformed_key_line_never_reaches_the_error(scorer, tmp_path):
    """A traceback is the output channel wearing a different hat."""
    bad = tmp_path / "k.jsonl"
    bad.write_text('{"id": "q001", "primary": "docs/ALPHA-SECRET.md" \n', encoding="utf-8")
    with pytest.raises(SystemExit) as exc:
        scorer.read_jsonl(bad, redact=True)
    assert "ALPHA-SECRET" not in str(exc.value)
    assert "line 1" in str(exc.value)


# ── decision 13a (Arpit, 2026-09-28, W-168): per-tag pool COUNTS ──────────────
# The only key field it reads is `exercises`, and it publishes counts keyed by a
# tag NAME of a recipe's shape. Adding a pool field is an amendment, as above.
ALLOWED_POOL_FIELDS = {
    "tagged", "answerable", "miss@1", "reorderable@1", "miss@5", "reorderable@5", "not_in_top10",
}


def _pool_fixture():
    key = {
        "q1": {**SYNTHETIC_KEY, "id": "q1", "exercises": "step10_section"},
        "q2": {**SYNTHETIC_KEY, "id": "q2", "exercises": "step10_section"},
        "q3": {**SYNTHETIC_KEY, "id": "q3", "exercises": "step10_section", "answerable": False,
               "relevant": [], "primary": None},
        "q4": {**SYNTHETIC_KEY, "id": "q4", "exercises": "the quick brown fox SECRET-TAG"},
        "q5": {**SYNTHETIC_KEY, "id": "q5"},
    }
    rows = {
        # q1: hit at rank 1 · q2: target at rank 7 (reorderable) · q3: unanswerable
        "q1": {**SYNTHETIC_ROW, "id": "q1"},
        "q2": {**SYNTHETIC_ROW, "id": "q2", "ranked": [f"docs/x{i}.md" for i in range(6)] + ["docs/BETA-SECRET.md"]},
        "q3": {**SYNTHETIC_ROW, "id": "q3", "ranked": ["docs/x.md"]},
        "q4": {**SYNTHETIC_ROW, "id": "q4"},
        "q5": {**SYNTHETIC_ROW, "id": "q5"},
    }
    return rows, key


def test_pools_are_counts_under_a_recipe_tag_name(scorer):
    rows, key = _pool_fixture()
    pools = scorer.build_payload(rows, key, rung="r", arm="a", set_name="4-claude")["pools"]
    assert set(pools) == {"step10_section", "_unrecognised"}
    for p in pools.values():
        assert set(p) == ALLOWED_POOL_FIELDS
        assert all(isinstance(v, int) for v in p.values())
    assert pools["step10_section"] == {
        "tagged": 3, "answerable": 2, "miss@1": 1, "reorderable@1": 1,
        "miss@5": 1, "reorderable@5": 1, "not_in_top10": 0,
    }


def test_pools_echo_no_free_text_and_no_row_carries_a_tag(scorer):
    rows, key = _pool_fixture()
    payload = scorer.build_payload(rows, key, rung="r", arm="a", set_name="4-claude")
    blob = json.dumps(payload)
    for secret in ("SECRET-TAG", "quick brown fox", "ALPHA-SECRET", "BETA-SECRET"):
        assert secret not in blob
    for row in payload["rows"]:
        assert "exercises" not in row and set(row) <= ALLOWED_ROW_KEYS


# ── decision 13b (Arpit, 2026-09-28, W-168 step 7): per-question facet COUNTS ─
# The key's `facets` (SR-WORK-TESTDATA R8) is a list of document-name groups.
# The row carries how many groups exist and how many reach the top 5 — two ints.
FACET_KEY = {
    **SYNTHETIC_KEY,
    "facets": [
        ["docs/ALPHA-SECRET.md", "docs/GAMMA-SECRET.md"],
        ["docs/BETA-SECRET.md"],
        ["docs/DELTA-SECRET.md"],
        "the quick brown fox FACET-TEXT",  # malformed: not a group, not counted
        [],                                 # empty: not counted
    ],
}


def test_facets_are_two_counts_over_the_top_five(scorer):
    row = {**SYNTHETIC_ROW, "ranked": [
        "docs/ALPHA-SECRET.md", "docs/x1.md", "docs/x2.md", "docs/x3.md", "docs/x4.md",
        "docs/BETA-SECRET.md",  # rank 6: outside the top 5, so its facet is not covered
    ]}
    out = scorer.score_one(row, FACET_KEY)
    assert (out["facets_top5"], out["facets_key"]) == (1, 3)
    assert isinstance(out["facets_top5"], int) and isinstance(out["facets_key"], int)


def test_a_question_without_facets_scores_zero_zero(scorer):
    out = scorer.score_one(SYNTHETIC_ROW, SYNTHETIC_KEY)
    assert (out["facets_top5"], out["facets_key"]) == (0, 0)


def test_facets_echo_no_member_and_no_group_text(scorer):
    blob = json.dumps(scorer.score_one(SYNTHETIC_ROW, FACET_KEY))
    for secret in ("GAMMA-SECRET", "DELTA-SECRET", "FACET-TEXT", "quick brown fox"):
        assert secret not in blob
