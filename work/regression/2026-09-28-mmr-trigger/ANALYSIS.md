---
type: Analysis
description: "Why step 7 cannot reach the floor on set-4-claude: 81 of 125 top-5 lists already span five communities, because 774 of 1 000 documents have no edge and each is its own community."
run: 2026-09-28-mmr-trigger
---

# Analysis: step 7's trigger is rare because the graph is sparse

- **Cause:** only **226 of 1 000** documents have an edge. Every other document is
  its own community (`graph/community.py`), so a top 5 with any unlinked document
  in it already spans at least two communities. **81 of 125 top-5 lists span five.**
- **So the premise does not hold here.** MMR helps when the head of the list is
  crowded with one cluster. On this corpus the head is already diverse by the
  graph's measure. The 7 crowded lists are
  `s4u-009 018 022 030 073 108 122`, and 5 of them have an alternative in 6–10.
- **What would change it:** a denser graph (a corpus whose documents link to
  each other), or a similarity measure other than communities, which is option C
  and needs its own ruling, key and sweep. Both are in the W-168 reopen-trigger.
- **Reproduce:** the command in [`evidence/trigger.py`](evidence/trigger.py)'s
  docstring, with the fux-lab arm tree present.
