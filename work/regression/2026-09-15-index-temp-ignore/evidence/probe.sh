#!/bin/sh
# The controlled probe behind W-185's only number. Two arms, same churn.
#
# ⚠ **The CONTROL is the load-bearing half.** "0 failures after the change" is
# indistinguishable from a window that did not happen to open that afternoon.
set -e
rm -rf gitprobe && mkdir gitprobe && cd gitprobe
git init -q . && git config user.email t@t.test && git config user.name T
mkdir -p d && echo hi > d/a.txt

run_arm() {                      # $1 = .gitignore contents
  printf '%s' "$1" > .gitignore
  git add -A && git commit -qm "arm" >/dev/null 2>&1 || true
  python3 ../churn.py & CH=$!
  fails=0; runs=0; end=$((SECONDS+18))
  while [ $SECONDS -lt $end ]; do
    runs=$((runs+1))
    git add -A >/dev/null 2>&1 || fails=$((fails+1))
  done
  wait $CH 2>/dev/null || true
  echo "$fails failures in $runs git add -A runs"
}

echo "ignored:   $(run_arm 'd/*.tmp')"
echo "control:   $(run_arm '')"
