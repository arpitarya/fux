"""`fux setup` never edits a consumer's workspace manifest — W-292 DoD 2.

Until 2026-10-21 setup detected a monorepo and spliced `.fux/node` into its root
`package.json` or `pnpm-workspace.yaml` (SR-NODE-SEARCH decision 15, now
superseded). This file asserted that wiring; it is rewritten to assert the
opposite, plus **the one removal that is still allowed**: taking out the entry
an earlier setup added, by the reverse splice, so the consumer's indentation,
key order, quoting and trailing newline survive the diff a team reviews.

A team that wants the Node reader in its workspace adds `fux-engine` to its own
manifest.
"""

from __future__ import annotations

import json

from fux.setup import WORKSPACE_MEMBER, run as setup_run
from fux.store import fuxdir


def _repo(tmp_path):
    (tmp_path / ".git").mkdir(exist_ok=True)
    return tmp_path


def _npm(tmp_path, manifest: str):
    (tmp_path / "package.json").write_text(manifest, encoding="utf-8")
    (tmp_path / "package-lock.json").write_text("{}", encoding="utf-8")
    return _repo(tmp_path)


MONO = '{\n  "name": "mono",\n  "private": true,\n  "workspaces": [\n    "packages/*"\n  ]\n}\n'


def test_setup_in_a_monorepo_edits_no_manifest(tmp_path):
    _npm(tmp_path, MONO)
    (tmp_path / "pnpm-workspace.yaml").write_text("packages:\n  - 'packages/*'\n", encoding="utf-8")
    report = setup_run(tmp_path, agents=False)
    assert (tmp_path / "package.json").read_text(encoding="utf-8") == MONO
    assert (tmp_path / "pnpm-workspace.yaml").read_text(encoding="utf-8") == "packages:\n  - 'packages/*'\n"
    assert report.unwired == []
    assert not (tmp_path / ".fux" / "node").exists()
    assert "package.json" not in report.written


def test_setup_removes_the_entry_an_earlier_setup_added(tmp_path):
    """The reverse of the old multi-line splice: the entry went in last and the
    element before it gained a comma, so both are undone."""
    _npm(tmp_path, '{\n  "name": "mono",\n  "private": true,\n  "workspaces": [\n'
                   '    "packages/*",\n    ".fux/node"\n  ]\n}\n')
    report = setup_run(tmp_path, agents=False)
    after = (tmp_path / "package.json").read_text(encoding="utf-8")
    assert after == MONO
    assert list(json.loads(after)) == ["name", "private", "workspaces"]
    assert report.unwired == ["package.json"]


def test_an_entry_in_the_middle_is_removed_cleanly(tmp_path):
    _npm(tmp_path, '{\n  "workspaces": [\n    "a",\n    ".fux/node",\n    "b"\n  ]\n}\n')
    setup_run(tmp_path, agents=False)
    assert (tmp_path / "package.json").read_text(encoding="utf-8") == (
        '{\n  "workspaces": [\n    "a",\n    "b"\n  ]\n}\n'
    )


def test_a_single_line_array_stays_on_one_line(tmp_path):
    _npm(tmp_path, '{\n  "workspaces": ["packages/*", ".fux/node"]\n}\n')
    setup_run(tmp_path, agents=False)
    assert (tmp_path / "package.json").read_text(encoding="utf-8") == (
        '{\n  "workspaces": ["packages/*"]\n}\n'
    )


def test_the_pnpm_list_loses_only_its_fux_line(tmp_path):
    (tmp_path / "pnpm-workspace.yaml").write_text(
        "packages:\n  - 'packages/*'\n  - '.fux/node'\n\nshamefullyHoist: true\n", encoding="utf-8"
    )
    report = setup_run(_repo(tmp_path), agents=False)
    assert (tmp_path / "pnpm-workspace.yaml").read_text(encoding="utf-8") == (
        "packages:\n  - 'packages/*'\n\nshamefullyHoist: true\n"
    )
    assert report.unwired == ["pnpm-workspace.yaml"]


def test_the_pnpm_flow_form_is_unwired_too(tmp_path):
    (tmp_path / "pnpm-workspace.yaml").write_text(
        'packages: ["packages/*", ".fux/node"]\n', encoding="utf-8"
    )
    setup_run(_repo(tmp_path), agents=False)
    assert (tmp_path / "pnpm-workspace.yaml").read_text(encoding="utf-8") == 'packages: ["packages/*"]\n'


def test_a_manifest_that_never_named_fux_is_untouched_byte_for_byte(tmp_path):
    odd = '{\n\t"workspaces": [ "x" ,"y" ],\n\t"name": "z"\n}'
    _npm(tmp_path, odd)
    setup_run(tmp_path, agents=False)
    assert (tmp_path / "package.json").read_text(encoding="utf-8") == odd


def test_an_ingest_never_edits_the_consumers_manifest(tmp_path):
    """⚠ **Asserted where it could be violated.** `ensure_layout` runs at the
    head of every ingest; even a leftover entry stays until `fux setup`."""
    wired = '{\n  "workspaces": ["packages/*", ".fux/node"]\n}\n'
    _npm(tmp_path, wired)
    fuxdir.ensure_layout(tmp_path)
    assert (tmp_path / "package.json").read_text(encoding="utf-8") == wired


def test_the_member_is_the_path_the_old_setup_wrote():
    assert WORKSPACE_MEMBER == ".fux/node"
