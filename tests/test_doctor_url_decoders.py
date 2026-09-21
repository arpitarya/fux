"""`fux doctor`'s two `decoder=` rows — W-199 DoD 10, SR-DOCTOR's register.

- **`url decoders`** — every `decoder=` on every URL line resolves to a module.
  An **error**: every URL on a line that does not is skipped at ingest.
- **`observed types`** — a line's declared stem against the `Content-Type` of
  the bytes fux actually retained. A **finding**, because the line wins and the
  header loses *silently* by design, so this row is the only place anybody
  learns the two disagree. 🔴 W-200's second provenance finding, which had no
  field to read until this half of the pipe shipped.

🔴 **Both offline, and neither imports a decoder.** A consumer decoder whose
dependency is missing is SR-DECODE decision 7's loud ingest failure, not
`doctor`'s business — it reports that a stem is *absent*, never that a library
is, which is why the row lists a directory instead of loading it.
"""

from __future__ import annotations


from fux import doctor
from fux.store import acquired


def _repo(tmp_path, *, urls="", decoders=()):
    (tmp_path / ".git").mkdir(exist_ok=True)
    (tmp_path / "fux.toml").write_text(
        "[sources]\n[sources.url]\nmax_parallel = 4\n", encoding="utf-8"
    )
    fetchers = tmp_path / ".fux" / "fetchers"
    fetchers.mkdir(parents=True, exist_ok=True)
    (fetchers / "http.py").write_text("def fetch(url): ...\n", encoding="utf-8")
    if decoders:
        d = tmp_path / ".fux" / "decoders"
        d.mkdir(parents=True, exist_ok=True)
        for stem in decoders:
            (d / f"{stem}.py").write_text(
                f"EXTENSIONS = ('.{stem}',)\ndef decode(raw, rel_path):\n    return 'x'\n",
                encoding="utf-8",
            )
    src = tmp_path / ".fux" / "sources"
    src.mkdir(parents=True, exist_ok=True)
    (src / "urls").write_text(urls, encoding="utf-8")
    (tmp_path / ".fux" / "pii.toml").write_text("", encoding="utf-8")
    return tmp_path


def _row(root, name):
    return next(c for c in doctor.run(root) if c.name == name)


# --- url decoders -----------------------------------------------------------


def test_a_built_in_prose_and_a_consumer_module_all_resolve(tmp_path):
    root = _repo(
        tmp_path,
        urls=(
            "https://x.test/a fetch=http decoder=html\n"
            "https://x.test/b fetch=http decoder=prose\n"
            "https://x.test/c fetch=http decoder=vndthing\n"
        ),
        decoders=("vndthing",),
    )
    row = _row(root, "url decoders")
    assert row.ok and "3 URL line(s)" in row.detail


def test_a_typo_is_a_FAILURE_naming_the_stem_and_both_vocabularies(tmp_path):
    """The whole reason the row exists: `decoder=xlxs` parses.

    Without it, that line is discovered by the next person's ingest skipping
    the document with `no decoder module named 'xlxs'` — mid-run, on somebody
    else's machine.
    """
    root = _repo(tmp_path, urls="https://x.test/a fetch=http decoder=xlxs\n")
    row = _row(root, "url decoders")
    assert not row.ok
    assert "xlxs" in row.detail
    assert "Built-ins are" in row.detail and ".fux/decoders/" in row.detail


def test_a_consumer_decoder_is_checked_by_NAME_and_never_imported(tmp_path):
    """Edge case 3: a missing dependency is ingest's loud failure, not this row's.

    The module here raises on import. The row must still pass — it listed a
    directory, which is all it is allowed to do.
    """
    root = _repo(tmp_path, urls="https://x.test/a fetch=http decoder=needy\n")
    d = root / ".fux" / "decoders"
    d.mkdir(parents=True, exist_ok=True)
    (d / "needy.py").write_text("import a_library_nobody_has\n", encoding="utf-8")
    row = _row(root, "url decoders")
    assert row.ok, row.detail


def test_an_excluded_or_absent_list_is_not_a_finding(tmp_path):
    assert _row(_repo(tmp_path, urls=""), "url decoders").ok


def test_a_list_that_does_not_parse_is_skipped_rather_than_reported_twice(tmp_path):
    """A line with no `decoder=` at all fails the PARSE, and the fetcher-bindings
    row already reports that. Two rows saying one thing is noise."""
    root = _repo(tmp_path, urls="https://x.test/a fetch=http\n")
    row = _row(root, "url decoders")
    assert row.ok and "does not parse" in row.detail


# --- observed types ---------------------------------------------------------


def _retain(root, url, content_type, raw=b"<html>x</html>"):
    blob = acquired.save(root, url, raw, content_type, ".html", run_seq=1)
    acquired.write_manifest(root, {url: blob})


def test_a_line_declaring_what_it_came_back_as_is_clean(tmp_path):
    root = _repo(tmp_path, urls="https://x.test/a fetch=http decoder=html\n")
    _retain(root, "https://x.test/a", "text/html; charset=utf-8")
    row = _row(root, "observed types")
    assert row.ok and "1 retained URL(s)" in row.detail


def test_a_disagreement_is_a_FINDING_naming_both_sides(tmp_path):
    """W-200's finding. The line wins by design, so this reports and stops."""
    root = _repo(tmp_path, urls="https://x.test/a fetch=http decoder=prose\n")
    _retain(root, "https://x.test/a", "application/pdf", raw=b"%PDF-1.7\n")
    row = _row(root, "observed types")
    assert not row.ok
    assert row.level == "warn", "the header loses silently — never an error"
    assert "declares prose" in row.detail and "came back as pdf" in row.detail


def test_nothing_retained_is_not_a_finding(tmp_path):
    """`keep=false` means there is nothing to compare against, which is not news."""
    root = _repo(tmp_path, urls="https://x.test/a fetch=http decoder=html keep=false\n")
    row = _row(root, "observed types")
    assert row.ok and "nothing retained" in row.detail


def test_a_type_that_maps_to_nothing_is_not_a_finding(tmp_path):
    """Only a type that resolves to a DIFFERENT stem is a disagreement.

    An `application/octet-stream` with no telling extension proposes nothing,
    and *"we cannot tell"* must not read as *"the line is wrong"*.
    """
    root = _repo(tmp_path, urls="https://x.test/a fetch=http decoder=xlsx\n")
    _retain(root, "https://x.test/a", "application/octet-stream", raw=b"PK\x03\x04")
    row = _row(root, "observed types")
    assert row.ok, row.detail


def test_both_rows_are_ascii_in_every_branch(tmp_path):
    """A `FuxError` message may hold an em dash and a Windows console runs
    cp1252 — a detail that crashes `print()` does it when the repo is already
    broken. The suite-wide check covers the clean branches; these are the two
    failing ones."""
    root = _repo(tmp_path, urls="https://x.test/a fetch=http decoder=xlxs\n")
    _retain(root, "https://x.test/a", "application/pdf", raw=b"%PDF-1.7\n")
    for name in ("url decoders", "observed types"):
        detail = _row(root, name).detail
        detail.encode("ascii")


def test_neither_row_writes_anything(tmp_path):
    """`doctor` is read-only, and `acquired.plane()` is pure on purpose."""
    root = _repo(tmp_path, urls="https://x.test/a fetch=http decoder=html\n")
    before = sorted(p.as_posix() for p in root.rglob("*"))
    _row(root, "url decoders")
    _row(root, "observed types")
    assert sorted(p.as_posix() for p in root.rglob("*")) == before
