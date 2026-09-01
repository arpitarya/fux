"""`.fux/refusals.toml` — parsing, matching, and the always-on magic floor.

Every test here runs on captured bytes. No browser, no network, no Chrome —
which is the whole argument for the rules being data rather than a predicate.
"""

from __future__ import annotations

import pytest

from fux.errors import FuxError
from fux.ingest import refusals

XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
HTML = "text/html; charset=utf-8"

# Over 1 KiB on purpose: `suspiciously-small-document` fires under that, and
# a 200-byte fixture would make this file assert the opposite of reality.
REAL_XLSX = b"PK\x03\x04" + b"\x14\x00\x06\x00" + b"sheet1.xml" * 300

LOGIN_PAGE = (
    b'<!DOCTYPE html><html><head><title>Sign in to your account</title></head>'
    b'<body><form method="post" action="/common/login">'
    b'<input type="email" name="loginfmt" id="i0116">'
    b'<input type="password" name="passwd" id="i0118">'
    b"</form></body></html>"
)

SAML_HANDOFF = (
    b'<html><body onload="document.forms[0].submit()">'
    b'<form method="post" action="https://idp.example.com/sso">'
    b'<input type="hidden" name="SAMLRequest" value="fZJb...">'
    b"</form></body></html>"
)

STARTER = """
[[rule]]
name   = "document-request-returned-a-web-page"
reason = "asked for a document and got a web page - sign in and re-run"
content_type         = ["text/html", "application/xhtml+xml"]
requested_suffix_not = [".html", ".htm", ""]

[[rule]]
name   = "password-form-in-response"
reason = "the response body contains a sign-in form - you are signed out"
content_type  = ["text/html"]
body_contains = ['type="password"']

[[rule]]
name   = "suspiciously-small-document"
reason = "the response is too small to be the document"
requested_suffix_not = [".html", ".htm", ".txt", ".md"]
max_bytes            = 1024

[[rule]]
name   = "office-web-viewer-shell"
reason = "the Office web viewer, not the workbook - append &download=1"
content_type  = ["text/html"]
body_contains = ["WOPISrc=", "_wopiContextJson", "viewerinternal.aspx", "WacFrame_Excel"]
"""


def rules(text: str = STARTER):
    return refusals.parse(__import__("tomllib").loads(text), origin="test")


# -- the always-on floor ----------------------------------------------------


def test_magic_floor_passes_a_real_workbook():
    assert refusals.magic_mismatch(XLSX, REAL_XLSX) is None


def test_magic_floor_catches_html_wearing_a_workbook_type():
    reason = refusals.magic_mismatch(XLSX, LOGIN_PAGE)
    assert reason is not None
    assert "does not start like one" in reason


def test_magic_floor_is_silent_on_types_it_does_not_know():
    # An unknown type is NOT a refusal. Guessing a signature would turn the
    # floor into a source of false skips, and a floor that cries wolf gets
    # switched off.
    assert refusals.magic_mismatch("application/octet-stream", b"anything") is None


def test_magic_floor_runs_with_no_rules_file():
    assert refusals.refused((), "https://x/a.xlsx", XLSX, LOGIN_PAGE) is not None


def test_magic_floor_cannot_be_overridden_by_rules():
    # Even a rules file that would happily accept this still refuses: the
    # floor is checked first and no rule can subtract a refusal.
    assert refusals.refused(rules(), "https://x/a.xlsx", XLSX, LOGIN_PAGE) is not None


# -- matching ---------------------------------------------------------------


def test_document_request_returning_html_is_refused():
    reason = refusals.refused(rules(), "https://x/report.xlsx", HTML, LOGIN_PAGE)
    assert reason is not None
    assert "document-request-returned-a-web-page" in reason


def test_a_real_workbook_is_not_refused():
    assert refusals.refused(rules(), "https://x/report.xlsx", XLSX, REAL_XLSX) is None


# Over 1 KiB deliberately. `suspiciously-small-document` refuses sub-1 KiB HTML
# at ANY url now, extensionless included, because that much markup is a <head>
# and little else. A 137-byte fixture would assert the opposite of the design.
ORDINARY_PAGE = (
    b"<!DOCTYPE html><html><head><title>Deploy runbook</title></head><body>"
    b"<h1>Deploy runbook</h1>"
    + b"<p>Roll forward, never back. A rollback needing a schema change is not "
      b"a rollback. Health endpoints carry the commit sha.</p>" * 8
    + b"</body></html>"
)
assert len(ORDINARY_PAGE) > 1024


def test_an_html_page_requested_as_html_is_not_refused():
    assert refusals.refused(rules(), "https://x/page.html", HTML, ORDINARY_PAGE) is None


def test_extensionless_url_is_not_refused_for_being_html():
    # A bare URL asks for a page. `""` is in requested_suffix_not precisely so
    # the common case does not become a corpus-wide false positive.
    assert refusals.refused(rules(), "https://x/wiki/runbook", HTML, ORDINARY_PAGE) is None


