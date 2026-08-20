"""The freshness policy — what it allows, and what it refuses to pretend."""

from __future__ import annotations

import ast
import inspect

import pytest

from fux.errors import FuxError
from fux.refer import freshness
from fux.refer.freshness import ALWAYS, NEVER, Policy, decide, verify


def test_never_is_the_default():
    """Offline by default (L4) means the default policy does not go out."""
    assert Policy().mode == NEVER
    assert Policy().forbids_fetch


def test_never_forbids_the_fetch_and_says_why():
    decision = decide(Policy(mode=NEVER))
    assert not decision and decision.reason == "policy:never"


def test_always_permits_the_fetch():
    assert decide(Policy(mode=ALWAYS))


def test_an_age_based_mode_is_refused_with_the_reason():
    """W-58: the record carries no ingest time, so an age bound could not be
    honoured. Refusing loudly beats accepting a knob that does nothing."""
    with pytest.raises(FuxError, match="no ingest time"):
        Policy(mode="max_age")


@pytest.mark.parametrize("bad", [0, -1, "5", 1.5, True])
def test_a_nonsense_timeout_is_refused(bad):
    with pytest.raises(FuxError, match="timeout_seconds"):
        Policy(mode=ALWAYS, timeout_seconds=bad)


def test_the_policy_travels_with_the_answer():
    """A replay that silently used a different policy is indistinguishable
    from a replay that reproduced. So the policy is part of the output."""
    assert Policy(mode=ALWAYS, timeout_seconds=9).as_record() == {
        "mode": "always",
        "timeout_seconds": 9,
        "cache_ttl_seconds": 0,
        "no_cache": False,
    }


def test_nothing_in_this_module_reads_the_clock():
    """The no-wall-clock law, asserted against the AST rather than trusted."""
    tree = ast.parse(inspect.getsource(freshness))
    imported = {
        alias.name.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    } | {
        node.module.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module
    }
    assert not {"time", "datetime"} & imported, imported


# -- verification is by content, not by clock ------------------------------


def test_matching_shas_are_current():
    v = verify("abc", "abc")
    assert v.current is True and v.label == "current"


def test_differing_shas_are_stale():
    v = verify("abc", "def")
    assert v.current is False and v.label == "stale"


def test_no_fetch_is_unverified_and_that_is_not_fresh():
    """The three-state verdict exists so nothing downstream can collapse
    'we did not look' into 'we looked and it was fine'."""
    v = verify("abc", None)
    assert v.current is None
    assert v.label == "unverified"
    assert v.label != "current"
