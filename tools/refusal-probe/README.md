# `refusal-probe` — do this repo's rules say the right thing about a real response?

The runnable form of [ADR-REFUSAL](../../docs/adr/0051_refusals.md)'s veto
condition, and the tool for debugging a rule.

```console
$ python3 tools/refusal-probe/probe.py <repo-root> tools/refusal-probe/cases.toml
```

`<repo-root>` is any repo whose `.fux/refusals.toml` you want to evaluate —
your own, or a scratch directory holding just the shipped starter.

**It never fetches.** Every case names a file under `captures/`, saved by
whatever obtained it. A probe that went to the network would answer differently
depending on who was signed in, which is the entire condition refusals exist to
detect.

## Captures and stand-ins

⚠ **A file named `*.stand-in.*` is not a capture.** It is a minimal file built
to carry the properties the rules test — the magic bytes, the size, a form field
name — because the real response was somebody's document and does not belong in
a public repo. `onedrive-viewer-shell.html` **is** a real capture, saved from a
live `1drv.ms` share link; it is the response this feature was built for, and
the only one whose byte offsets mean anything.

The distinction is in the filename because a reader who mistakes a stand-in for
a capture will draw conclusions from bytes nobody ever received.

## Adding a case

Save the response body into `captures/`, add a `[[case]]`, and set `expect`.

⚠ **An `expect = "accepted"` case is worth more than a refused one.** A rule
that refuses too much is invisible to every other check in the system — the
documents simply stop appearing — and these are the only thing that catches it.
Every rule added to the starter should arrive with at least one nearby response
that it must *not* match.

`tests/ingest/test_refusal_probe.py` runs every case in CI against the shipped
template, so a rule edit that changes an outcome fails there rather than in
somebody's corpus.
