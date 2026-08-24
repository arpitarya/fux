"""The Porter stemmer, stdlib-only — analyzer v2's morphology step.

**Why hand-rolled.** L1 is stdlib-only, and every packaged stemmer
(`nltk`, `snowballstemmer`, `PyStemmer`) is a dependency. Porter is a fully
specified algorithm with a published test vocabulary, so "hand-rolled" here
means "transcribed", not "invented" — which is the same reason the BM25F
scorer is hand-rolled and the same standard it is held to.

**Why stem at all.** Recall on morphology: `deploy` / `deployment` /
`deploying` are one concept and three postings without it. Doc 02 of the ideal
set names it as one of the analyzer changes worth doing, alongside identifier
splitting.

**Where it sits in the pipeline, and why the order is not negotiable:**

    split -> lower -> stopword -> STEM -> hash

The hash is taken of the **final analyzed token**. Ingest and query share this
module for exactly that reason: if the two sides stem differently, or stem at
different points, they hash different strings and nothing matches — silently,
with no error and no empty result to signal it.

**What is deliberately not stemmed** (see `should_stem`): anything carrying a
digit or an underscore, and anything shorter than three characters. A version
string, a hex id or an identifier fragment has no morphology to strip, and
Porter's rules will happily strip characters that were load-bearing —
`sha256` and `sha25` are not the same term.

Reference: M.F. Porter, "An algorithm for suffix stripping", Program 14(3),
1980. Step numbering below follows the paper.
"""

from __future__ import annotations

_VOWELS = frozenset("aeiou")


def _is_consonant(word: str, i: int) -> bool:
    """`y` is the awkward one: a consonant unless preceded by a consonant."""
    ch = word[i]
    if ch in _VOWELS:
        return False
    if ch == "y":
        return i == 0 or not _is_consonant(word, i - 1)
    return True


def _measure(stem: str) -> int:
    """`m` — the number of VC sequences in [C](VC){m}[V]."""
    m = 0
    i = 0
    n = len(stem)
    while i < n and _is_consonant(stem, i):
        i += 1
    while i < n:
        while i < n and not _is_consonant(stem, i):
            i += 1
        if i >= n:
            break
        m += 1
        while i < n and _is_consonant(stem, i):
            i += 1
    return m


def _has_vowel(stem: str) -> bool:
    return any(not _is_consonant(stem, i) for i in range(len(stem)))


def _double_consonant_suffix(word: str) -> bool:
    return (
        len(word) >= 2
        and word[-1] == word[-2]
        and _is_consonant(word, len(word) - 1)
    )


def _cvc(word: str) -> bool:
    """consonant-vowel-consonant where the final one is not w, x or y."""
    if len(word) < 3:
        return False
    if not (
        _is_consonant(word, len(word) - 3)
        and not _is_consonant(word, len(word) - 2)
        and _is_consonant(word, len(word) - 1)
    ):
        return False
    return word[-1] not in "wxy"


def _replace(word: str, suffix: str, repl: str, min_m: int) -> str | None:
    if not word.endswith(suffix):
        return None
    stem = word[: len(word) - len(suffix)]
    return stem + repl if _measure(stem) > min_m else None


_STEP2 = (
    ("ational", "ate"), ("tional", "tion"), ("enci", "ence"), ("anci", "ance"),
    ("izer", "ize"), ("bli", "ble"), ("alli", "al"), ("entli", "ent"),
    ("eli", "e"), ("ousli", "ous"), ("ization", "ize"), ("ation", "ate"),
    ("ator", "ate"), ("alism", "al"), ("iveness", "ive"), ("fulness", "ful"),
    ("ousness", "ous"), ("aliti", "al"), ("iviti", "ive"), ("biliti", "ble"),
    ("logi", "log"),
)

_STEP3 = (
    ("icate", "ic"), ("ative", ""), ("alize", "al"), ("iciti", "ic"),
    ("ical", "ic"), ("ful", ""), ("ness", ""),
)

_STEP4 = (
    "al", "ance", "ence", "er", "ic", "able", "ible", "ant", "ement",
    "ment", "ent", "ou", "ism", "ate", "iti", "ous", "ive", "ize",
)


def should_stem(token: str) -> bool:
    """Words only.

    A token with a digit or an underscore is an identifier, a version or an id,
    and Porter's rules strip characters that were carrying meaning in it.
    Two-character tokens have nothing to strip.
    """
    if len(token) < 3:
        return False
    return token.isalpha()


def stem(word: str) -> str:
    """Porter-stem one already-lowercased token. Returns it unchanged when
    `should_stem` says it is not a word."""
    if not should_stem(word):
        return word

    # Step 1a — plurals
    if word.endswith("sses"):
        word = word[:-2]
    elif word.endswith("ies"):
        word = word[:-2]
    elif word.endswith("ss"):
        pass
    elif word.endswith("s"):
        word = word[:-1]

    # Step 1b — -ed / -ing
    second_pass = False
    if word.endswith("eed"):
        if _measure(word[:-3]) > 0:
            word = word[:-1]
    elif word.endswith("ed") and _has_vowel(word[:-2]):
        word = word[:-2]
        second_pass = True
    elif word.endswith("ing") and _has_vowel(word[:-3]):
        word = word[:-3]
        second_pass = True
    if second_pass:
        if word.endswith(("at", "bl", "iz")):
            word += "e"
        elif _double_consonant_suffix(word) and not word.endswith(("l", "s", "z")):
            word = word[:-1]
        elif _measure(word) == 1 and _cvc(word):
            word += "e"

    # Step 1c — terminal y
    if word.endswith("y") and _has_vowel(word[:-1]):
        word = word[:-1] + "i"

    # Step 2 / 3 — derivational suffixes
    for suffix, repl in _STEP2:
        out = _replace(word, suffix, repl, 0)
        if out is not None:
            word = out
            break
    for suffix, repl in _STEP3:
        out = _replace(word, suffix, repl, 0)
        if out is not None:
            word = out
            break

    # Step 4 — strip when m > 1
    for suffix in _STEP4:
        if word.endswith(suffix):
            stem_ = word[: len(word) - len(suffix)]
            if suffix in ("ion",) and not stem_.endswith(("s", "t")):
                continue
            if _measure(stem_) > 1:
                word = stem_
            break
    else:
        if word.endswith("ion"):
            stem_ = word[:-3]
            if _measure(stem_) > 1 and stem_.endswith(("s", "t")):
                word = stem_

    # Step 5a / 5b — terminal e and doubled l
    if word.endswith("e"):
        m = _measure(word[:-1])
        if m > 1 or (m == 1 and not _cvc(word[:-1])):
            word = word[:-1]
    if word.endswith("ll") and _measure(word) > 1:
        word = word[:-1]

    return word
