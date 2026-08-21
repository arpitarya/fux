#!/bin/sh
# The corpus behind this run's capture. 1 203 documents, each one heading and
# one body line, 37 shared terms — large enough that extract, edges, write,
# read, codes and postings all clear progress.THRESHOLD (~200).
#
#   sh fixture.sh /tmp/progress-demo
set -eu
root="${1:?usage: fixture.sh <dir>}"
mkdir -p "$root/.fux/sources" "$root/docs"
printf '[sources]\n' > "$root/fux.toml"
printf 'docs\n' > "$root/.fux/sources/dirs"
python3 - "$root" <<'PY'
import pathlib, sys
docs = pathlib.Path(sys.argv[1]) / "docs"
for i in range(1203):
    (docs / f"doc{i:04d}.md").write_text(
        f"---\ntitle: Document {i}\n---\n# Document {i}\n\n"
        f"term{i % 41} the committed index and the refer plane, pruning gate {i}.\n"
    )
PY
echo "fixture written to $root"
