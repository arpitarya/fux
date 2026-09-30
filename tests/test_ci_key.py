"""The FULL-stage verdict key — `scripts/ci-key.py`, SR-WORK-RELEASE decision 14.

The executable twin, in `test_version_parity.py`'s shape: the script is the
implementation, this makes its promises run on every push.

🔴 **What a wrong key costs is asymmetric, and the tests lean on that.** A key
that moves when it need not costs a FULL run. A key that does NOT move when
code changed lets FULL skip on a verdict about different code — a release gate
reading green for something nobody tested. So every test here is about the
second kind.
"""

from __future__ import annotations

import importlib.util
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent

_spec = importlib.util.spec_from_file_location("ci_key", ROOT / "scripts" / "ci-key.py")
ci_key = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(ci_key)

WORKFLOWS = ROOT / ".github" / "workflows"


@pytest.mark.parametrize("path", [
    "work/WORKLOG.md", "work/regression/x/evidence/rows.jsonl", "docs/index.md",
    "CHANGELOG.md", "README.md", "CLAUDE.md", "records/0063_WORK-release.md",
    ".claude/skills/fux-usage/SKILL.md",
])
def test_inert_paths(path: str) -> None:
    assert ci_key.inert(path)


@pytest.mark.parametrize("path", [
    # Markdown a test or `fux setup` reads byte-for-byte is code.
    "src/fux/templates/agents/INSPECT-SKILL.md", "node/README.md",
    "tests/fixtures/doc.md", "tests_e2e/fixtures/a.md",
    # The committed index is the arm's corpus.
    ".fux/index/00.jsonl", ".fux/tune.toml",
    # Not Markdown, so not inert, even beside Markdown.
    "records/RULE-SINCE", ".github/workflows/ci.yml", "scripts/ci-key.py",
    # 🔴 The exclude-list promise: a folder nobody has heard of is code.
    "brand-new-folder/thing.py", "brand-new-folder/notes.txt",
])
def test_code_paths(path: str) -> None:
    assert not ci_key.inert(path)


def _repo(tmp_path: Path) -> Path:
    def git(*a: str) -> None:
        subprocess.run(["git", *a], cwd=tmp_path, check=True, capture_output=True)

    git("init", "-q")
    git("config", "user.email", "t@t")
    git("config", "user.name", "t")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "a.py").write_text("x = 1\n")
    (tmp_path / "work").mkdir()
    (tmp_path / "work" / "log.md").write_text("one\n")
    git("add", "-A")
    git("commit", "-qm", "one")
    return tmp_path


def _commit(root: Path, rel: str, text: str) -> None:
    (root / rel).parent.mkdir(parents=True, exist_ok=True)
    (root / rel).write_text(text)
    subprocess.run(["git", "add", "-A"], cwd=root, check=True)
    subprocess.run(["git", "commit", "-qm", rel], cwd=root, check=True)


def test_an_inert_commit_keeps_the_key_and_a_code_commit_moves_it(tmp_path, monkeypatch) -> None:
    root = _repo(tmp_path)
    monkeypatch.chdir(root)
    before = ci_key.tree_digest()
    _commit(root, "work/log.md", "two\n")
    assert ci_key.tree_digest() == before
    _commit(root, "src/a.py", "x = 2\n")
    assert ci_key.tree_digest() != before


def test_a_new_top_level_folder_moves_the_key(tmp_path, monkeypatch) -> None:
    root = _repo(tmp_path)
    monkeypatch.chdir(root)
    before = ci_key.tree_digest()
    _commit(root, "newdir/x.txt", "hi\n")
    assert ci_key.tree_digest() != before


def test_a_mode_change_moves_the_key(tmp_path, monkeypatch) -> None:
    """A hook committed 100644 cannot launch (W-230) — that IS a verdict change."""
    root = _repo(tmp_path)
    monkeypatch.chdir(root)
    before = ci_key.tree_digest()
    subprocess.run(["git", "update-index", "--chmod=+x", "src/a.py"], cwd=root, check=True)
    subprocess.run(["git", "commit", "-qm", "mode"], cwd=root, check=True)
    assert ci_key.tree_digest() != before


def test_the_cell_key_carries_the_cell_and_the_runtime(tmp_path, monkeypatch) -> None:
    root = _repo(tmp_path)
    monkeypatch.chdir(root)
    a = ci_key.cell_key("py-windows-latest-3.12")
    assert a.startswith(f"{ci_key.SCHEMA}-") and "-py-windows-latest-3.12-" in a
    assert ci_key.cell_key("py-windows-latest-3.14") != a
    monkeypatch.setenv("ImageVersion", "20990101.1")
    assert ci_key.cell_key("py-windows-latest-3.12") != a


def test_every_full_job_goes_through_the_verdict_and_saves_only_its_own_key() -> None:
    ci = (WORKFLOWS / "ci.yml").read_text(encoding="utf-8")
    for job in ("  python:\n", "  node-arm:\n"):
        body = ci.split(job, 1)[1].split("\n  verdict:\n", 1)[0].split("\n  node-arm:\n", 1)[0]
        assert "uses: ./.github/actions/full-verdict" in body, job
        assert "actions/cache/save@v4" in body, job
        # Every `run:` step after the lookup must be guarded by the hit.
        steps = body.split("id: verdict", 1)[1].split("\n      - ")
        for step in steps[1:]:
            if "run:" in step or "setup-fux" in step:
                assert "steps.verdict.outputs.hit != 'true'" in step, f"{job}: unguarded step\n{step}"


def test_only_a_push_reads_a_verdict() -> None:
    """Nightly and dispatch always run FULL whole — the backstop the key needs."""
    action = (ROOT / ".github" / "actions" / "full-verdict" / "action.yml").read_text(encoding="utf-8")
    lookup = action.split("id: lookup", 1)[1]
    assert "if: github.event_name == 'push'" in lookup
    assert "lookup-only: true" in lookup


def test_the_aggregate_verdict_needs_every_job() -> None:
    ci = (WORKFLOWS / "ci.yml").read_text(encoding="utf-8")
    body = ci.split("\n  verdict:\n", 1)[1]
    assert "needs: [unit, e2e, build, arm, python, node-arm]" in body
    assert "scripts/ci-key.py verdict" in body


def test_publish_reads_the_same_key_the_verdict_job_saves() -> None:
    publish = (WORKFLOWS / "publish.yml").read_text(encoding="utf-8")
    assert "python3 scripts/ci-key.py verdict" in publish
    assert "refusing to publish" in publish
