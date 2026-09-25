/** `.fux/tune.toml`, read. The reader half of `src/fux/tune.py`.
 *
 * 🔴 **This file closes [SR-NODE-SEARCH](../../../records/0153_node-search.md)
 * decision 8**, which was filed as a gap rather than a decision: Node read no
 * tune file at all, so a consumer who ran `fux tune` got **a different ranked
 * list from the same index at the same engine version**, with nothing saying
 * so. Measured on fux's own repo, whose tune sets `rerank_weight = 0.3`:
 * 90 of 174 comparisons discordant against a tuned Python, 0 of 174 against
 * `--no-tune`.
 *
 * ## What is here, and what is deliberately not
 *
 * `tune.py` is 739 lines; most of them are the **writer's** half — `specimen()`,
 * the commented starter `fux setup` writes, and the prose that explains each
 * key to a person editing it. Node never writes this file, so none of that is
 * transcribed. What IS transcribed, exactly:
 *
 * - **The defaults**, because they are the answer when the file is absent.
 * - **The closed key set.** An unknown table or key is a REFUSAL. This is the
 *   one file that can change every answer without changing a byte of the
 *   index, so a typo must not fail silently — and a Node reader that shrugged
 *   at a key Python refuses would disagree about which files load.
 * - **The value validators**, including the integer/float distinction: `[graph]
 *   iterations = 3.0` is an error and `3` is not (`wasFloat`, `config/toml.mjs`).
 * - **The error COLLECTION.** One error at a time turns a hand-edited file into
 *   a guessing game; ten together name the cause.
 *
 * `[index]` is validated and then dropped, exactly as Python does: those keys
 * change committed bytes at ingest, Node does not ingest, and `--no-tune` does
 * not reach them. Validating them anyway means `fux ask` reports a bad
 * `[index]` value in both runtimes rather than one.
 *
 * R5: **absent, empty or all-commented = every default; malformed = a hard
 * error.** A file that exists and cannot be parsed means somebody edited it and
 * got it wrong; degrading there would answer with the engine's ranking while
 * the reader believed it was theirs (SR-TUNE decision 10).
 */
import { readFileSync, statSync } from "node:fs";
import { join } from "node:path";
import { FuxError } from "../errors.mjs";
import { parseToml, wasFloat } from "./toml.mjs";
import { ANCHOR, B, FIELD_WEIGHTS, K1, Scoring } from "../query/bm25f.mjs";
import { DOC_COVERAGE_FLOOR, SEPARATION_FLOOR } from "../query/confidence.mjs";
import { TF_FIELDS } from "../store/format.mjs";
import { cmpCodePoints } from "../compat/pyfloat.mjs";
// `ask_kinds` is validated against the kinds the index mints, at load — the
// same list `graph --kinds` refuses against at the CLI boundary.
import { EDGE_KINDS } from "../graph/walk.mjs";

export const TUNE_NAME = ".fux/tune.toml";

//: At most this many semantic errors are reported together.
const MAX_REPORTED = 10;

//: The `[bm25f]` field-weight keys ARE the field names (Arpit, 2026-08-27):
//: inside a table already named `bm25f` a `_weight` suffix is noise.
const FIELD_KEYS = TF_FIELDS;

//: Old spelling -> new, for the migration message only.
const LEGACY_FIELD_KEYS = new Map(TF_FIELDS.map((name) => [`${name}_weight`, name]));

export const DEFAULT_MAX_PHRASES = 32;
export const DEFAULT_MAX_TABLE_ROWS = 20000;
export const INDEX_TABLE = "index";

