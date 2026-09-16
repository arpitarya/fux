#!/bin/sh
# The corpus behind this run's capture — W-178, `fetch=` as a typed attribute.
# A repo with TWO URL lines: one through the shipped `http` fetcher, one through
# a `glassbox` fetcher that only this repo has.
#
# 🔴 **`glassbox.py` is the whole point.** Before 2026-09-15 the grammar
# rejected `fetch=glassbox` before anything looked at the directory, so this
# fixture could not be ingested at all.
#
#   sh fixture.sh /tmp/consumer-fetchers-demo
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
https://wiki.test/api fetch=http meta=plain keep=true ttl=24h enrich=false archived=false update=auto
https://wiki.test/rota fetch=glassbox meta=plain keep=true ttl=24h enrich=false archived=false update=auto
URLS

cat > "$root/.fux/fetchers/http.py" <<'FETCHER'
def fetch(url):
    return "# The API reference\n\nevery endpoint and what it returns\n"
FETCHER

# The consumer's OWN fetcher. Fux ships nothing called `glassbox`.
cat > "$root/.fux/fetchers/glassbox.py" <<'FETCHER'
def fetch(url):
    return "# The pager rota\n\nglassbox carried this one, and fux ships no such module\n"
FETCHER

cat > "$root/docs/onboarding.md" <<'MD'
---
title: Onboarding
---
# Onboarding

A new joiner reads the pager rota first.
MD

echo "fixture written to $root"
