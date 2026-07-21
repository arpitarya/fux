"""Crawl frontier logic with a fake fetcher — depth, budget, robots, dedupe."""

from __future__ import annotations

import pytest

from fux.config import WebParams
from fux.errors import FuxError
from fux.ingest.web import WebSkip, cache_rel_for_url, crawl


class FakeFetcher:
    def __init__(self, pages: dict[str, tuple[bytes, str]]):
        self.pages = pages
        self.fetched: list[str] = []

    def fetch(self, url: str):
        self.fetched.append(url)
        if url not in self.pages:
            raise WebSkip("HTTP 404")
        data, ctype = self.pages[url]
        return url, data, ctype


class FakeRobots:
    def __init__(self, disallowed: set[str] | None = None):
        self.disallowed = disallowed or set()

    def allowed(self, url: str) -> bool:
        return url not in self.disallowed


def html(links: list[str] = (), text: str = "hello world") -> tuple[bytes, str]:
    body = "".join(f'<a href="{l}">l</a>' for l in links)
    return f"<title>T</title><p>{text}</p>{body}".encode(), "text/html"


def params(**kw) -> WebParams:
    kw.setdefault("urls", ("http://site.test/",))
    kw.setdefault("delay_s", 0)
    return WebParams(**kw)


def test_depth_cap():
    fetcher = FakeFetcher(
        {
            "http://site.test/": html(["http://site.test/a"]),
            "http://site.test/a": html(["http://site.test/b"]),
            "http://site.test/b": html(),
        }
    )
    report = crawl(params(max_depth=1), fetcher, FakeRobots())
    urls = [a.url for a in report.artifacts]
    assert urls == ["http://site.test/", "http://site.test/a"]  # b is depth 2


def test_cycles_terminate():
    fetcher = FakeFetcher(
        {
            "http://site.test/": html(["http://site.test/a"]),
            "http://site.test/a": html(["http://site.test/"]),
        }
    )
    report = crawl(params(max_depth=5), fetcher, FakeRobots())
    assert len(report.artifacts) == 2
    assert len(fetcher.fetched) == 2


def test_same_domain_and_allowlist():
    fetcher = FakeFetcher(
        {
            "http://site.test/": html(
                ["http://other.test/x", "http://friend.test/y"]
            ),
            "http://friend.test/y": html(),
        }
    )
    report = crawl(params(max_depth=1, allow=("friend.test",)), fetcher, FakeRobots())
    urls = [a.url for a in report.artifacts]
    assert "http://friend.test/y" in urls
    assert all("other.test" not in u for u in urls)
    assert any("off-domain" in reason for _, reason in report.skipped)


def test_budget_cap():
    pages = {"http://site.test/": html([f"http://site.test/p{i}" for i in range(10)])}
    pages.update({f"http://site.test/p{i}": html() for i in range(10)})
    report = crawl(params(max_depth=1, budget=3), fetcher := FakeFetcher(pages), FakeRobots())
    assert len(report.artifacts) == 3
    assert sum("budget" in r for _, r in report.skipped) == 8


def test_robots_disallow_reported():
    fetcher = FakeFetcher(
        {
            "http://site.test/": html(["http://site.test/private"]),
            "http://site.test/private": html(),
        }
    )
    robots = FakeRobots({"http://site.test/private"})
    report = crawl(params(max_depth=1), fetcher, robots)
    assert [a.url for a in report.artifacts] == ["http://site.test/"]
    assert ("http://site.test/private", "disallowed by robots.txt") in report.skipped


def test_attachment_routed_by_extension():
    fetcher = FakeFetcher(
        {
            "http://site.test/": html(["http://site.test/spec.pdf"]),
            "http://site.test/spec.pdf": (b"%PDF-1.4 fake", "application/pdf"),
        }
    )
    report = crawl(params(max_depth=1), fetcher, FakeRobots())
    pdf = next(a for a in report.artifacts if a.url.endswith(".pdf"))
    assert pdf.origin == "attachment" and pdf.kind == "office"
    assert pdf.parent == "http://site.test/" and pdf.depth == 1


def test_sha_dedupe_records_both_provenances():
    same = html(text="identical content everywhere")
    fetcher = FakeFetcher(
        {
            "http://site.test/": html(
                ["http://site.test/a", "http://site.test/b"], text="root"
            ),
            "http://site.test/a": same,
            "http://site.test/b": same,
        }
    )
    report = crawl(params(max_depth=1), fetcher, FakeRobots())
    a = next(x for x in report.artifacts if x.url.endswith("/a"))
    b = next(x for x in report.artifacts if x.url.endswith("/b"))
    assert a.duplicate_of is None
    assert b.duplicate_of == "http://site.test/a"


def test_fetch_failure_skips_not_crashes():
    fetcher = FakeFetcher({"http://site.test/": html(["http://site.test/gone"])})
    report = crawl(params(max_depth=1), fetcher, FakeRobots())
    assert ("http://site.test/gone", "HTTP 404") in report.skipped


def test_unsupported_content_type_skipped():
    fetcher = FakeFetcher(
        {
            "http://site.test/": html(["http://site.test/blob"]),
            "http://site.test/blob": (b"\x00\x01", "application/octet-stream"),
        }
    )
    report = crawl(params(max_depth=1), fetcher, FakeRobots())
    assert any("unsupported content-type" in r for _, r in report.skipped)


def test_renderer_hook_replaces_html():
    fetcher = FakeFetcher({"http://site.test/": html(text="shell only")})
    report = crawl(
        params(render="cdp"),
        fetcher,
        FakeRobots(),
        renderer=lambda url, fallback: "<p>rendered dom</p>",
    )
    art = report.artifacts[0]
    assert art.renderer == "cdp"
    assert b"rendered dom" in art.data


def test_cache_rel_for_url_shapes():
    assert cache_rel_for_url("http://site.test/") == ".fux/cache/_web/site.test/index.md"
    assert (
        cache_rel_for_url("http://site.test/docs/guide.html")
        == ".fux/cache/_web/site.test/docs/guide.html.md"
    )
    a = cache_rel_for_url("http://site.test/p?x=1")
    b = cache_rel_for_url("http://site.test/p?x=2")
    assert a != b  # query strings disambiguated
    assert cache_rel_for_url("http://localhost:8123/x") == ".fux/cache/_web/localhost_8123/x.md"


def test_web_config_validation(tmp_path):
    from fux.config import load

    (tmp_path / "fux.toml").write_text(
        '[sources]\ndocs = []\n[sources.web]\nurls = ["https://a.test"]\nmax_depth = 2\n'
        'attachments = ["PDF", ".docx"]\n',
        encoding="utf-8",
    )
    cfg = load(tmp_path)
    assert cfg.web.urls == ("https://a.test",)
    assert cfg.web.max_depth == 2
    assert cfg.web.attachments == ("pdf", "docx")
    assert cfg.web.render == "off"

    (tmp_path / "fux.toml").write_text(
        '[sources.web]\nurls = ["ftp://nope"]\n', encoding="utf-8"
    )
    with pytest.raises(FuxError, match="http"):
        load(tmp_path)

    (tmp_path / "fux.toml").write_text(
        '[sources.web]\nurls = ["https://a.test"]\nrender = "magic"\n', encoding="utf-8"
    )
    with pytest.raises(FuxError, match="render"):
        load(tmp_path)
