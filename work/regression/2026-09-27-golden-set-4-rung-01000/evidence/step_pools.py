#!/usr/bin/env python3
"""W-168 steps 6–10 — a KEY-FREE CROSS-CHECK of each step's pool on set-4-claude (2026-09-28).

⚠ **Not the pool of record.** Step 10 cannot be tagged from text: the two rules
below (10a, 10b) give 5 and 13, either side of the stop line. Arpit ruled
(2026-09-28, L11 decision 13a) that the pools come from the key's own
`exercises` tag, counted by `score.py`'s `pools` block. This script stays as the
cross-check it became, and as the record of why the ruling was needed.

The generation-2 rule, carried forward
(`../../2026-09-24-golden-gen2-rung-01000/evidence/step_pools.py`): **tags come
from question TEXT and from `seed/` alone — never from the key.** The key's own
`exercises` field is unreachable (L11), and a step's later verdict tags its
questions by a rule like these, so the pool is counted with the same kind of tag
the verdict will use. Correctness comes only from `score.py`'s output under
`scores/`, which carries ids, ranks and flags. **Prints counts, never a question.**

A pool is *tagged ∩ answerable ∩ missing rank 1 ∩ in the returned ten* — the
rule of steps 1, 5 and 9 and of `compare/section-units` E1. Answerable is the
score row's `answered_unanswerable` being false (no row abstained, so every
unanswerable question is flagged there). Rank 5 is printed beside it, as on
generation 2.

⚠ **`informed`.** The whole-topic cue of step 7 was written after the question
text had been read; the other four rules restate SR-WORK-TESTDATA R6–R10 as
mechanical tests on `seed/`. Nothing here imports the engine: the tokenizer is a
plain word split, so a tag cannot move when the ranking code does.

    python3 work/regression/2026-09-27-golden-set-4-rung-01000/evidence/step_pools.py
"""

from __future__ import annotations

import collections
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[4]
GOLDEN = ROOT / "work" / "golden"
SEED = GOLDEN / "seed"
RUN = pathlib.Path(__file__).resolve().parents[1]
SET = "set-4-claude"

STOP = set(
    "a an and are as at be before by can do does for from get go how i if in is it its me my of on "
    "one or our per so that the their them there this to up us was we what when where which who why "
    "will with you your did should just any all ok".split()
)
WINDOW = 20  # step 6: "together" means inside one run of this many tokens
LONG_WORDS, LONG_HEADINGS = 3000, 8  # R10's long document
CUES = {  # step 9: I1 exactly as the 2026-09-24 pools drafted it and Arpit ruled it
    "procedure": [r"^how (do|should|can) (i|we)\b", r"^how to\b", r"\bsteps? to\b", r"^what (do|should) (i|we) do\b"],
    "rationale": [r"^why\b", r"\bwhat was the (reason|rationale)\b"],
    "reference": [r"^what is\b", r"^what does\b.*\bmean\b", r"^what'?s the\b", r"^define\b"],
}
WHOLE = r"\b(everything|all the|full picture|end to end|walk (me )?through|walkthrough|what should \w+ know|day to day|rules for)\b"


def words(text: str) -> list[str]:
    out = []
    for w in re.findall(r"[a-z0-9]+", text.lower()):
        if len(w) > 3 and w.endswith("s") and not w.endswith("ss"):
            w = w[:-1]
        out.append(w)
    return out


def body(text: str) -> str:
    return re.sub(r"\A---\n.*?\n---\n", "", text, flags=re.S)


def sections(text: str) -> list[list[str]]:
    return [words(s) for s in re.split(r"(?m)^#{1,6} ", body(text)) if s.strip()]