def test_a_login_page_is_refused_even_at_an_html_url():
    # The suffix rules cannot catch this one - the URL asked for a page and got
    # a page. `password-form-in-response` is what covers a wiki or docs URL
    # whose session has expired, and it is why that rule exists separately.
    reason = refusals.refused(rules(), "https://x/wiki/runbook", HTML, LOGIN_PAGE)
    assert reason is not None
    assert "password-form-in-response" in reason


def test_password_form_catches_a_login_page_at_an_html_url():
    only = rules(
        """
        [[rule]]
        name   = "password-form-in-response"
        reason = "sign-in form"
        content_type  = ["text/html"]
        body_contains = ['type="password"']
        """
    )
    assert refusals.refused(only, "https://x/page.html", HTML, LOGIN_PAGE) is not None


def test_saml_handoff_matches_on_protocol_markup_not_branding():
    only = rules(
        """
        [[rule]]
        name   = "saml-or-oidc-handoff"
        reason = "identity-provider handoff page"
        content_type  = ["text/html"]
        body_contains = ['name="SAMLRequest"', 'name="SAMLResponse"']
        """
    )
    assert refusals.refused(only, "https://x/p.html", HTML, SAML_HANDOFF) is not None


def test_small_response_where_a_document_was_expected():
    reason = refusals.refused(rules(), "https://x/a.pdf", "application/pdf", b"%PDF-tiny")
    assert reason is not None
    assert "suspiciously-small-document" in reason


def test_first_match_wins_in_file_order():
    two = rules(
        """
        [[rule]]
        name   = "first"
        reason = "first reason"
        content_type = ["text/html"]

        [[rule]]
        name   = "second"
        reason = "second reason"
        content_type = ["text/html"]
        """
    )
    assert "[first]" in refusals.refused(two, "https://x/a.html", HTML, LOGIN_PAGE)


def test_conditions_within_a_rule_are_anded():
    both = rules(
        """
        [[rule]]
        name   = "needs-both"
        reason = "both"
        content_type  = ["text/html"]
        body_contains = ["nowhere-in-this-page"]
        """
    )
    assert refusals.refused(both, "https://x/a.html", HTML, LOGIN_PAGE) is None


def test_body_conditions_never_fire_on_an_unsearchable_body():
    # A large binary body is not decoded, and "we could not look" must not
    # read as a match — that would refuse real documents.
    big_binary = b"PK\x03\x04" + bytes(range(256)) * 1000
    rule = rules(
        """
        [[rule]]
        name   = "marker"
        reason = "marker present"
        body_contains = ["password"]
        """
    )
    assert refusals.refused(rule, "https://x/a.xlsx", XLSX, big_binary) is None


def test_body_starts_with_hex():
    rule = rules(
        """
        [[rule]]
        name   = "zip-shaped"
        reason = "zip shaped"
        body_starts_with = "50 4b 03 04"
        """
    )
    assert refusals.refused(rule, "https://x/a.bin", "application/octet-stream", REAL_XLSX)


def test_content_type_matches_prefix_ignoring_parameters():
    rule = rules(
        """
        [[rule]]
        name   = "html"
        reason = "html"
        content_type = ["text/html"]
        """
    )
    assert refusals.refused(rule, "https://x/a", "TEXT/HTML; charset=UTF-8", b"<html>")


def test_suffix_is_taken_from_the_url_not_the_response():
    assert refusals.suffix_of("https://x/a/b/report.XLSX?download=1&v=2") == ".xlsx"
    assert refusals.suffix_of("https://x/wiki/runbook") == ""
    assert refusals.suffix_of("https://x/") == ""


def test_body_contains_finds_a_marker_past_64_kib():
    """Regression: a live Office viewer put its marker at ~byte 101,000.

    The scan cap was 64 KiB, so the rule written for that exact page could not
    see it and the shell was indexed as a document. Measured 2026-09-01
    against a 160,068-byte response that decoded to two words.
    """
    body = b"<html><head><title>Book.xlsx</title></head><body>"
    body += b"<script>var x=1;</script>" * 4000          # ~100 KB of filler
    assert len(body) > 64 * 1024
    body += b'<iframe name="WacFrame_Excel_0"></iframe></body></html>'
    rule = rules(
        """
        [[rule]]
        name   = "office-web-viewer-shell"
        reason = "the Office web viewer, not the workbook"
        content_type  = ["text/html"]
        body_contains = ["WacFrame_Excel"]
        """
    )
    assert refusals.refused(rule, "https://x/share/token", HTML, body) is not None


def test_body_scan_is_still_bounded():
    # Not unbounded: a pathological response must not make matching unbounded.
    assert refusals.BODY_SCAN_BYTES <= 4 * 1024 * 1024


