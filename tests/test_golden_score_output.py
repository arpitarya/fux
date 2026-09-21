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
