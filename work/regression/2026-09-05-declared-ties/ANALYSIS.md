---
type: Analysis
run: 2026-09-05-declared-ties
date: 2026-09-05
---

# A correct change with no demonstration, and what that is worth

## 1 · The honest summary

**The tie-break is right and this run cannot show it working.** 0 of 2 450
top-5 rows tie on the playground; 3 of 1 200 at 10 000 documents; **0 queries
change order** on either.

That is not a failure of the change — it is a fact about the two corpora this
repo can reach, and the structural reasons are worth writing down because they
will bite the next measurement too:

- **`fux-playground` has one commit**, so every document shares an `mtime` and
  the recency signal is constant. It also has no supersession.
- **`t10000` is not a git repository**, so **no document has an `mtime` at
  all** — `git_commit_times` walks git and there is no git to walk.

🔴 **Read that second one again before trusting any future recency
measurement.** A corpus copied out of its repository silently loses the entire
recency prior, and nothing reports it. `fux doctor` does not check it; this run
found it by printing the field.

## 2 · The 4.38 % is not comparable, and saying so is the point

It was measured on **297 generated queries over a 495-document corpus** that
does not exist on this machine. Quoting *"we fixed 4.38 % of arbitrary
orderings"* would be attaching a number from one corpus to a change measured on
two others.

**What is defensible:** the tie-break makes the order *stated* rather than
arbitrary wherever it fires, at no cost to any score, and the two corpora here
say it fires rarely on them.

**The measurement that would settle it**, and it is not this one: the
`rank-flip` corpus, or any corpus with real commit history and real
supersession.

```bash
# what would make this run informative
git -C <corpus> log --oneline | wc -l      # > 1 commit, or recency is constant
python -c "import sys;sys.path.insert(0,'src');from fux.store import read_index;from pathlib import Path;\
rs=list(read_index(Path('<corpus>')).values());print(len({r.get('mtime') for r in rs}),'distinct mtimes')"
```

## 3 · `-priority` is a slot that cannot fire, and the code says so

`[priority]` has no fact beside its weight — `Weighting.priority_for` **is**
the weight, and `Weighting.of` multiplies the score by it. Different priorities
therefore produce different *scores* and never reach the tie-break; equal
priorities do not separate anything.

**It is kept** because it is what was ratified, because it costs nothing, and
because it is already correct if `[priority]` ever becomes a declaration that
does not multiply. A test asserts the current state and **fails the day it
changes**, which is the difference between a documented dead branch and an
undocumented one.

## 4 · What the run does establish

- **Safety.** 101 248 differential comparisons byte-identical, both skipping
  modes, at four `top` values.
- **The flag is meaningful.** All three ties at 10 000 documents marked exactly
  one row of five — each a row tied with the *sixth* document, off the page.
  That is the case a neighbour comparison on the truncated window would have
  silently un-marked, and it is the only thing here a caller would have seen.

## 5 · What this run cannot support

- Any claim that the tie-break improved retrieval. It changed no ordering here.
- Any comparison with the 4.38 % figure.
- Any claim about recency as a tie-break on a corpus with real history.
- Any claim at 10 000 documents beyond the tie rate itself.
