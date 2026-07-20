"""skillgen: render fux's committed skill artifacts from edited fragments.

Build-time only. Nothing here ships in the wheel and nothing under
``tools/skillgen/`` is imported by the ``fux`` package at runtime. Fragments
under ``tools/skillgen/fragments/`` are the single source a human edits; the
rendered skill bodies (``fux/data/skills/fux/SKILL.md``,
``fux/data/skills/agents/SKILL.md``, ``fux/data/copilot/prompts/fux.prompt.md``)
are generated, committed artifacts. This module renders those artifacts and
guards them against drift.

Usage (from the repo root)::

    python -m tools.skillgen                 # regen every host's artifact
    python -m tools.skillgen --platform claude
    python -m tools.skillgen --check         # byte-diff render vs committed + expected/, exit 1 on drift
    python -m tools.skillgen --bless         # rewrite expected/ from the current render

The render is deterministic: the body template's per-host slots are filled in a
fixed order, output is LF-newline with exactly one trailing newline, and no
timestamp, version, or random value is ever written into a generated file. Same
fragments ⇒ byte-identical render.

This module is self-contained — no shared code with any other repo — to preserve
fux's standalone, zero-dependency guarantee. ``gen.py`` is stdlib-only
(``argparse``, ``re``, ``sys``, ``tomllib``).
"""
from __future__ import annotations

import argparse
import re
import sys
import tomllib  # Python 3.11+ stdlib
from dataclasses import dataclass
from pathlib import Path

# tools/skillgen/gen.py -> repo root is two parents up (skillgen -> tools -> root).
SKILLGEN_DIR = Path(__file__).resolve().parent
REPO_ROOT = SKILLGEN_DIR.parent.parent
FRAGMENTS_DIR = SKILLGEN_DIR / "fragments"
EXPECTED_DIR = SKILLGEN_DIR / "expected"
PLATFORMS_TOML = SKILLGEN_DIR / "platforms.toml"


@dataclass(frozen=True)
class Platform:
    """One render unit parsed from platforms.toml.

    The ``fux`` skill is single-body: each host renders exactly one artifact from
    its ``core`` fragment with the per-host slots filled. There is no split /
    references sidecar and no subagent dispatch (the ``fux`` skill fans out none).
    """

    key: str
    core: str  # body fragment basename under fragments/core/
    skill_dst: str  # rendered artifact path, relative to the repo root
    kind: str  # "skill" (name + quoted description) | "prompt" (agent + description)
    description: str  # frontmatter description, PRESERVED VERBATIM per platform
    name: str = "fux"  # frontmatter name (kind="skill")
    agent: str | None = None  # frontmatter agent (kind="prompt")
    pointer_file: str = "CLAUDE.md"  # @@POINTER_FILE@@ — the always-on pointer file


def load_platforms() -> dict[str, Platform]:
    """Parse platforms.toml into Platform records, keyed by platform name."""
    data = tomllib.loads(PLATFORMS_TOML.read_text(encoding="utf-8"))
    out: dict[str, Platform] = {}
    for key, cfg in data.get("platform", {}).items():
        if "description" not in cfg:
            raise ValueError(f"platform '{key}' is missing a description")
        out[key] = Platform(
            key=key,
            core=cfg["core"],
            skill_dst=cfg["skill_dst"],
            kind=cfg["kind"],
            description=cfg["description"],
            name=cfg.get("name", "fux"),
            agent=cfg.get("agent"),
            pointer_file=cfg.get("pointer_file", "CLAUDE.md"),
        )
    return out


