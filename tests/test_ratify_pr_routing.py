"""`fux ratify` routes a ratification through a new branch + gated PR (§2g).

Deterministic git/gh only — these tests assert the *guard* logic (when the PR
path is skipped) without hitting the network: no remote / --no-pr / feature
branch all leave the on-disk ratification standing and never commit to the
protected branch.
"""
from __future__ import annotations

import subprocess
from types import SimpleNamespace

from fux import cliconstitution, config, constitution, gitutil, loader, paths
from conftest import write_rule

CON = """---
id: con-pr
type: rule
status: active
tier: constitutional
---
**Rule:** money docs are never committed; plans live in elgar.
"""


def _git(root, *args):
    subprocess.run(["git", *args], cwd=root, check=True,
                   capture_output=True, text=True)


def _ratify_rule(project, rid):
    cfg = config.load(paths.Footprint(project).config)
    rules = loader.resolve(project, cfg).rules
    return constitution.ratify(project, rules, rid, by="Arpit", date="2026-06-18")


def test_no_pr_flag_skips_routing(project):
    write_rule(project, "con-pr", CON)
    r = _ratify_rule(project, "con-pr")
    # --no-pr → in-place ratify, no branch switch attempted.
    rc = cliconstitution._route_through_pr(project, r, "Arpit", "2026-06-18", no_pr=True)
    assert rc == 0
    # still on whatever branch we started on (no constitution/* created)
    assert gitutil.current_branch(project) != "constitution/con-pr"


def test_no_remote_skips_routing(project):
    write_rule(project, "con-pr", CON)
    _git(project, "init", "-q")
    _git(project, "config", "user.email", "t@t")
    _git(project, "config", "user.name", "t")
    _git(project, "add", "-A")
    _git(project, "commit", "-qm", "init")
    r = _ratify_rule(project, "con-pr")
    # repo but no remote → no-op (can't open a PR; on-disk ratify stands).
    assert not gitutil.has_remote(project)
    rc = cliconstitution._route_through_pr(project, r, "Arpit", "2026-06-18", no_pr=False)
    assert rc == 0
    assert gitutil.current_branch(project) != "constitution/con-pr"


def test_feature_branch_leaves_write_for_caller(project):
    write_rule(project, "con-pr", CON)
    _git(project, "init", "-q")
    _git(project, "config", "user.email", "t@t")
    _git(project, "config", "user.name", "t")
    _git(project, "add", "-A")
    _git(project, "commit", "-qm", "init")
    _git(project, "switch", "-c", "feature/x")
    r = _ratify_rule(project, "con-pr")
    rc = cliconstitution._route_through_pr(project, r, "Arpit", "2026-06-18", no_pr=False)
    assert rc == 0
    # already on a feature branch → don't create constitution/* ; caller commits.
    assert gitutil.current_branch(project) == "feature/x"