def seed_inputs():
    docs = {p.name: p.read_text(errors="replace") for p in sorted(SEED.glob("*")) if p.is_file()}
    toks = {k: set(words(body(v))) for k, v in docs.items()}

    # R10 — long documents first: omnibus by construction, so they are left out
    # when a topic's own words are found.
    long_docs = {n for n, v in docs.items() if len(body(v).split()) >= LONG_WORDS and len(re.findall(r"(?m)^#{1,6} ", v)) >= LONG_HEADINGS}

    # R6 — the triple topics, from file names only: a slug carried by all three intents.
    found: dict[str, dict[str, str]] = collections.defaultdict(dict)
    for name in docs:
        m = re.match(r"\d+-(procedure|decision|reference)-(.+)\.\w+$", name)
        if m:
            found[m.group(2)][m.group(1)] = name
    topics = {t: set(v.values()) for t, v in found.items() if len(v) == 3}
    # A doc outside the triple whose file name carries the slug's first word joins
    # the topic (R9's single-author rival).
    for t, members in topics.items():
        head = t.split("-")[0]
        members |= {n for n in docs if f"-{head}-" in n and n not in long_docs and not re.match(r"\d+-(procedure|decision|reference)-", n)}
    distinct = {}
    for t, members in topics.items():
        inside = set().union(*(toks[m] for m in members))
        outside = set().union(*(toks[n] for n in docs if n not in members and n not in long_docs))
        distinct[t] = {w for w in inside - outside - STOP if not w.isdigit()} | {t.split("-")[0]}

    # R9 — authority: a maintained doc (>= 3 authors, >= 4 commits) and an unhistoried rival.
    hist = collections.defaultdict(list)
    for line in (GOLDEN / "seed-history.tsv").read_text().splitlines():
        if line.strip():
            path, _date, who, _rev = line.split("\t")
            hist[pathlib.PurePosixPath(path).name].append(who)
    maintained = {n for n, w in hist.items() if len(w) >= 4 and len(set(w)) >= 3}
    authority = {t for t, members in topics.items() if members & maintained and any(m not in hist for m in members)}

    # R10 — the words only one long document carries.
    long_only = {n: toks[n] - STOP - set().union(*(toks[o] for o in docs if o != n)) for n in long_docs}
    return docs, topics, distinct, authority, long_docs, long_only


def together(sec: list[str], q: set[str]) -> set[str]:
    best: set[str] = set()
    for i in range(len(sec)):
        hit = q & set(sec[i : i + WINDOW])
        if len(hit) > len(best):
            best = hit
    return best


def proximity(q: set[str], docs: dict[str, str]) -> bool:
    """R7: one section holds >= 3 question words inside one window, and another
    section of the same doc holds those same words, never inside one window."""
    for text in docs.values():
        secs = sections(text)
        for i, s in enumerate(secs):
            close = together(s, q)
            if len(close) < 3:
                continue
            for j, o in enumerate(secs):
                if j != i and close <= set(o) and len(together(o, close)) < len(close):
                    return True
    return False


def main() -> None:
    docs, topics, distinct, authority, long_docs, long_only = seed_inputs()
    print(f"triple topics {len(topics)} · authority topics {len(authority)} · long docs {len(long_docs)}")
    questions = {}
    for line in (GOLDEN / "questions" / f"{SET}.jsonl").read_text().splitlines():
        if line.strip():
            row = json.loads(line)
            questions[row["id"]] = row["question"]
    rows = {r["id"]: r for r in json.loads((RUN / "scores" / "single" / "rung-01000" / f"{SET}.json").read_text())["rows"]}
    assert set(rows) == set(questions), "the score and the question set disagree on ids"

    tags: dict[str, set] = {k: set() for k in ("6 proximity", "7 diversity", "8 authority", "9 intent", "10a section", "10b section")}
    toks = {n: set(words(body(v))) for n, v in docs.items()}
    secs = {n: [set(x) for x in sections(docs[n])] for n in long_docs}
    for qid, q in questions.items():
        low = q.lower().strip()
        qw = set(words(q)) - STOP
        on = {t for t in topics if qw & distinct[t]}
        whole = bool(re.search(WHOLE, low))
        if proximity(qw, docs):
            tags["6 proximity"].add(qid)
        if on and whole:
            tags["7 diversity"].add(qid)
        if on & authority and not whole:
            tags["8 authority"].add(qid)
        if on and any(re.search(p, low) for ps in CUES.values() for p in ps):
            tags["9 intent"].add(qid)
        # 10a: a word only one long document carries.
        if any(qw & long_only[n] for n in long_docs):
            tags["10a section"].add(qid)
        # 10b: one section of a long document covers >= half the question's words,
        # and at least as many as any whole short document does.
        if qw:
            best_long = max(len(qw & sec) for n in long_docs for sec in secs[n])
            best_short = max(len(qw & toks[n]) for n in docs if n not in long_docs)
            if best_long >= best_short and best_long / len(qw) >= 0.5:
                tags["10b section"].add(qid)

    print(SET)
    print("  step           tagged answerable miss@1 reorderable@1 miss@5 reorderable@5 not-in-top10")
    for step, ids in tags.items():
        ans = [i for i in ids if not rows[i]["answered_unanswerable"]]
        m1 = [i for i in ans if not rows[i]["hit@1"]]
        m5 = [i for i in ans if not rows[i]["hit@5"]]
        print(f"  {step:14} {len(ids):6} {len(ans):10} {len(m1):6} {sum(rows[i]['hit@10'] for i in m1):13}"
              f" {len(m5):6} {sum(rows[i]['hit@10'] for i in m5):13} {sum(not rows[i]['hit@10'] for i in ans):12}")


if __name__ == "__main__":
    main()
