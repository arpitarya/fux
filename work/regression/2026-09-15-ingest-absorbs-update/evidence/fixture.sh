#!/bin/sh
# The corpus behind this run's capture — W-177, `fux ingest` absorbing
# `fux update`. A small repo with a docs tree, one PDF the type allowlist
# rejects, and TWO URLs served by a LOCAL FAKE fetcher.
#
# 🔴 **The fetcher writes a marker file every time it is called**, because this
# capture's whole subject is WHICH invocations go to the network. Reading the
# announcement off stderr is not enough: that line is exactly what a bug would
# leave in place while the fetch happened anyway.
#
#   sh fixture.sh /tmp/ingest-absorbs-demo
set -eu
root="${1:?usage: fixture.sh <dir>}"
rm -rf "$root"
mkdir -p "$root/.fux/sources" "$root/.fux/fetchers" "$root/docs"

cat > "$root/fux.toml" <<'TOML'
[sources]

[sources.url]
fetcher = ".fux/fetchers/http.py"
max_parallel = 4
TOML

printf 'docs\n' > "$root/.fux/sources/dirs"
: > "$root/.fux/pii.toml"

cat > "$root/.fux/sources/urls" <<'URLS'
https://wiki.test/runbook fetch=http meta=plain keep=true ttl=24h enrich=false archived=false update=auto
https://wiki.test/pinned fetch=http meta=plain keep=true ttl=24h enrich=false archived=false update=never
URLS

# The consumer-owned fetcher. Fixed bytes — a real request would make this run
# unreproducible — plus one line appended to `.fux/fetchers/CALLED` per call.
cat > "$root/.fux/fetchers/http.py" <<'FETCHER'
import pathlib


def fetch(url):
    log = pathlib.Path(__file__).with_name("CALLED")
    with log.open("a", encoding="utf-8") as fh:
        fh.write(url + "\n")
    return "# The oncall runbook\n\nwho carries the pager, and the escalation path\n"
FETCHER

cat > "$root/docs/pruning.md" <<'MD'
---
title: Why pruning failed
---
# Why pruning failed

The gate measured static pruning twice and it did not preserve candidate recall.
MD

cat > "$root/docs/onboarding.md" <<'MD'
---
title: Onboarding
---
# Onboarding

A new joiner reads `docs/pruning.md` first.
MD

printf '%%PDF-1.4 not really a pdf\n' > "$root/docs/architecture.pdf"

echo "fixture written to $root"
