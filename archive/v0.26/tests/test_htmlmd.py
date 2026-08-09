"""HTML→Markdown converter: golden-style unit suite (deterministic output)."""

from __future__ import annotations

from fux.ingest.htmlmd import extract_links, extract_title, html_to_markdown


def test_headings_and_paragraphs():
    html = "<h1>Title</h1><p>First para.</p><h2>Sub</h2><p>Second   para\nwrapped.</p>"
    assert html_to_markdown(html) == (
        "# Title\n\nFirst para.\n\n## Sub\n\nSecond para wrapped.\n"
    )


def test_nested_lists():
    html = "<ul><li>one</li><li>two<ul><li>deep</li></ul></li></ul><ol><li>first</li><li>second</li></ol>"
    out = html_to_markdown(html)
    assert "- one" in out
    assert "  - deep" in out
    assert "1. first" in out and "2. second" in out


def test_links_images_emphasis_code():
    html = (
        '<p>See <a href="https://x.test/doc">the doc</a> and '
        '<img src="a.png" alt="chart"> with <b>bold</b>, <em>it</em>, <code>x=1</code>.</p>'
    )
    out = html_to_markdown(html)
    assert "[the doc](https://x.test/doc)" in out
    assert "![chart](a.png)" in out
    assert "**bold**" in out and "*it*" in out and "`x=1`" in out


def test_pre_block_preserved():
    html = "<p>before</p><pre>def f():\n    return 1</pre><p>after</p>"
    out = html_to_markdown(html)
    assert "```\ndef f():\n    return 1\n```" in out


def test_table_emitted_with_header_separator():
    html = (
        "<table><tr><th>key</th><th>val</th></tr>"
        "<tr><td>rate</td><td>5</td></tr></table>"
    )
    out = html_to_markdown(html)
    assert "| key | val |" in out
    assert "|---|---|" in out
    assert "| rate | 5 |" in out


def test_blockquote():
    assert "> quoted text" in html_to_markdown("<blockquote>quoted text</blockquote>")


def test_script_style_head_dropped():
    html = (
        "<head><title>T</title><style>p{}</style></head>"
        "<body><script>evil()</script><p>kept</p><noscript>no</noscript></body>"
    )
    out = html_to_markdown(html)
    assert out == "kept\n"


def test_deterministic():
    html = "<h1>A</h1><ul><li>x</li></ul><table><tr><td>1</td></tr></table>"
    assert html_to_markdown(html) == html_to_markdown(html)


def test_malformed_html_degrades():
    out = html_to_markdown("<p>unclosed <b>bold <li>stray</p></div>")
    assert "unclosed" in out and "stray" in out


def test_extract_links_absolute_dedup_and_filters():
    html = (
        '<a href="/rel">r</a><a href="https://other.test/x#frag">o</a>'
        '<a href="/rel">dup</a><a href="#top">skip</a><a href="mailto:a@b">skip</a>'
        '<a href="javascript:void(0)">skip</a>'
    )
    links = extract_links(html, "https://site.test/dir/page.html")
    assert links == ["https://site.test/rel", "https://other.test/x"]


def test_extract_links_honors_base_tag():
    html = '<base href="https://cdn.test/root/"><a href="doc.html">d</a>'
    assert extract_links(html, "https://site.test/") == ["https://cdn.test/root/doc.html"]


def test_extract_title():
    assert extract_title("<head><title> My Page </title></head>") == "My Page"
    assert extract_title("<p>no title</p>") == ""
