# Security policy

## Reporting a vulnerability

**Please don't open a public issue.** Report it privately through GitHub instead:

1. Go to the repository's **Security** tab.
2. Choose **Report a vulnerability**.

You'll get an acknowledgement within 5 working days, and a fix or a plan within 30 days of confirming the issue.

## What counts

fux reads your documents, commits an index to git and can fetch from the systems that own your docs. These are in scope:

- **text that should have been redacted reaching the committed index**, past `.fux/pii.toml`;
- **a crafted document that makes a decoder run code**, read files outside the corpus, or reach the network;
- **network access on a default path**, or a fetch that isn't announced on stderr;
- **a fetcher that leaks a session or credential**, including the signed-in Chrome route;
- **a sign-in or error page indexed as the page behind it**, past `.fux/refusals.toml`;
- **an answer marked `current` when its source has changed**;
- anything in a published package (`fux-engine`, `fux-core`, `fux-reader`, `fux-writer`, or the npm package) that differs from this repository.

A ranking you disagree with isn't a security issue. Please [open a wrong-answer issue](https://github.com/arpitarya/fux/issues/new?template=wrong_answer.yml) for those.

## Supported versions

Fixes go into the latest release only.
