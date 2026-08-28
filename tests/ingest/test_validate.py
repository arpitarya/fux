"""`validate()` — the optional fifth function on the fetcher contract.

W-87 P4 fork 3, ruled by Arpit 2026-08-28 after P3 cleared its gate (19/19 =
100 % of sanitized shas unchanged on an immediate re-fetch).

⚠ **THE INVARIANT this file exists to hold: a changed token must NEVER mean a
changed record.** Token unchanged skips the fetch — the only thing `validate`
may do. Token changed, `None`, or raising means fetch, and then *still* compare
the sanitized sha. Otherwise a chatty `ETag` churns shards and byte-determinism
is gone.
"""

from __future__ import annotations

import hashlib
import types

from fux.ingest.urlsrc import validate_group


def sha(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def fetcher(fn):
    m = types.ModuleType("f")
    if fn is not None:
        m.validate = fn
    return m


URLS = ["https://a.test/x", "https://b.test/y"]


def test_an_unchanged_token_skips_the_fetch():
    known = {"https://a.test/x": sha("v1")}
    unchanged, learned = validate_group(fetcher(lambda u: "v1"), URLS, known)

    assert unchanged == {"https://a.test/x"}, "matching token -> no body fetch"
    assert learned["https://b.test/y"] == sha("v1"), "and the new token is learned"


def test_a_changed_token_does_not_skip():
    """⚠ **The invariant.** A changed token buys a fetch, never a write."""
    known = {"https://a.test/x": sha("v1")}
    unchanged, _ = validate_group(fetcher(lambda u: "v2"), URLS, known)
    assert unchanged == set()


def test_none_means_cannot_tell_and_never_unchanged():
    """Every fetcher written before this contract returns nothing here."""
    known = {"https://a.test/x": sha("v1")}
    unchanged, learned = validate_group(fetcher(lambda u: None), URLS, known)
    assert unchanged == set()
    assert learned == {}, "nothing was learned, so nothing is recorded"


def test_a_fetcher_without_validate_is_untouched():
    """Zero migration: the contract stays four functions for everyone who has
    not opted in."""
    unchanged, learned = validate_group(fetcher(None), URLS, {"https://a.test/x": sha("v1")})
    assert (unchanged, learned) == (set(), {})


def test_a_raising_validate_fetches_rather_than_skipping():
    """An optimisation may not fail a run, and it may not empty a corpus.

    A broken `validate` that raised into a 'skip' would silently stop refreshing
    every URL it touched — the failure that looks exactly like a working cache.
    """
    def boom(url):
        raise RuntimeError("HEAD refused")

    unchanged, learned = validate_group(fetcher(boom), URLS, {"https://a.test/x": sha("v1")})
    assert unchanged == set()
    assert learned == {}


def test_an_empty_token_is_not_a_token():
    """`""` is falsy and must read as "cannot tell", not as a value that could
    match a stored empty string."""
    unchanged, learned = validate_group(fetcher(lambda u: ""), URLS, {"https://a.test/x": ""})
    assert unchanged == set()
    assert learned == {}


def test_no_known_token_means_fetch():
    """First sight of a URL: nothing to compare against."""
    unchanged, learned = validate_group(fetcher(lambda u: "v1"), URLS, {})
    assert unchanged == set()
    assert set(learned) == set(URLS), "but both tokens are learned for next time"


def test_the_token_is_hashed_never_stored(tmp_path):
    """W-87 P4 fork 4: `sha256(token)`, never the token.

    An `ETag` is opaque to fux but not necessarily to everyone — it can be a
    content hash, a version counter or an internal object id — and
    `url-state.json`, while gitignored, is the kind of local state that ends up
    in a support bundle. **L5 is untouched by construction, not by policy.**
    """
    secret = "W/\"internal-object-id-8891\""
    _, learned = validate_group(fetcher(lambda u: secret), ["https://a.test/x"], {})

    stored = learned["https://a.test/x"]
    assert secret not in stored
    assert stored == sha(secret)
    assert len(stored) == 64


def test_the_shipped_fetcher_implements_it():
    """The clean test that the fifth function is not dead weight — a contract
    nobody implements is surface with no proof behind it.
    """
    from pathlib import Path

    template = Path(__file__).resolve().parents[2] / "src" / "fux" / "templates" / "http.py.txt"
    source = template.read_text(encoding="utf-8")
    assert "def validate(url: str) -> str | None:" in source
    assert "ETag" in source and "Last-Modified" in source
    assert 'method="HEAD"' in source
