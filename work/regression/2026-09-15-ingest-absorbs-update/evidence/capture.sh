FUX=/Users/arpitarya/my_programs/fux/.venv/bin/fux
cap() { echo "\$ fux $*"; "$FUX" "$@" 2>&1; echo "# exit $?"; echo; }
called() { echo "--- .fux/fetchers/CALLED ($1) ---"; cat .fux/fetchers/CALLED 2>/dev/null || echo "(the fetcher has never been called)"; echo; }
cap ingest
called "after the first bare ingest"
cap ingest
called "after a second bare ingest"
cap ingest --no-fetch
called "after --no-fetch"
cap ingest --refetch-all
called "after --refetch-all"
cap ingest --check
cap ingest --check --json
cap ingest --failed
cap ingest --check --list-skipped
cap ingest --list-skipped
cap ingest https://wiki.test/runbook
cap ingest docs/nothing.md
cap ingest --no-fetch docs/nothing.md
cap update
cap ingest --refresh-urls
called "at the end"
