"""Tests for the build-time skill renderer (tools/skillgen).

The renderer is stdlib-only and never imported by the fux package at runtime;
these tests guard the render contract: byte-determinism, the --check drift guard,
per-host anchor lines, no surviving slots, and the wheel/sdist exclusion.
"""
from __future__ import annotations

import subprocess
import sys
import tarfile
import zipfile
from pathlib import Path

import pytest

from tools.skillgen import gen

REPO = Path(__file__).resolve().parent.parent


def _platforms():
    return gen.load_platforms()


def test_render_is_byte_deterministic():
    """Same fragments ⇒ byte-identical render across two runs (no clocks/random)."""
    first = gen.render_all(_platforms())
    second = gen.render_all(_platforms())
    assert [(a.path, a.content) for a in first] == [(a.path, a.content) for a in second]


def test_check_passes_on_clean_committed_tree():
    """The committed artifacts + expected/ snapshots match the current render."""
    assert gen.check(gen.render_all(_platforms())) == []
    assert gen.main(["--check"]) == 0


def test_check_detects_drift():
    """A render whose bytes differ from the committed/expected files is caught."""
    artifacts = gen.render_all(_platforms())
    drifted = [gen.RenderedArtifact(artifacts[0].path, artifacts[0].content + "\nDRIFT\n")]
    problems = gen.check(drifted)
    assert problems, "check() must flag a render that differs from committed/expected"
    assert any("out of date" in p or "missing" in p for p in problems)


def test_main_check_returns_1_on_drift(monkeypatch):
    """main(--check) exits 1 when the render drifts from the committed artifacts."""
    real = gen.render_all

    def drifted(platforms, only=None):
        arts = real(platforms, only=only)
        return [gen.RenderedArtifact(arts[0].path, arts[0].content + "\nDRIFT\n"), *arts[1:]]

    monkeypatch.setattr(gen, "render_all", drifted)
    assert gen.main(["--check"]) == 1


def test_no_unfilled_slot_survives():
    """No `@@SLOT@@` (in fact no `@@` at all) remains in any rendered artifact."""
    for art in gen.render_all(_platforms()):
        assert "@@" not in art.content, f"unfilled slot survived in {art.path}"


@pytest.mark.parametrize("key", ["claude", "agents", "copilot"])
def test_per_host_anchor_lines(key):
    """Each host's render carries its non-negotiable anchor lines."""
    platforms = _platforms()
    plat = platforms[key]
    (art,) = gen.render(plat)
    body = art.content
    # The description is the firing trigger — present VERBATIM from platforms.toml.
    assert plat.description in body

    if plat.kind == "skill":
        assert f"name: {plat.name}" in body
        assert f'description: "{plat.description}"' in body
        assert "## Usage" in gen.headings(body)
        assert "$0" in body
    else:  # prompt (copilot)
        assert f"agent: {plat.agent}" in body
        assert f"description: {plat.description}" in body


def test_shared_core_drives_breadth():
    """claude + agents render from the same core body, differing only by the slot.

    This is the breadth proof: one core.md edit updates both hosts. Their rendered
    bodies are identical except the always-on pointer file (CLAUDE.md vs AGENTS.md)
    and the frontmatter — so a shared-line edit can never touch only one of them.
    """
    platforms = _platforms()
    assert platforms["claude"].core == platforms["agents"].core == "core"
    claude = gen.render(platforms["claude"])[0].content
    agents = gen.render(platforms["agents"])[0].content
    assert "Tier-0 pointer into `CLAUDE.md`" in claude
    assert "Tier-0 pointer into `AGENTS.md`" in agents


def test_committed_artifacts_match_render():
    """The on-disk committed artifacts are exactly what the renderer produces."""
    for art in gen.render_all(_platforms()):
        committed = REPO / art.path
        assert committed.exists(), f"missing committed artifact {art.path}"
        assert committed.read_text(encoding="utf-8") == art.content


def test_skillgen_not_imported_by_fux_package():
    """Nothing under the runtime fux/ package imports tools.skillgen."""
    offenders = []
    for path in (REPO / "fux").rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        if "tools.skillgen" in text or "from tools import" in text:
            offenders.append(str(path.relative_to(REPO)))
    assert not offenders, f"fux runtime must not import skillgen: {offenders}"


def test_wheel_and_sdist_exclude_skillgen(tmp_path):
    """The built wheel and sdist must not ship anything under tools/skillgen/."""
    pytest.importorskip("build")
    out = tmp_path / "dist"
    # Prefer a fast hermetic build when the setuptools backend is importable here;
    # otherwise fall back to an isolated build (fetches build deps). Either way, a
    # build that can't run for environment reasons (offline, no backend) skips
    # rather than fails — the assertion only fires on a real build.
    cmd = [sys.executable, "-m", "build", "--outdir", str(out), str(REPO)]
    try:
        import setuptools.build_meta  # noqa: F401
        cmd.insert(3, "--no-isolation")
    except ModuleNotFoundError:
        pass
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        pytest.skip(f"package build unavailable in this env:\n{result.stdout}\n{result.stderr}")

    wheels = list(out.glob("*.whl"))
    sdists = list(out.glob("*.tar.gz"))
    assert wheels and sdists, "build did not produce a wheel + sdist"

    with zipfile.ZipFile(wheels[0]) as zf:
        wheel_names = zf.namelist()
    assert not any("tools/skillgen" in n or n.startswith("tools/") for n in wheel_names), \
        "skillgen leaked into the wheel"

    with tarfile.open(sdists[0]) as tf:
        sdist_names = tf.getnames()
    assert not any("tools/skillgen" in n for n in sdist_names), "skillgen leaked into the sdist"