def _normalise(text: str) -> str:
    """Force LF newlines and exactly one trailing newline."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    return text.rstrip("\n") + "\n"


def _read_fragment(rel: str) -> str:
    """Read a fragment file under fragments/, normalised to LF newlines."""
    return _normalise((FRAGMENTS_DIR / rel).read_text(encoding="utf-8"))


@dataclass(frozen=True)
class RenderedArtifact:
    """A single generated file: its repo-relative path and exact bytes."""

    path: str  # relative to REPO_ROOT
    content: str


def _render_frontmatter(platform: Platform) -> str:
    """Render the YAML frontmatter for this host.

    The ``description`` is the firing trigger — emitted VERBATIM from
    platforms.toml, never normalized. The surrounding YAML quoting is a property
    of the frontmatter *kind* (the host's convention), not an edit to the
    description text:

      - kind="skill"  -> name + double-quoted description (Agent Skills spec).
      - kind="prompt" -> agent + bare description (copilot .prompt.md convention).
    """
    if platform.kind == "skill":
        return "\n".join(
            ["---", f"name: {platform.name}", f'description: "{platform.description}"', "---"]
        )
    if platform.kind == "prompt":
        if platform.agent is None:
            raise ValueError(f"platform '{platform.key}' (kind=prompt) is missing an agent")
        return "\n".join(
            ["---", f"agent: {platform.agent}", f"description: {platform.description}", "---"]
        )
    raise ValueError(f"unknown frontmatter kind '{platform.kind}' for platform '{platform.key}'")


def _render_core(platform: Platform) -> str:
    """Fill the body template's per-host slots for this platform.

    Raises if any ``@@SLOT@@`` survives — a half-rendered file is never emitted.
    """
    template = _read_fragment(f"core/{platform.core}.md")
    body = (
        template.replace("@@FRONTMATTER@@", _render_frontmatter(platform))
        .replace("@@POINTER_FILE@@", platform.pointer_file)
    )
    if "@@" in body:
        leftover = sorted(set(re.findall(r"@@\w+@@", body)))
        raise ValueError(f"unfilled slots for '{platform.key}': {leftover}")
    return _normalise(body)


def render(platform: Platform) -> list[RenderedArtifact]:
    """Render the committed artifact(s) for one platform (single body for fux)."""
    return [RenderedArtifact(platform.skill_dst, _render_core(platform))]


def render_all(platforms: dict[str, Platform], only: str | None = None) -> list[RenderedArtifact]:
    """Render the selected platform (or all), flattened into one artifact list."""
    if only is not None and only not in platforms:
        raise SystemExit(
            f"error: unknown platform '{only}'. Known: {', '.join(sorted(platforms))}"
        )
    keys = [only] if only else sorted(platforms)
    out: list[RenderedArtifact] = []
    for key in keys:
        out.extend(render(platforms[key]))
    return out


def write_artifacts(artifacts: list[RenderedArtifact]) -> list[str]:
    """Write artifacts to disk under REPO_ROOT. Returns the paths written."""
    written: list[str] = []
    for art in artifacts:
        dst = REPO_ROOT / art.path
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(art.content, encoding="utf-8", newline="\n")
        written.append(art.path)
    return written


def _expected_path(rel: str) -> Path:
    """Map a repo-relative artifact path to its expected/ snapshot path.

    The artifact path is flattened (``/`` -> ``__``) into a single filename so the
    snapshot tree stays a flat, fully tracked dir with no nested ``skills/`` path
    component a .gitignore might catch.
    """
    return EXPECTED_DIR / rel.replace("/", "__")


def bless(artifacts: list[RenderedArtifact]) -> list[str]:
    """Write the current render into expected/ as the blessed snapshot."""
    written: list[str] = []
    for art in artifacts:
        dst = _expected_path(art.path)
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(art.content, encoding="utf-8", newline="\n")
        written.append(str(dst.relative_to(SKILLGEN_DIR)))
    return written


def check(artifacts: list[RenderedArtifact]) -> list[str]:
    """Byte-diff the render against both committed artifacts and expected/.

    Returns human-readable drift messages; empty list means clean. This is the
    anti-drift guard wired into CI and pre-commit: any hand-edit of a generated
    file, or a stale expected/ snapshot, is caught here.
    """
    problems: list[str] = []
    for art in artifacts:
        committed = REPO_ROOT / art.path
        if not committed.exists():
            problems.append(f"missing committed artifact: {art.path} (run: python -m tools.skillgen)")
        elif committed.read_text(encoding="utf-8") != art.content:
            problems.append(f"committed artifact out of date: {art.path} (run: python -m tools.skillgen)")

        snapshot = _expected_path(art.path)
        if not snapshot.exists():
            problems.append(f"missing expected/ snapshot: {art.path} (run: python -m tools.skillgen --bless)")
        elif snapshot.read_text(encoding="utf-8") != art.content:
            problems.append(f"expected/ snapshot out of date: {art.path} (run: python -m tools.skillgen --bless)")
    return problems


def headings(markdown: str) -> list[str]:
    """Return the ATX markdown headings in source order, ignoring code fences.

    A ``#``-prefixed line inside a fenced code block is a shell comment, not a
    heading, so fence state is tracked to avoid counting them. Used by the anchor
    test to assert each rendered body keeps its non-negotiable headings.
    """
    out: list[str] = []
    in_fence = False
    fence_marker = ""
    for line in markdown.splitlines():
        stripped = line.lstrip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            marker = stripped[:3]
            if not in_fence:
                in_fence, fence_marker = True, marker
            elif marker == fence_marker:
                in_fence, fence_marker = False, ""
            continue
        if in_fence:
            continue
        if stripped.startswith("#"):
            hashes = len(stripped) - len(stripped.lstrip("#"))
            if 1 <= hashes <= 6 and stripped[hashes:hashes + 1] == " ":
                out.append(stripped.strip())
    return out


def _parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="python -m tools.skillgen",
        description="Render and guard fux's committed skill artifacts.",
    )
    p.add_argument("--platform", help="render or check just this platform key")
    p.add_argument("--check", action="store_true", help="byte-diff render vs committed + expected/, exit 1 on drift")
    p.add_argument("--bless", action="store_true", help="rewrite expected/ from the current render")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv if argv is not None else sys.argv[1:])
    platforms = load_platforms()
    artifacts = render_all(platforms, only=args.platform)

    if args.check:
        problems = check(artifacts)
        if problems:
            print("check FAILED (skill artifacts have drifted):", file=sys.stderr)
            for m in problems:
                print(f"  {m}", file=sys.stderr)
            return 1
        print(f"check OK: {len(artifacts)} artifact(s) match committed output and expected/.")
        return 0

    if args.bless:
        written = bless(artifacts)
        print(f"blessed {len(written)} artifact(s) into expected/.")
        return 0

    written = write_artifacts(artifacts)
    print(f"rendered {len(written)} artifact(s):")
    for path in written:
        print(f"  {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
