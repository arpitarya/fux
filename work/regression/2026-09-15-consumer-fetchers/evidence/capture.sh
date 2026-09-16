FUX=/Users/arpitarya/my_programs/fux/.venv/bin/fux
cap() { echo "\$ fux $*"; "$FUX" "$@" 2>&1; echo "# exit $?"; echo; }
cap ingest
cap answer "pager rota"
echo "\$ fux doctor | grep 'fetcher bindings'"
"$FUX" doctor 2>&1 | grep -i "fetcher"
echo
echo "--- now the typo: fetch=glasbox, one letter short ---"
sed -i '' 's/fetch=glassbox/fetch=glasbox/' .fux/sources/urls
echo "\$ fux doctor | grep fetcher"
"$FUX" doctor 2>&1 | grep -i "fetcher"; echo "# doctor exit ${?}"
echo
cap ingest
