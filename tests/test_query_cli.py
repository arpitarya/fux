"""ask / find / answer through the CLI boundary (error contract + output modes)."""

from __future__ import annotations

import json

from fux.cli import main


def make_corpus(tmp_path):
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "deploy.md").write_text(
        "# Deploy\n\n## Rollout\n\n"
        "The deploy uses a blue-green rollout with health checks before cutover.\n"
        "Rollbacks complete within two minutes when checks fail.\n",
        encoding="utf-8",
    )
    (tmp_path / "docs" / "style.md").write_text(
        "# Style\n\nWe indent with four spaces and never use tabs anywhere.\n",
        encoding="utf-8",
    )
    (tmp_path / "fux.toml").write_text('[sources]\ndocs = ["docs"]\n', encoding="utf-8")


def run(tmp_path, monkeypatch, *argv):
    monkeypatch.chdir(tmp_path)
    return main(list(argv))


def test_no_config_exit_one(tmp_path, monkeypatch, capsys):
    assert run(tmp_path, monkeypatch, "ask", "anything") == 1
    assert "fux setup" in capsys.readouterr().err


def test_no_index_points_to_ingest(tmp_path, monkeypatch, capsys):
    (tmp_path / "fux.toml").write_text("[sources]\ndocs = []\n", encoding="utf-8")
    assert run(tmp_path, monkeypatch, "ask", "anything") == 1
    assert "fux ingest" in capsys.readouterr().err


def test_ask_human_output(tmp_path, monkeypatch, capsys):
    make_corpus(tmp_path)
    run(tmp_path, monkeypatch, "ingest")
    capsys.readouterr()
    assert run(tmp_path, monkeypatch, "ask", "how does the deploy rollout work") == 0
    out = capsys.readouterr().out
    assert "docs/deploy.md:1  (score " in out
    assert "blue-green" in out
    assert "passage" in out and "corpus 2 docs" in out  # footer per cli-examples.md


def test_ask_json_with_explain(tmp_path, monkeypatch, capsys):
    make_corpus(tmp_path)
    run(tmp_path, monkeypatch, "ingest")
    capsys.readouterr()
    assert run(tmp_path, monkeypatch, "ask", "deploy rollout", "--json", "--explain") == 0
    payload = json.loads(capsys.readouterr().out)
    top = payload["results"][0]
    assert top["path"] == "docs/deploy.md"
    assert top["line_start"] >= 1 and top["line_end"] >= top["line_start"]
    assert top["fidelity"] == "inferred"
    assert top["explain"][0]["term"] in ("deploy", "rollout")
    assert payload["engine"] == "bm25f" and payload["corpus"]["docs"] == 2


def test_find_ranks_files(tmp_path, monkeypatch, capsys):
    make_corpus(tmp_path)
    run(tmp_path, monkeypatch, "ingest")
    capsys.readouterr()
    assert run(tmp_path, monkeypatch, "find", "indent tabs style", "--json") == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["results"][0]["path"] == "docs/style.md"


def test_answer_cited_and_extractive(tmp_path, monkeypatch, capsys):
    make_corpus(tmp_path)
    run(tmp_path, monkeypatch, "ingest")
    capsys.readouterr()
    assert run(tmp_path, monkeypatch, "answer", "how fast are rollbacks") == 0
    out = capsys.readouterr().out
    assert "two minutes" in out and "[1]" in out
    assert "Sources:" in out and "[1] docs/deploy.md:" in out
    assert "(extractive — sentences are verbatim from sources)" in out


def test_answer_json_sentences(tmp_path, monkeypatch, capsys):
    make_corpus(tmp_path)
    run(tmp_path, monkeypatch, "ingest")
    capsys.readouterr()
    assert run(tmp_path, monkeypatch, "answer", "rollout health checks", "--json") == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["answer"]
    assert payload["sentences"][0]["path"] == "docs/deploy.md"
    assert payload["sources"][0]["id"] == 1


def test_zero_hits_honest_exit_zero(tmp_path, monkeypatch, capsys):
    make_corpus(tmp_path)
    run(tmp_path, monkeypatch, "ingest")
    capsys.readouterr()
    assert run(tmp_path, monkeypatch, "ask", "zzz qqq xyzzy") == 0
    assert "No confident matches" in capsys.readouterr().out
    assert run(tmp_path, monkeypatch, "answer", "zzz qqq xyzzy") == 0
    assert "No confident answer" in capsys.readouterr().out


def test_stale_cache_warns_on_ask(tmp_path, monkeypatch, capsys):
    make_corpus(tmp_path)
    run(tmp_path, monkeypatch, "ingest")
    (tmp_path / "docs" / "deploy.md").write_text("# Changed a lot now\n", encoding="utf-8")
    capsys.readouterr()
    run(tmp_path, monkeypatch, "ask", "deploy")
    assert "sources changed" in capsys.readouterr().err