//: The closed key set. Table -> keys. Adding one here is a change to SR-TUNE.
const SCHEMA = {
  bm25f: ["k1", "b", ...FIELD_KEYS, "anchor"],
  ranking: ["rerank_weight", "expand_weight", "rm3_weight"],
  // The six `ask_*` keys are W-161's graph tier. They are parsed and carried
  // here so a consumer's committed `tune.toml` is accepted identically by both
  // readers; whether the Node reader COMPOSES the tier is
  // SR-NODE-SEARCH's, and today it does not — see the divergence note there.
  // A key this reader refused and Python accepted would make the same file
  // valid in one reader and an error in the other, which is the one asymmetry
  // the config parity test exists to forbid.
  graph: [
    "damping", "iterations", "laziness", "hop_decay", "expand_limit", "seed_depth",
    "ask_boost", "ask_related", "ask_kinds", "ask_link_idf", "ask_max_hops",
    "ask_related_limit",
  ],
  refer: ["budget", "per_doc_fraction", "min_passage_bytes", "max_passage_bytes"],
  confidence: ["separation_floor", "doc_coverage_floor"],
  // ⚠ THE EXCEPTION — read by ingest, changes committed bytes, untouched by
  // `--no-tune`. Node validates it and carries none of it.
  [INDEX_TABLE]: ["max_phrases", "max_table_rows"],
  // `[priority]` is the one open table: its keys are the consumer's own
  // source entries, which fux cannot know in advance.
  priority: [],
};

const OPEN_TABLES = new Set(["priority"]);

//: Keys fux ITSELF shipped and then removed. `"<table>.<key>" -> the rest of
//: the sentence`, so the error names the removal and its date rather than
//: reporting an unknown key on a line the consumer copied out of fux's own
//: specimen. The Python twin is `tune._REMOVED_KEYS`; the two must agree, or a
//: Node reader shrugs at a file Python refuses.
const REMOVED_KEYS = new Map([
  ["ranking.archived_weight",
    "was REMOVED on 2026-09-13 (W-152). Being retired is a FACT, not a weight. " +
    "Delete the key; ranking is unchanged, because it shipped at 1.0. The FACT " +
    "is untouched and already reaches you: `archived=true` in .fux/sources/dirs, " +
    "the `archived` record property, the `[archived]` marker in prose output and " +
    "`archived: bool` on every JSON hit -- BRANCH ON THAT. " + "Each of the three priors shipped as a no-op, so DELETING the key changes " +
    "nothing you can measure; what went is a global multiplier no single value " +
    "can set correctly -- measured across 26 intent-split probes, every value " +
    "that perfects current-seeking dismantles history-seeking one probe for one " +
    "(work/regression/2026-09-12-priors-and-tables/VERDICT-W143.md)"],
  ["ranking.recency_half_life_days",
    "was REMOVED on 2026-09-13 (W-152). At a half-life of a year or less it took " +
    "history-seeking queries to ZERO of thirteen: a per-document decay cannot " +
    "carry a per-query distinction, because `what do we do now?` and `what did we " +
    "do before?` want opposite orderings out of one corpus. Delete the key; " +
    "ranking is unchanged, because it shipped at 0.0 (off). `mtime` is still " +
    "committed on every record and still breaks a tie in favour of the newer " +
    "document. " + "Each of the three priors shipped as a no-op, so DELETING the key changes " +
    "nothing you can measure; what went is a global multiplier no single value " +
    "can set correctly -- measured across 26 intent-split probes, every value " +
    "that perfects current-seeking dismantles history-seeking one probe for one " +
    "(work/regression/2026-09-12-priors-and-tables/VERDICT-W143.md)"],
  ["ranking.superseded_weight",
    "was REMOVED on 2026-09-13 (W-151). Supersession is a FACT, not a weight: " +
    "no multiplier decides which document supersedes another, and the only band " +
    "of values that ordered a corpus sensibly had its lower edge set by an " +
    "UNRELATED document -- so adding a document moved the correct value. Delete " +
    "the key; ranking is unchanged, because it shipped at 1.0. The FACT is " +
    "untouched: `supersedes:` in frontmatter, the `superseded` record property, " +
    "the graph edge, `fux explain`, and the declared tie-break that puts a live " +
    "document above a retired one at an equal score"],
]);

