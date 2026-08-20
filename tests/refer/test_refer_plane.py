"""The refer plane end to end — offline, with a fake fetcher and no socket."""

from __future__ import annotations

import ast
import inspect

import pytest

from fux import store as store_mod
from fux.refer import Policy, refer
from fux.refer.arc import ARC
from fux.refer.freshness import ALWAYS, NEVER

DOC = """# Rollback runbook

Drain traffic from the affected region before touching the release.

## Restore

Restore the previous release from the artifact store, then verify telemetry
against the golden dashboards for a full ten minutes before declaring success.

## Escalation

Page the on-call engineer if telemetry has not recovered. The rota hands over
every Monday morning and the handover notes live beside this runbook.
"""


@pytest.fixture
def repo(tmp_path):
    (tmp_path / "runbook.md").write_text(DOC, encoding="utf-8")
    return tmp_path


def _sha(text: str) -> str:
    return store_mod.content_sha(text.encode("utf-8"))


def _candidates(text: str = DOC):
    return [("file:runbook.md", "runbook.md", _sha(text))]


# -- it answers, and it cites verbatim -------------------------------------


def test_it_cites_a_verbatim_span_of_the_real_document(repo):
    bundle = refer(repo, "restore the previous release", _candidates())
    assert bundle.assembled.citations
    for citation in bundle.assembled.citations:
        assert citation.text in DOC, "a citation must be bytes that came from the source"


def test_a_git_source_keeps_full_function_with_the_never_policy(repo):
    """Offline degradation is honest: reading the checkout is not a fetch.

    `never` forbids going *out*. Refusing to read the local repository would
    make an audit unable to quote the repository it is auditing.
    """
    bundle = refer(repo, "telemetry", _candidates(), policy=Policy(mode=NEVER))
    assert bundle.assembled.citations
    assert bundle.documents[0].verdict.label == "current"


def test_the_policy_is_recorded_in_the_bundle(repo):
    bundle = refer(repo, "telemetry", _candidates(), policy=Policy(mode=ALWAYS, timeout_seconds=3))
    assert bundle.as_record()["policy"] == {"mode": "always", "timeout_seconds": 3}


# -- freshness, by content ------------------------------------------------


def test_a_changed_document_is_reported_stale_not_silently_used(repo):
    """The index says one sha; the working tree says another."""
    bundle = refer(repo, "telemetry", [("file:runbook.md", "runbook.md", "a" * 64)])
    assert bundle.documents[0].verdict.label == "stale"
    assert bundle.documents[0].verdict.fetched_sha == _sha(DOC)


def test_an_unreachable_url_declares_staleness_rather_than_serving_stale_bytes(repo):
    """The DoD's honest-degradation clause, as a test."""
    def broken(url):
        raise OSError("name resolution failed")

    bundle = refer(
        repo,
        "telemetry",
        [("url:https://x.test/page", "https://x.test/page", "b" * 64)],
        policy=Policy(mode=ALWAYS),
        fetcher=broken,
    )
    cited = bundle.documents[0]
    assert cited.verdict.label == "unverified"
    assert cited.verdict.current is None  # not False, and certainly not True
    assert "name resolution failed" in cited.note
    assert bundle.assembled.citations == []  # nothing invented from a failed fetch


def test_never_does_not_reach_out_for_a_url_document(repo):
    """L4 at the plane: the default policy opens nothing."""
    def forbidden(url):  # pragma: no cover - the point is that it never runs
        raise AssertionError("the never policy must not fetch")

    bundle = refer(
        repo,
        "telemetry",
        [("url:https://x.test/page", "https://x.test/page", "b" * 64)],
        policy=Policy(mode=NEVER),
        fetcher=forbidden,
    )
    assert bundle.documents[0].verdict.label == "unverified"
    assert bundle.documents[0].verdict.note == "policy:never"


def test_a_url_document_verifies_through_the_injected_fetcher(repo):
    page = "# Handbook\n\nThe on-call rota hands over on Monday and telemetry is checked hourly.\n"
    bundle = refer(
        repo,
        "telemetry rota",
        [("url:https://x.test/p", "https://x.test/p", _sha(page))],
        policy=Policy(mode=ALWAYS),
        fetcher=lambda url: page,
    )
    assert bundle.documents[0].verdict.label == "current"
    assert bundle.assembled.citations


def test_a_deleted_document_is_a_dead_citation_not_a_crash(repo):
    bundle = refer(repo, "telemetry", [("file:gone.md", "gone.md", "c" * 64)])
    assert bundle.documents[0].verdict.label == "unverified"
    assert "no longer in the working tree" in bundle.documents[0].note


# -- the ARC differential: the DoD's own clause ----------------------------


def test_cached_and_uncached_answers_are_byte_identical(repo):
    """The differential law, applied to the cache.

    A cache that can change an answer is not an optimisation, it is a second
    ranking system. This is the same discipline M2 established for the
    accelerator.
    """
    import json

    uncached = json.dumps(refer(repo, "restore telemetry", _candidates()).as_record(), indent=2)

    cache = ARC(100_000)
    cold = json.dumps(refer(repo, "restore telemetry", _candidates(), cache=cache).as_record(), indent=2)
    warm = json.dumps(refer(repo, "restore telemetry", _candidates(), cache=cache).as_record(), indent=2)

    assert cold == uncached, "the cold cache path changed the answer"
    assert warm == uncached, "the warm cache path changed the answer"
    assert cache.hits >= 1, "the second call did not actually hit the cache"


def test_the_cache_is_keyed_by_content_so_a_changed_source_is_never_served_stale(repo):
    cache = ARC(100_000)
    refer(repo, "telemetry", _candidates(), cache=cache)

    changed = DOC.replace("Monday", "Thursday")
    (repo / "runbook.md").write_text(changed, encoding="utf-8")
    bundle = refer(repo, "telemetry", _candidates(changed), cache=cache)

    assert bundle.documents[0].verdict.label == "current"
    for citation in bundle.assembled.citations:
        assert citation.text in changed


# -- determinism and the fence --------------------------------------------


def test_the_same_query_twice_is_the_same_bytes(repo):
    import json

    first = json.dumps(refer(repo, "restore telemetry", _candidates()).as_record())
    assert json.dumps(refer(repo, "restore telemetry", _candidates()).as_record()) == first


def test_no_module_in_the_plane_imports_a_network_library():
    """L4's import fence, extended to the plane that most wants to break it."""
    import fux.refer as plane
    from fux.refer import arc, assemble, chunk, freshness, rescore, source

    for module in (plane, arc, assemble, chunk, freshness, rescore, source):
        tree = ast.parse(inspect.getsource(module))
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
        assert not {"urllib", "socket", "http", "ssl", "requests"} & imported, (
            f"{module.__name__} imports a network library: {imported}"
        )
