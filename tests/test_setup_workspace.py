"""`fux setup` detects a monorepo and wires `.fux/node` into it.

Ruled by Arpit 2026-09-12 — *"Auto detect. Auto detect and set it up as well."*
— and recorded as ADR-NODE-SEARCH decision 15. The detection table and the
`.fux/node` dot-path are **measured**, in
[`2026-09-12-workspace-dotpath-probe`](../work/regression/2026-09-12-workspace-dotpath-probe/report.md):
npm, pnpm, yarn 1 and bun all link it when it is declared, and **none** of the
four picks it up from a `packages/*` glob — which is what makes the wiring
required rather than convenient.

**What these tests are really guarding is somebody else's file.** This is the
first place fux writes to a manifest a team reviews, so the assertions are
about the DIFF as much as the result: existing indentation, key order and the
trailing newline survive, the edit is idempotent, and anything fux cannot
change safely leaves the file alone and falls back to the offline shape.
"""

from __future__ import annotations

import json

from fux.setup import (
    WORKSPACE_MEMBER,
    detect_workspace,
    run as setup_run,
    wire_workspace,
)
from fux.store import fuxdir


def _repo(tmp_path):
    (tmp_path / ".git").mkdir(exist_ok=True)
    return tmp_path


def _npm(tmp_path, manifest: str = None):
    (tmp_path / "package.json").write_text(
        manifest or '{\n  "name": "mono",\n  "private": true,\n  "workspaces": [\n    "packages/*"\n  ]\n}\n',
        encoding="utf-8",
    )
    (tmp_path / "package-lock.json").write_text("{}", encoding="utf-8")
    return _repo(tmp_path)


# --------------------------------------------------------------------------
# detection


def test_no_monorepo_means_no_workspace(tmp_path):
    assert detect_workspace(_repo(tmp_path)) is None


def test_a_plain_package_json_is_not_a_monorepo(tmp_path):
    """A `package.json` with no `workspaces` key is a project, not a workspace
    root. Wiring one would add a key fux made up."""
    (tmp_path / "package.json").write_text('{"name": "app"}\n', encoding="utf-8")
    assert detect_workspace(_repo(tmp_path)) is None


def test_an_npm_workspaces_array_is_detected(tmp_path):
    found = detect_workspace(_npm(tmp_path))
    assert found is not None
    assert (found.kind, found.manager) == ("package-json", "npm")


def test_pnpm_wins_over_package_json(tmp_path):
    """First hit wins, and pnpm keeps its list in its own file."""
    (tmp_path / "pnpm-workspace.yaml").write_text("packages:\n  - 'packages/*'\n", encoding="utf-8")
    found = detect_workspace(_npm(tmp_path))
    assert found is not None
    assert found.manifest.name == "pnpm-workspace.yaml"
    assert found.kind == "pnpm-yaml"


def _berry(tmp_path, rc: str):
    (tmp_path / "package.json").write_text(
        '{\n  "name": "berry",\n  "packageManager": "yarn@4.1.0",\n  "workspaces": ["packages/*"]\n}\n',
        encoding="utf-8",
    )
    (tmp_path / ".yarnrc.yml").write_text(rc, encoding="utf-8")
    return _repo(tmp_path)


def test_yarn_berry_under_pnp_is_detected_but_NOT_wired(tmp_path):
    """🔴 **MEASURED, not assumed** ([probe 2](../work/regression/2026-09-12-yarn-berry-probe/report.md)).

    Yarn 4.1.0 links `.fux/node` happily — the dot path was never the problem
    in Berry either. What PnP has is **no `node_modules` anywhere**, so neither
    of the shim's install rungs can resolve a binary, and shape A is both
    correct and offline. Berry's default linker IS PnP, so an unset key takes
    this path.

    🔴 **And the order this is checked in is not the order decision 15's table
    was written in, because the table was wrong.** A Berry repository declares
    `workspaces` in `package.json` exactly like npm does, so a literal
    first-hit reading of that table gave every Berry repo shape C — including
    the PnP ones the record's own warning says must not have it.
    """
    found = detect_workspace(_berry(tmp_path, "nodeLinker: pnp\n"))
    assert found is not None and found.kind == "yarn-pnp"
    wired, refusal = wire_workspace(tmp_path, found)
    assert wired is False
    assert "PnP" in refusal and "node_modules" in refusal


def test_berry_with_no_linker_key_is_treated_as_PnP(tmp_path):
    """Berry's own default. Guessing the convenient answer here would wire a
    workspace whose reader nothing can resolve."""
    found = detect_workspace(_berry(tmp_path, "enableGlobalCache: true\n"))
    assert found is not None and found.kind == "yarn-pnp"


def test_berry_with_the_node_modules_linker_GETS_shape_C(tmp_path):
    """Measured: `nodeLinker: node-modules` hoists `fux` to the workspace root's
    `node_modules/.bin`, which is the shim's third rung — the same place npm and
    yarn 1 put it. So Berry is not excluded as a manager; PnP is excluded as a
    layout."""
    found = detect_workspace(_berry(tmp_path, "nodeLinker: node-modules\n"))
    assert found is not None and found.kind == "package-json"
    wired, refusal = wire_workspace(tmp_path, found)
    assert (wired, refusal) == (True, None)
    assert WORKSPACE_MEMBER in json.loads(
        (tmp_path / "package.json").read_text(encoding="utf-8")
    )["workspaces"]