/** Every tunable, resolved. Build it with `loadTune`; the defaults are the engine's. */
export class Tune {
  constructor(values = {}) {
    // [bm25f]
    this.k1 = K1;
    this.b = B;
    this.fieldWeights = FIELD_WEIGHTS;
    // W-168 step 1 — the anchor field, folded at read time from other
    // documents' edges. NOT in `fieldWeights`: that array is aligned with
    // TF_FIELDS, the five fields a record commits an `flen` for. 0 = off; the
    // default ANCHOR (1.0) is ON since its pre-registered PASS on 2026-09-24.
    this.anchorWeight = ANCHOR;
    // [ranking]
    // The three DOCUMENT priors were removed on 2026-09-13 (W-151, W-152).
    this.rerankWeight = 0.0;
    this.expandWeight = 0.2;
    // W-168 step 5 — RM3 feedback terms' weight. 0 = off, and off runs no first
    // pass at all; it turns on only on a pre-registered PASS.
    this.rm3Weight = 0.0;
    // [graph]
    this.damping = 0.85;
    this.iterations = 3;
    this.laziness = 0.5;
    this.hopDecay = 0.5;
    this.expandLimit = 10;
    this.seedDepth = 5;
    // W-161's graph tier. Carried, not composed — see SCHEMA above.
    this.askBoost = true;
    this.askRelated = true;
    this.askKinds = "ref";
    this.askLinkIdf = true;
    this.askMaxHops = 1;
    this.askRelatedLimit = 5;
    // [confidence]
    this.separationFloor = SEPARATION_FLOOR;
    this.docCoverageFloor = DOC_COVERAGE_FLOOR;
    // [refer]
    this.budget = 8000;
    this.perDocFraction = 0.5;
    this.minPassageBytes = 120;
    this.maxPassageBytes = 4000;
    //: `[priority]`, sorted longest-key-first so a reader can stop at the
    //: first match. The resolution itself lives on `query/rank.mjs`'s
    //: `Weighting` — this class carries the data, the scorer carries the rule.
    this.priority = [];
    Object.assign(this, values);
    Object.freeze(this);
  }

  /** The three-part BM25F parameter set, as one object. */
  get scoring() { return new Scoring(this.k1, this.b, this.fieldWeights, this.anchorWeight); }
}

export const DEFAULT_TUNE = new Tune();

/** Gathers semantic errors so a hand-edited file reports them together. */
class Collector {
  constructor(label) { this.label = label; this.errors = []; }
  add(message) { this.errors.push(message); }
  raiseIfAny() {
    if (!this.errors.length) return;
    const shown = this.errors.slice(0, MAX_REPORTED);
    const more = this.errors.length - shown.length;
    const tail = more > 0 ? `\n  ... and ${more} more` : "";
    throw new FuxError(`${this.label}:\n  ` + shown.join("\n  ") + tail);
  }
}

/** Python's `repr` for the values that reach an error message. */
function repr(value) {
  if (typeof value === "string") return `'${value}'`;
  if (value === true) return "True";
  if (value === false) return "False";
  if (value === null || value === undefined) return "None";
  return String(value);
}

function number(c, table, key, value, dflt) {
  if (typeof value !== "number") {
    c.add(`[${table}] ${key} must be a number (got ${repr(value)})`);
    return dflt;
  }
  return value;
}

function positive(c, table, key, value, dflt) {
  const v = number(c, table, key, value, dflt);
  if (v <= 0) {
    c.add(`[${table}] ${key} must be greater than zero — at zero the term it scales vanishes (got ${v})`);
    return dflt;
  }
  return v;
}

function nonNegative(c, table, key, value, dflt) {
  const v = number(c, table, key, value, dflt);
  if (v < 0) {
    c.add(
      `[${table}] ${key} must not be negative — a negative multiplier inverts ` +
      `the ordering, which is broken rather than aggressive (got ${v})`,
    );
    return dflt;
  }
  return v;
}

function fraction(c, table, key, value, dflt) {
  const v = number(c, table, key, value, dflt);
  if (!(v >= 0.0 && v <= 1.0)) {
    c.add(
      `[${table}] ${key} must be between 0 and 1 — 0 turns the effect off ` +
      `entirely, 1 applies it in full (got ${v})`,
    );
    return dflt;
  }
  return v;
}

/** A TOML **integer**, at least `floor`. `3.0` is not an integer here, because
 *  it is not one in `tune.py` either — see `config/toml.mjs`'s `wasFloat`. */
function atLeast(c, tbl, table, key, value, dflt, floor) {
  if (typeof value !== "number" || !Number.isInteger(value) || wasFloat(tbl, key)) {
    c.add(`[${table}] ${key} must be a whole number (got ${repr(value)})`);
    return dflt;
  }
  if (value < floor) {
    c.add(`[${table}] ${key} must be at least ${floor} (got ${value})`);
    return dflt;
  }
  return value;
}