def test_wopi_viewer_host_page_is_refused():
    """Markers taken from a real capture, not invented.

    A `1drv.ms` share link lands on onedrive.live.com and returns 160,077
    bytes of HTML carrying ONE word of visible text. The first version of this
    rule matched `WacFrame_Excel`, read off the excel.cloud.microsoft launcher
    -- a different page in the chain, which does not contain that string. It
    never fired. `WOPISrc` and `_wopiContextJson` are protocol and internal-API
    names and are present on both.
    """
    page = (
        b'<!DOCTYPE html><html lang="en-us"><head><title>Book.xlsx</title>'
        b"<script>var wopiDiagClient={};var _wopiContextJson={"
        b'"HostName":"SharePoint Online Consumer",'
        b'"WebAppUrl":"https://excel.officeapps.live.com/x/_layouts/'
        b'xlviewerinternal.aspx?unified=1&WOPISrc=https%3A%2F%2Fexample"};'
        b"</script>" + b"<script>var pad=%d;</script>" * 40 % tuple(range(40))
        + b"</head><body></body></html>"
    )
    assert len(page) > 1024
    reason = refusals.refused(rules(), "https://1drv.ms/x/c/abc/TOKEN?e=xyz", HTML, page)
    assert reason is not None
    assert "office-web-viewer-shell" in reason


def test_wacframe_launcher_still_matches_too():
    # The other real page in the chain. Both markers are kept; one page's
    # marker says nothing about the others.
    page = b'<html><body><iframe name="WacFrame_Excel_0"></iframe></body></html>'
    assert refusals.refused(rules(), "https://x/open/onedrive/", HTML, page) is not None


# -- missing vs malformed ---------------------------------------------------


def test_missing_file_is_a_legitimate_configuration(tmp_path):
    assert refusals.load(tmp_path) == ()


def test_missing_file_still_leaves_the_floor_in_place(tmp_path):
    assert refusals.refused(refusals.load(tmp_path), "https://x/a.pdf", "application/pdf", b"<html>")


def test_malformed_toml_raises(tmp_path):
    (tmp_path / ".fux").mkdir()
    (tmp_path / ".fux" / "refusals.toml").write_text("[[rule]\nname = ", encoding="utf-8")
    with pytest.raises(FuxError, match="invalid TOML"):
        refusals.load(tmp_path)


def test_a_rule_without_a_name_raises():
    with pytest.raises(FuxError, match="'name' is required"):
        rules('[[rule]]\nreason = "r"\ncontent_type = ["text/html"]\n')


def test_a_rule_without_a_reason_raises():
    with pytest.raises(FuxError, match="'reason' is required"):
        rules('[[rule]]\nname = "n"\ncontent_type = ["text/html"]\n')


def test_an_unknown_condition_raises_rather_than_being_ignored():
    # The whole point: a typo'd condition that silently does nothing leaves a
    # rule that reads as protection and is not.
    with pytest.raises(FuxError, match="unknown condition"):
        rules('[[rule]]\nname = "n"\nreason = "r"\nstatus = [403]\n')


def test_transport_conditions_are_rejected_by_name():
    # ADR-FETCHER decision 13. These are the three that were specified and
    # then removed; naming them in a test is what stops them drifting back.
    for key, value in (
        ("status", "[403]"),
        ("final_url_host", '["login.example.com"]'),
        ("final_url_contains", '["/login"]'),
    ):
        with pytest.raises(FuxError, match="unknown condition"):
            rules(f'[[rule]]\nname = "n"\nreason = "r"\n{key} = {value}\n')


def test_a_rule_with_no_conditions_raises():
    with pytest.raises(FuxError, match="declares no conditions"):
        rules('[[rule]]\nname = "n"\nreason = "r"\n')


def test_duplicate_rule_names_raise():
    with pytest.raises(FuxError, match="duplicate rule name"):
        rules(
            '[[rule]]\nname = "n"\nreason = "r"\ncontent_type = ["text/html"]\n'
            '[[rule]]\nname = "n"\nreason = "r2"\ncontent_type = ["text/xml"]\n'
        )


def test_unknown_top_level_key_raises():
    with pytest.raises(FuxError, match="unknown top-level key"):
        rules('rules = []\n[[rule]]\nname = "n"\nreason = "r"\nmax_bytes = 10\n')


def test_bad_hex_raises():
    with pytest.raises(FuxError, match="not valid hex"):
        rules('[[rule]]\nname = "n"\nreason = "r"\nbody_starts_with = "zz zz"\n')


def test_max_bytes_must_be_a_positive_int():
    for value in ("0", "-1", "true", '"10"'):
        with pytest.raises(FuxError, match="must be a positive integer"):
            rules(f'[[rule]]\nname = "n"\nreason = "r"\nmax_bytes = {value}\n')


def test_empty_condition_list_raises():
    with pytest.raises(FuxError, match="non-empty list"):
        rules('[[rule]]\nname = "n"\nreason = "r"\ncontent_type = []\n')


def test_the_shipped_starter_file_parses(tmp_path):
    # The template fux writes must itself be valid, or `fux setup` hands the
    # consumer a repo that refuses to run.
    from fux import setup as setup_mod

    text = (Path(setup_mod.__file__).parent / "templates" / "refusals.toml.txt").read_text(
        encoding="utf-8"
    )
    parsed = refusals.parse(__import__("tomllib").loads(text), origin="template")
    assert parsed, "the shipped starter must contain at least one rule"
    assert len({r.name for r in parsed}) == len(parsed)


from pathlib import Path  # noqa: E402  (used only by the template test above)