def test_the_object_form_of_workspaces_is_not_edited_by_guess(tmp_path):
    (tmp_path / "package.json").write_text(
        '{\n  "packageManager": "yarn@4.1.0",\n  "workspaces": {"packages": ["packages/*"]}\n}\n',
        encoding="utf-8",
    )
    (tmp_path / ".yarnrc.yml").write_text("nodeLinker: node-modules\n", encoding="utf-8")
    found = detect_workspace(_repo(tmp_path))
    assert found is not None and found.kind == "yarn-object-form"
    wired, refusal = wire_workspace(tmp_path, found)
    assert wired is False and "object" in refusal


# --------------------------------------------------------------------------
# the edit itself


def test_the_edit_preserves_indentation_key_order_and_the_newline(tmp_path):
    before = '{\n  "name": "mono",\n  "private": true,\n  "workspaces": [\n    "packages/*"\n  ]\n}\n'
    _npm(tmp_path, before)
    wired, refusal = wire_workspace(tmp_path, detect_workspace(tmp_path))
    after = (tmp_path / "package.json").read_text(encoding="utf-8")
    assert (wired, refusal) == (True, None)
    assert after == (
        '{\n  "name": "mono",\n  "private": true,\n  "workspaces": [\n'
        '    "packages/*",\n    ".fux/node"\n  ]\n}\n'
    )
    assert list(json.loads(after)) == ["name", "private", "workspaces"]


def test_a_single_line_array_stays_on_one_line(tmp_path):
    _npm(tmp_path, '{\n  "workspaces": ["packages/*"]\n}\n')
    wire_workspace(tmp_path, detect_workspace(tmp_path))
    assert (tmp_path / "package.json").read_text(encoding="utf-8") == (
        '{\n  "workspaces": ["packages/*", ".fux/node"]\n}\n'
    )


def test_wiring_twice_adds_one_entry(tmp_path):
    """Idempotent — `fux setup` is run again on every upgrade."""
    _npm(tmp_path)
    for _ in range(3):
        wire_workspace(tmp_path, detect_workspace(tmp_path))
    listed = json.loads((tmp_path / "package.json").read_text(encoding="utf-8"))["workspaces"]
    assert listed.count(WORKSPACE_MEMBER) == 1


def test_json_with_comments_is_left_alone(tmp_path):
    """Half-configured is not a state (constraint 4): if the file cannot be
    edited by splice, fux does not guess — it writes shape A and says why."""
    before = '{\n  // our workspaces\n  "workspaces": ["packages/*"]\n}\n'
    _npm(tmp_path, before)
    found = detect_workspace(tmp_path)
    assert found is not None
    wired, refusal = wire_workspace(tmp_path, found)
    assert wired is False
    assert "not plain JSON" in refusal
    assert (tmp_path / "package.json").read_text(encoding="utf-8") == before


def test_a_read_only_manifest_is_left_alone(tmp_path):
    import os
    import stat

    _npm(tmp_path)
    manifest = tmp_path / "package.json"
    before = manifest.read_text(encoding="utf-8")
    manifest.chmod(stat.S_IRUSR)
    try:
        if os.access(manifest, os.W_OK):  # running as root, or a permissive FS
            import pytest

            pytest.skip("this filesystem does not enforce read-only for this user")
        wired, refusal = wire_workspace(tmp_path, detect_workspace(tmp_path))
    finally:
        manifest.chmod(stat.S_IRUSR | stat.S_IWUSR)
    assert wired is False and "read-only" in refusal
    assert manifest.read_text(encoding="utf-8") == before


def test_the_pnpm_list_keeps_its_quoting_style(tmp_path):
    (tmp_path / "pnpm-workspace.yaml").write_text(
        "packages:\n  - 'packages/*'\n\nshamefullyHoist: true\n", encoding="utf-8"
    )
    _repo(tmp_path)
    wire_workspace(tmp_path, detect_workspace(tmp_path))
    assert (tmp_path / "pnpm-workspace.yaml").read_text(encoding="utf-8") == (
        "packages:\n  - 'packages/*'\n  - '.fux/node'\n\nshamefullyHoist: true\n"
    )


# --------------------------------------------------------------------------
# end to end, through `fux setup`


def test_setup_in_a_monorepo_writes_shape_C_and_says_what_it_edited(tmp_path):
    report = setup_run(_npm(tmp_path), agents=False)
    assert report.node_shape == fuxdir.SHAPE_WORKSPACE
    assert report.wired_manifest == "package.json"
    assert report.workspace_manager == "npm"
    target = tmp_path / ".fux" / "node"
    assert {p.name for p in target.iterdir()} == {"package.json"}
    assert WORKSPACE_MEMBER in json.loads(
        (tmp_path / "package.json").read_text(encoding="utf-8")
    )["workspaces"]


def test_setup_outside_a_monorepo_writes_shape_A_and_edits_nothing(tmp_path):
    report = setup_run(_repo(tmp_path), agents=False)
    assert report.node_shape == fuxdir.SHAPE_VENDORED
    assert report.wired_manifest is None
    assert report.workspace_note is None
    assert (tmp_path / ".fux" / "node" / "fux.mjs").is_file()


def test_an_ingest_never_edits_the_consumers_manifest(tmp_path):
    """⚠ **Constraint 1, asserted where it can actually be violated.**
    `ensure_layout` runs at the head of every ingest; an ingest that rewrote
    `package.json` would turn a no-op run into a dirty tree.
    """
    _npm(tmp_path)
    before = (tmp_path / "package.json").read_text(encoding="utf-8")
    fuxdir.ensure_layout(tmp_path)
    assert (tmp_path / "package.json").read_text(encoding="utf-8") == before
    assert fuxdir.node_shape(tmp_path / ".fux") == fuxdir.SHAPE_VENDORED