/**
 * A strict boolean. `1`/`0` are refused rather than coerced — the twin of
 * Python's `_boolean`, and for its reason: a consumer who writes
 * `ask_boost = 1` is told the key is a boolean instead of getting a silent
 * `true` out of a file that never said so.
 */
function boolean(c, table, key, value, dflt) {
  if (typeof value !== "boolean") {
    c.add(`[${table}] ${key} must be true or false (got ${repr(value)})`);
    return dflt;
  }
  return value;
}

/**
 * A comma-separated list of edge kinds the index actually mints.
 *
 * Validated at LOAD rather than where a walk would run: an unknown kind walks
 * nothing, and a walk over no edges returns an empty neighbourhood that cannot
 * be told from a corpus with no links at all.
 */
function edgeKinds(c, table, key, value, dflt) {
  if (typeof value !== "string") {
    c.add(`[${table}] ${key} must be a string (got ${repr(value)})`);
    return dflt;
  }
  const named = value.split(",").map((k) => k.trim()).filter((k) => k.length > 0);
  if (named.length === 0) {
    c.add(`[${table}] ${key} names no edge kind; the kinds this index mints are ${EDGE_KINDS.join(", ")}`);
    return dflt;
  }
  const unknown = [...new Set(named.filter((k) => !EDGE_KINDS.includes(k)))].sort();
  if (unknown.length > 0) {
    c.add(
      `[${table}] ${key} names ${unknown.join(", ")}, which is not an edge kind; ` +
      `the kinds this index mints are ${EDGE_KINDS.join(", ")}`,
    );
    return dflt;
  }
  return named.join(",");
}

function has(table, key) {
  return table !== null && typeof table === "object" && Object.prototype.hasOwnProperty.call(table, key);
}

/** `[index]`'s values, validated and discarded — see the module docstring. */
function checkIndexValues(c, table) {
  const t = table && typeof table === "object" ? table : {};
  if (has(t, "max_phrases")) {
    atLeast(c, t, INDEX_TABLE, "max_phrases", t.max_phrases, DEFAULT_MAX_PHRASES, 1);
  }
  if (has(t, "max_table_rows")) {
    atLeast(c, t, INDEX_TABLE, "max_table_rows", t.max_table_rows, DEFAULT_MAX_TABLE_ROWS, 1);
  }
}

/** A committed file people edit will eventually carry `<<<<<<<`, and the TOML
 *  error for one points three lines below the cause. */
function rejectConflictMarkers(label, text) {
  for (const marker of ["<<<<<<< ", "=======\n", ">>>>>>> "]) {
    if (text.includes(marker)) {
      throw new FuxError(
        `${label}: unresolved merge conflict — the file still carries conflict markers. ` +
        "Resolve it by hand and keep one side; fux never rewrites this file",
      );
    }
  }
}

/** Read `.fux/tune.toml`. Absent, empty or all-commented means every default.
 *
 * `enabled=false` is `--no-tune`: the file is not read at all, so the answer is
 * the engine's own (SR-TUNE decision 11). */
