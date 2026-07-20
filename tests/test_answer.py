"""Extractive answer selection: overlap + TextRank + ordering + citations."""

from __future__ import annotations

from fux.index.bm25f import ScoredChunk
from fux.query.answer import build_answer, _sentences, _textrank


def chunk(file, text, score, start=10):
    return ScoredChunk(
        file=file, heading="H", text=text, start=start, end=start + 5, score=score
    )


def test_picks_question_relevant_sentence():
    results = [
        chunk(
            "docs/a.md",
            "The deploy uses blue-green rollout for safety reasons.\n"
            "Lunch is served at noon in the cafeteria every day.",
            5.0,
        )
    ]
    out = build_answer(results, "how does the deploy rollout work", 1)
    assert len(out) == 1
    assert "blue-green" in out[0].text
    assert out[0].file == "docs/a.md"
    assert out[0].line == 10  # first line of the chunk


def test_document_order_restored_and_cited():
    results = [
        chunk("docs/b.md", "Beta topic covers the install steps in detail.", 4.0, start=50),
        chunk("docs/a.md", "Alpha topic explains the install prerequisites fully.", 5.0, start=5),
    ]
    out = build_answer(results, "install", 2)
    assert [s.file for s in out] == ["docs/a.md", "docs/b.md"]  # doc order, not score order
    assert out[0].line == 5 and out[1].line == 50


def test_duplicate_sentences_deduped():
    text = "The retry limit is three attempts total."
    results = [chunk("a.md", text, 5.0), chunk("b.md", text, 4.0)]
    out = build_answer(results, "retry limit", 5)
    assert len(out) == 1


def test_max_sentences_respected():
    text = "\n\n".join(f"Sentence number {i} talks about widgets today." for i in range(10))
    out = build_answer([chunk("a.md", text, 5.0)], "widgets", 3)
    assert len(out) == 3


def test_empty_results_empty_answer():
    assert build_answer([], "anything", 5) == []


def test_low_relevance_noise_excluded():
    results = [
        chunk("a.md", "Rollbacks complete within two minutes when checks fail.", 5.0),
        chunk("b.md", "The cafeteria menu rotates weekly with seasonal dishes.", 0.6),
    ]
    out = build_answer(results, "how fast are rollbacks", 5)
    assert [s.file for s in out] == ["a.md"]  # noise falls under the keep floor


def test_stopwords_do_not_create_overlap():
    results = [
        chunk("a.md", "Rollbacks complete within two minutes when checks fail.", 5.0),
        chunk("b.md", "These are the things that are how they are.", 4.9),
    ]
    out = build_answer(results, "how fast are the rollbacks", 5)
    assert out and out[0].file == "a.md"
    assert all("cafeteria" not in s.text for s in out)


def test_sentences_skip_fences_tables_headings():
    text = (
        "# Heading\n"
        "```py\ncode_line = 1\n```\n"
        "| a | b |\n"
        "A real prose sentence lives right here.\n"
        "- A bullet sentence also counts as prose."
    )
    sents = [t for t, _ in _sentences(text)]
    assert sents == [
        "A real prose sentence lives right here.",
        "A bullet sentence also counts as prose.",
    ]


def test_sentence_line_numbers():
    text = "First line sentence is right here.\nSecond line sentence follows right after."
    sents = list(_sentences(text))
    assert sents[0][1] == 1 and sents[1][1] == 2


def test_wrapped_sentence_keeps_first_line():
    text = "This sentence wraps across two\nphysical lines before it ends."
    sents = list(_sentences(text))
    assert len(sents) == 1 and sents[0][1] == 1


def test_textrank_deterministic_and_normalized():
    sets = [
        {"deploy", "rollout", "safety"},
        {"deploy", "rollout", "steps"},
        {"lunch", "cafeteria", "noon"},
    ]
    a = _textrank(sets)
    b = _textrank(sets)
    assert a == b
    assert max(a) == 1.0
    assert a[0] > a[2]  # connected sentences outrank the isolated one
