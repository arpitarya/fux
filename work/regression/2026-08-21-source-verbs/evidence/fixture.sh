#!/bin/sh
# The corpus behind this run's capture — a small repo with a handbook, a docs
# tree, one PDF the type allowlist rejects, and one URL served by a LOCAL FAKE
# fetcher (no network; that is the consumer-fetcher boundary, not a shortcut).
#
#   sh fixture.sh /tmp/source-verbs-demo
set -eu
root="${1:?usage: fixture.sh <dir>}"
rm -rf "$root"
mkdir -p "$root/.fux/sources" "$root/.fux/fetchers" "$root/docs" "$root/handbook"

cat > "$root/fux.toml" <<'TOML'
[sources]

[sources.url]
fetcher = ".fux/fetchers/http.py"
TOML

printf 'docs\n' > "$root/.fux/sources/dirs"
: > "$root/.fux/sources/urls"

# The consumer-owned fetcher. Returns fixed bytes: what is being captured is
# the SURFACE, and a real request would make this run unreproducible.
# `fetch=cdp` on a line resolves to <fetchers dir>/cdp.py, so both exist.
for name in http cdp; do
cat > "$root/.fux/fetchers/$name.py" <<'FETCHER'
def fetch(url):
    return "# The oncall runbook\n\nwho carries the pager, and the escalation path\n"
FETCHER
done

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

cat > "$root/handbook/rota.md" <<'MD'
---
title: The rota
---
# The rota

Who is on call this week.
MD

printf '%%PDF-1.4 not really a pdf\n' > "$root/docs/architecture.pdf"

echo "fixture written to $root"