export function loadTune(root, { enabled = true } = {}) {
  if (!enabled) return DEFAULT_TUNE;

  const path = join(root, ".fux", "tune.toml");
  let raw;
  try {
    if (!statSync(path).isFile()) return DEFAULT_TUNE;
    raw = readFileSync(path, "utf8");
  } catch {
    return DEFAULT_TUNE;
  }

  const label = `${root}/${TUNE_NAME}`;
  rejectConflictMarkers(label, raw);
  const data = parseToml(raw, label);
  if (!Object.keys(data).length) return DEFAULT_TUNE;

  if (has(data, "dense")) {
    throw new FuxError(
      `${label}: [dense] was REMOVED on 2026-08-25 along with the embedding model, ` +
      "the committed per-chunk vectors and `ask --hybrid`. The lane never earned " +
      "its cost -- DENSE-CHUNK measured 0 fixed / 2 broken at every setting that " +
      "fires (work/regression/2026-08-24-dense-lane-gate/). Delete the table; " +
      "ranking is unchanged, because `mode` defaulted to `off`",
    );
  }

  const unknownTables = Object.keys(data).filter((k) => !(k in SCHEMA));
  if (unknownTables.length) {
    throw new FuxError(
      `${label}: unknown table(s) ${JSON.stringify(unknownTables.sort())} — ` +
      `known: ${JSON.stringify(Object.keys(SCHEMA).sort())}. ` +
      "The key set is closed on purpose: this is the one file that can change " +
      "every answer without changing a byte of the index (all but [index]), so a " +
      "typo here must not fail silently",
    );
  }
  for (const [name, value] of Object.entries(data)) {
    if (value === null || typeof value !== "object" || Array.isArray(value)) {
      throw new FuxError(`${label}: \`${name}\` must be a table (a \`[${name}]\` section), not a bare key`);
    }
    if (OPEN_TABLES.has(name)) continue;
    const unknownKeys = Object.keys(value).filter((k) => !SCHEMA[name].includes(k));
    if (unknownKeys.length) {
      // A key fux removed is named as removed. Sorted so two removed keys in
      // one table report the same one every run (L3 reaches errors too).
      const removed = unknownKeys.filter((k) => REMOVED_KEYS.has(`${name}.${k}`)).sort();
      if (removed.length) {
        throw new FuxError(
          `${label}: [${name}] \`${removed[0]}\` ${REMOVED_KEYS.get(`${name}.${removed[0]}`)}`,
        );
      }
      const renamed = unknownKeys.filter((k) => LEGACY_FIELD_KEYS.has(k)).sort();
      if (name === "bm25f" && renamed.length) {
        const pairs = renamed.map((k) => `\`${k}\` -> \`${LEGACY_FIELD_KEYS.get(k)}\``).join(", ");
        throw new FuxError(
          `${label}: [bm25f] field weights lost the \`_weight\` suffix in ` +
          `v2.0.0-alpha.2 -- rename ${pairs}. Inside a table already named ` +
          "`bm25f` the suffix was noise, and `k1`/`b` never carried one. " +
          "`[ranking]` is unchanged and keeps its suffixes.",
        );
      }
      throw new FuxError(
        `${label}: [${name}] has unknown key(s) ${JSON.stringify(unknownKeys.sort())} — ` +
        `known: ${JSON.stringify(SCHEMA[name])}`,
      );
    }
  }

  const c = new Collector(label);

  const bm25f = data.bm25f ?? {};
  const k1 = has(bm25f, "k1") ? positive(c, "bm25f", "k1", bm25f.k1, K1) : K1;
  const b = has(bm25f, "b") ? fraction(c, "bm25f", "b", bm25f.b, B) : B;
  const weights = [...FIELD_WEIGHTS];
  FIELD_KEYS.forEach((key, i) => {
    // Zero is legal and means *ignore this field* — a ranking choice, not the
    // source exclusion `.fux/sources/` owns.
    if (has(bm25f, key)) weights[i] = nonNegative(c, "bm25f", key, bm25f[key], FIELD_WEIGHTS[i]);
  });

  const anchorWeight = has(bm25f, "anchor")
    ? nonNegative(c, "bm25f", "anchor", bm25f.anchor, ANCHOR)
    : ANCHOR;

  const ranking = data.ranking ?? {};
  const pick = (table, name, key, dflt, fn = nonNegative) =>
    (has(table, key) ? fn(c, name, key, table[key], dflt) : dflt);

  const rerankWeight = pick(ranking, "ranking", "rerank_weight", 0.0);
  const expandWeight = pick(ranking, "ranking", "expand_weight", 0.2);
  const rm3Weight = pick(ranking, "ranking", "rm3_weight", 0.0);

  const graph = data.graph ?? {};
  const damping = pick(graph, "graph", "damping", 0.85, fraction);
  const laziness = pick(graph, "graph", "laziness", 0.5, fraction);
  const hopDecay = pick(graph, "graph", "hop_decay", 0.5, fraction);
  const iterations = has(graph, "iterations")
    ? atLeast(c, graph, "graph", "iterations", graph.iterations, 3, 1) : 3;
  const expandLimit = has(graph, "expand_limit")
    ? atLeast(c, graph, "graph", "expand_limit", graph.expand_limit, 10, 1) : 10;
  const seedDepth = has(graph, "seed_depth")
    ? atLeast(c, graph, "graph", "seed_depth", graph.seed_depth, 5, 1) : 5;
  const askBoost = has(graph, "ask_boost")
    ? boolean(c, "graph", "ask_boost", graph.ask_boost, true) : true;
  const askRelated = has(graph, "ask_related")
    ? boolean(c, "graph", "ask_related", graph.ask_related, true) : true;
  const askKinds = has(graph, "ask_kinds")
    ? edgeKinds(c, "graph", "ask_kinds", graph.ask_kinds, "ref") : "ref";
  const askLinkIdf = has(graph, "ask_link_idf")
    ? boolean(c, "graph", "ask_link_idf", graph.ask_link_idf, true) : true;
  const askMaxHops = has(graph, "ask_max_hops")
    ? atLeast(c, graph, "graph", "ask_max_hops", graph.ask_max_hops, 1, 1) : 1;
  const askRelatedLimit = has(graph, "ask_related_limit")
    ? atLeast(c, graph, "graph", "ask_related_limit", graph.ask_related_limit, 5, 1) : 5;

  const conf = data.confidence ?? {};
  const separationFloor = pick(conf, "confidence", "separation_floor", SEPARATION_FLOOR, fraction);
  const docCoverageFloor = pick(conf, "confidence", "doc_coverage_floor", DOC_COVERAGE_FLOOR, fraction);

  checkIndexValues(c, data[INDEX_TABLE]);

  const refer = data.refer ?? {};
  const budget = has(refer, "budget") ? atLeast(c, refer, "refer", "budget", refer.budget, 8000, 1) : 8000;
  const perDocFraction = pick(refer, "refer", "per_doc_fraction", 0.5, fraction);
  let minPassage = has(refer, "min_passage_bytes")
    ? atLeast(c, refer, "refer", "min_passage_bytes", refer.min_passage_bytes, 120, 1) : 120;
  let maxPassage = has(refer, "max_passage_bytes")
    ? atLeast(c, refer, "refer", "max_passage_bytes", refer.max_passage_bytes, 4000, 1) : 4000;
  if (minPassage >= maxPassage) {
    c.add(
      `[refer] min_passage_bytes (${minPassage}) must be smaller than ` +
      `max_passage_bytes (${maxPassage}) — the first is the floor below which a ` +
      "passage is not worth citing, the second the ceiling above which it is cut",
    );
    minPassage = 120;
    maxPassage = 4000;
  }

  const priority = [];
  for (const [entry, value] of Object.entries(data.priority ?? {})) {
    if (typeof value !== "number") {
      c.add(`[priority] "${entry}" must be a number (got ${repr(value)})`);
      continue;
    }
    if (value < 0) {
      c.add(
        `[priority] "${entry}" must not be negative — a negative multiplier ` +
        `inverts the ordering, which is broken rather than aggressive (got ${value})`,
      );
      continue;
    }
    if (value === 0) {
      c.add(
        `[priority] "${entry}" is zero, which means EXCLUDE — and exclusion ` +
        'already has one home: prefix the entry with `!` in .fux/sources/. ' +
        "Two ways to do one thing is how they drift apart",
      );
      continue;
    }
    priority.push([entry, value]);
  }
  // Longest first, so `priorityFor` can return on the first match. The tie case
  // cannot occur: TOML keys are unique. `id`-style code-point ordering, because
  // Python sorts by the string and JS `<` is UTF-16 (W-107 hazard H1).
  priority.sort((a, b2) => (a[0].length !== b2[0].length ? b2[0].length - a[0].length : cmpCodePoints(a[0], b2[0])));

  c.raiseIfAny();

  return new Tune({
    k1, b, fieldWeights: weights, anchorWeight,
    rerankWeight, expandWeight, rm3Weight,
    damping, iterations, laziness, hopDecay, expandLimit, seedDepth,
    askBoost, askRelated, askKinds, askLinkIdf, askMaxHops, askRelatedLimit,
    separationFloor, docCoverageFloor,
    budget, perDocFraction, minPassageBytes: minPassage, maxPassageBytes: maxPassage,
    priority,
  });
}
