/** The Porter stemmer — analyzer v2's morphology step.
 *
 * Twin of `src/fux/query/stem.py`. **Transcribed, not reimplemented**: Porter
 * is a fully specified algorithm with a published test vocabulary, and every
 * departure fux makes from the textbook (see `shouldStem`) is a departure the
 * Python side already made. A difference here is a silent no-match, not an
 * error — the query hashes a string the index never wrote.
 *
 * Reference: M.F. Porter, "An algorithm for suffix stripping", Program 14(3),
 * 1980. Step numbering follows the paper, as it does on the Python side.
 */

const VOWELS = new Set(["a", "e", "i", "o", "u"]);

function isConsonant(word, i) {
  const ch = word[i];
  if (VOWELS.has(ch)) return false;
  if (ch === "y") return i === 0 || !isConsonant(word, i - 1);
  return true;
}

/** `m` — the number of VC sequences in [C](VC){m}[V]. */
function measure(stemStr) {
  let m = 0;
  let i = 0;
  const n = stemStr.length;
  while (i < n && isConsonant(stemStr, i)) i++;
  while (i < n) {
    while (i < n && !isConsonant(stemStr, i)) i++;
    if (i >= n) break;
    m++;
    while (i < n && isConsonant(stemStr, i)) i++;
  }
  return m;
}

function hasVowel(stemStr) {
  for (let i = 0; i < stemStr.length; i++) if (!isConsonant(stemStr, i)) return true;
  return false;
}

function doubleConsonantSuffix(word) {
  return word.length >= 2
    && word[word.length - 1] === word[word.length - 2]
    && isConsonant(word, word.length - 1);
}

/** consonant-vowel-consonant where the final one is not w, x or y. */
function cvc(word) {
  if (word.length < 3) return false;
  const n = word.length;
  if (!(isConsonant(word, n - 3) && !isConsonant(word, n - 2) && isConsonant(word, n - 1))) {
    return false;
  }
  return !"wxy".includes(word[n - 1]);
}

function replace(word, suffix, repl, minM) {
  if (!word.endsWith(suffix)) return null;
  const s = word.slice(0, word.length - suffix.length);
  return measure(s) > minM ? s + repl : null;
}

const STEP2 = [
  ["ational", "ate"], ["tional", "tion"], ["enci", "ence"], ["anci", "ance"],
  ["izer", "ize"], ["bli", "ble"], ["alli", "al"], ["entli", "ent"],
  ["eli", "e"], ["ousli", "ous"], ["ization", "ize"], ["ation", "ate"],
  ["ator", "ate"], ["alism", "al"], ["iveness", "ive"], ["fulness", "ful"],
  ["ousness", "ous"], ["aliti", "al"], ["iviti", "ive"], ["biliti", "ble"],
  ["logi", "log"],
];

const STEP3 = [
  ["icate", "ic"], ["ative", ""], ["alize", "al"], ["iciti", "ic"],
  ["ical", "ic"], ["ful", ""], ["ness", ""],
];

const STEP4 = [
  "al", "ance", "ence", "er", "ic", "able", "ible", "ant", "ement",
  "ment", "ent", "ou", "ism", "ate", "iti", "ous", "ive", "ize",
];

/** Python's `str.isalpha()` — Unicode alphabetic, NOT `/^[a-z]+$/`.
 *
 * ⚠ This is a real divergence risk and the reason it is spelled out. Python's
 * `isalpha` is true for `café` and `中文`; a naive `[a-zA-Z]` test is not, and
 * would stem tokens Python leaves alone. `\p{Alphabetic}` is the Unicode
 * property Python uses.
 */
const ALPHA_RE = /^\p{Alphabetic}+$/u;

/** Words only: no digits, no underscores, at least three characters. */
export function shouldStem(token) {
  if (token.length < 3) return false;
  return ALPHA_RE.test(token);
}

/** Porter-stem one already-lowercased token. */
export function stem(word) {
  if (!shouldStem(word)) return word;

  // Step 1a — plurals
  if (word.endsWith("sses")) word = word.slice(0, -2);
  else if (word.endsWith("ies")) word = word.slice(0, -2);
  else if (word.endsWith("ss")) { /* unchanged */ }
  else if (word.endsWith("s")) word = word.slice(0, -1);

  // Step 1b — -ed / -ing
  let secondPass = false;
  if (word.endsWith("eed")) {
    if (measure(word.slice(0, -3)) > 0) word = word.slice(0, -1);
  } else if (word.endsWith("ed") && hasVowel(word.slice(0, -2))) {
    word = word.slice(0, -2);
    secondPass = true;
  } else if (word.endsWith("ing") && hasVowel(word.slice(0, -3))) {
    word = word.slice(0, -3);
    secondPass = true;
  }
  if (secondPass) {
    if (word.endsWith("at") || word.endsWith("bl") || word.endsWith("iz")) {
      word += "e";
    } else if (
      doubleConsonantSuffix(word)
      && !(word.endsWith("l") || word.endsWith("s") || word.endsWith("z"))
    ) {
      word = word.slice(0, -1);
    } else if (measure(word) === 1 && cvc(word)) {
      word += "e";
    }
  }

  // Step 1c — terminal y
  if (word.endsWith("y") && hasVowel(word.slice(0, -1))) {
    word = word.slice(0, -1) + "i";
  }

  // Step 2 / 3 — derivational suffixes
  for (const [suffix, repl] of STEP2) {
    const out = replace(word, suffix, repl, 0);
    if (out !== null) { word = out; break; }
  }
  for (const [suffix, repl] of STEP3) {
    const out = replace(word, suffix, repl, 0);
    if (out !== null) { word = out; break; }
  }

  // Step 4 — strip when m > 1. Python's for/else: the `ion` branch runs only
  // when NO suffix matched, which is why this needs an explicit flag.
  let matched = false;
  for (const suffix of STEP4) {
    if (word.endsWith(suffix)) {
      const s = word.slice(0, word.length - suffix.length);
      matched = true;
      if (suffix === "ion" && !(s.endsWith("s") || s.endsWith("t"))) continue;
      if (measure(s) > 1) word = s;
      break;
    }
  }
  if (!matched && word.endsWith("ion")) {
    const s = word.slice(0, -3);
    if (measure(s) > 1 && (s.endsWith("s") || s.endsWith("t"))) word = s;
  }

  // Step 5a / 5b — terminal e and doubled l
  if (word.endsWith("e")) {
    const m = measure(word.slice(0, -1));
    if (m > 1 || (m === 1 && !cvc(word.slice(0, -1)))) word = word.slice(0, -1);
  }
  if (word.endsWith("ll") && measure(word) > 1) word = word.slice(0, -1);

  return word;
}
