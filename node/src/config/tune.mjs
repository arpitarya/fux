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
 * - **No defaults.** Every key is required (L12, SR-LAW-12 decision 3): an
 *   absent file, table or key stops the command naming it, in the same words
 *   `tune.py` uses. `--no-tune` reads the packaged template — inlined into the
 *   bundle — never a value in code (L12 decision 7).
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
 * **Absent, malformed or missing a key = a hard error.** Degrading would answer
 * with a ranking the reader did not configure while they believed it was
 * theirs (SR-TUNE decision 10; L12 decision 3).
 */
import { readFileSync, statSync } from "node:fs";
import { join } from "node:path";
import { FuxError } from "../errors.mjs";
import { BOM, parseToml, wasFloat } from "./toml.mjs";
import { Scoring } from "../query/bm25f.mjs";
import { Proximity } from "../query/rerank.mjs";
import { TF_FIELDS } from "../store/format.mjs";
import { cmpCodePoints } from "../compat/pyfloat.mjs";
// `ask_kinds` is validated against the kinds the index mints, at load — the
// same list `graph --kinds` refuses against at the CLI boundary.
import { EDGE_KINDS } from "../graph/walk.mjs";
import { fixed } from "./constants.mjs";
import { intentTypes } from "../query/intent.mjs";

export const TUNE_NAME = fixed("files", "tune");

//: At most this many semantic errors are reported together.
const MAX_REPORTED = 10;

//: The `[bm25f]` field-weight keys ARE the field names (Arpit, 2026-08-27):
//: inside a table already named `bm25f` a `_weight` suffix is noise.
const FIELD_KEYS = TF_FIELDS;

//: Old spelling -> new, for the migration message only.
const LEGACY_FIELD_KEYS = new Map(TF_FIELDS.map((name) => [`${name}_weight`, name]));

export const INDEX_TABLE = "index";

//: The template `fux setup` writes (`src/fux/templates/tune.toml.txt`). In a
//: checkout it is read from the Python tree; in the bundle it is INLINED
//: (`@fux-inline`), so `--no-tune` never reads a path the consumer lacks.
const TEMPLATE_TEXT = /* @fux-inline src/fux/templates/tune.toml.txt */ readFileSync(
  new URL("../../../src/fux/templates/tune.toml.txt", import.meta.url),
  "utf8",
);
const TEMPLATE_LABEL = "the packaged tune.toml template (--no-tune)";

//: What a missing key's error tells the reader to do — `tune.py`'s sentence.
const FIX_HINT = "`fux doctor --fix` writes every missing key from the template `fux setup` uses";

//: The closed key set. Table -> keys. Adding one here is a change to SR-TUNE.
const SCHEMA = {
  bm25f: ["k1", "b", ...FIELD_KEYS, "anchor"],
  ranking: [
    "rerank_weight", "rerank_depth", "rerank_coverage_power", "rerank_base", "rerank_span",
    "rerank_adjacency", "expand_weight", "mined_weight", "intent_weight",
    "section_weight",
  ],
  // The six `ask_*` keys are W-161's graph tier. They are parsed and carried
  // here so a consumer's committed `tune.toml` is accepted identically by both
  // readers; whether the Node reader COMPOSES the tier is
  // SR-NODE-SEARCH's, and today it does not — see the divergence note there.
  // A key this reader refused and Python accepted would make the same file
  // valid in one reader and an error in the other, which is the one asymmetry
  // the config parity test exists to forbid.
  graph: [
    "damping", "iterations", "laziness", "hop_decay", "expand_limit", "seed_depth",
    "path_limit", "ask_boost", "ask_related", "ask_kinds", "ask_link_idf", "ask_max_hops",
    "ask_related_limit",
  ],
  refer: [
    "budget", "per_doc_fraction", "min_passage_bytes", "max_passage_bytes",
    "citation_overhead", "table_rows_per_passage",
  ],
  confidence: ["separation_floor", "doc_coverage_floor"],
  enrich: ["self_retrieval_k"],
  // ⚠ THE EXCEPTION — read by ingest, changes committed bytes, untouched by
  // `--no-tune`. Node validates it and carries none of it.
  [INDEX_TABLE]: ["max_phrases", "max_table_rows"],
  // `[priority]` is the one open table: its keys are the consumer's own
  // source entries, which fux cannot know in advance.
  priority: [],
  // W-168 step 9 (D2): glob -> document type, the consumer's own patterns.
  doctype: [],
};

const OPEN_TABLES = new Set(["priority", "doctype"]);

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
  ["ranking.rm3_weight",
    "was REMOVED on 2026-09-27 (W-224). RM3 -- ten feedback terms borrowed " +
    "from fux's own top ten -- FAILED its pre-registered run twice, on drift: " +
    "every weight lost 6 to 13 questions that were right at rank 1 " +
    "(work/regression/2026-09-23-rm3/VERDICT.md, " +
    "work/regression/2026-09-25-rm3-boosted/VERDICT.md). Delete the key; " +
    "ranking is unchanged, because it shipped at 0.0 (off). Removed a second " +
    "time on 2026-10-03 (W-237): RM3 gated on a `grounded` first pass FAILED " +
    "too, with no gain (work/regression/2026-09-30-rm3-grounded/VERDICT.md). " +
    "Supplying the words yourself is untouched: `--expand`, weighted by " +
    "`expand_weight`."],
]);

/** Every tunable, resolved. Build it with `loadTune` — there are no defaults (L12). */
export class Tune {
  constructor(values) {
    for (const name of TUNE_FIELDS) {
      if (!Object.hasOwn(values, name)) throw new FuxError(`Tune: ${name} was not supplied`);
    }
    Object.assign(this, values);
    Object.freeze(this);
  }

  /** The three-part BM25F parameter set, as one object. */
  get scoring() {
    return new Scoring(this.k1, this.b, this.fieldWeights, this.anchorWeight, this.sectionWeight);
  }

  /** The reranker's passage arithmetic — coverage power and the mix. */
  get proximity() {
    return new Proximity(this.rerankCoveragePower, this.rerankBase, this.rerankSpan, this.rerankAdjacency);
  }

  /** `[refer]`'s three passage bounds, as `refer/chunk.mjs`'s `chunk` takes them. */
  chunkBounds() {
    return {
      minPassageBytes: this.minPassageBytes,
      maxPassageBytes: this.maxPassageBytes,
      tableRowsPerPassage: this.tableRowsPerPassage,
    };
  }
}

//: Every field a `Tune` carries — `tune.py`'s dataclass fields, camel-cased.
const TUNE_FIELDS = [
  "k1", "b", "fieldWeights", "anchorWeight",
  "rerankWeight", "rerankDepth", "rerankCoveragePower", "rerankBase", "rerankSpan",
  "rerankAdjacency", "expandWeight", "minedWeight", "intentWeight", "sectionWeight",
  "damping", "iterations", "laziness", "hopDecay", "expandLimit", "seedDepth", "pathLimit",
  "askBoost", "askRelated", "askKinds", "askLinkIdf", "askMaxHops", "askRelatedLimit",
  "separationFloor", "docCoverageFloor",
  "budget", "perDocFraction", "minPassageBytes", "maxPassageBytes", "citationOverhead",
  "tableRowsPerPassage",
  "selfRetrievalK",
  "priority",
  "doctype",
];

/** Gathers semantic errors so a hand-edited file reports them together. */
class Collector {
  constructor(label) { this.label = label; this.errors = []; this.missing = false; }
  add(message) { this.errors.push(message); }
  /** L12 decision 3 — a missing key is an error that names it. */
  absent(table, key) { this.missing = true; this.errors.push(`[${table}] ${key} is missing`); }
  raiseIfAny() {
    if (!this.errors.length) return;
    const shown = this.errors.slice(0, MAX_REPORTED);
    const more = this.errors.length - shown.length;
    let tail = more > 0 ? `\n  ... and ${more} more` : "";
    if (this.missing) tail += `\n  ${FIX_HINT}`;
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

function number(c, table, key, value) {
  if (typeof value !== "number") {
    c.add(`[${table}] ${key} must be a number (got ${repr(value)})`);
  }
  return value;
}

function positive(c, table, key, value) {
  const v = number(c, table, key, value);
  if (typeof v === "number" && v <= 0) {
    c.add(`[${table}] ${key} must be greater than zero — at zero the term it scales vanishes (got ${v})`);
  }
  return v;
}

function nonNegative(c, table, key, value) {
  const v = number(c, table, key, value);
  if (typeof v === "number" && v < 0) {
    c.add(
      `[${table}] ${key} must not be negative — a negative multiplier inverts ` +
      `the ordering, which is broken rather than aggressive (got ${v})`,
    );
  }
  return v;
}

function fraction(c, table, key, value) {
  const v = number(c, table, key, value);
  if (typeof v === "number" && !(v >= 0.0 && v <= 1.0)) {
    c.add(
      `[${table}] ${key} must be between 0 and 1 — 0 turns the effect off ` +
      `entirely, 1 applies it in full (got ${v})`,
    );
  }
  return v;
}

/** A TOML **integer**, at least one. `3.0` is not an integer here, because it
 *  is not one in `tune.py` either — see `config/toml.mjs`'s `wasFloat`. */
function whole(c, table, key, value, tbl) {
  if (typeof value !== "number" || !Number.isInteger(value) || wasFloat(tbl, key)) {
    c.add(`[${table}] ${key} must be a whole number (got ${repr(value)})`);
    return value;
  }
  if (value < 1) c.add(`[${table}] ${key} must be at least 1 (got ${value})`);
  return value;
}

/**
 * A strict boolean. `1`/`0` are refused rather than coerced — the twin of
 * Python's `_boolean`, and for its reason: a consumer who writes
 * `ask_boost = 1` is told the key is a boolean instead of getting a silent
 * `true` out of a file that never said so.
 */
function boolean(c, table, key, value) {
  if (typeof value !== "boolean") c.add(`[${table}] ${key} must be true or false (got ${repr(value)})`);
  return value;
}

/**
 * A comma-separated list of edge kinds the index actually mints.
 *
 * Validated at LOAD rather than where a walk would run: an unknown kind walks
 * nothing, and a walk over no edges returns an empty neighbourhood that cannot
 * be told from a corpus with no links at all.
 */
function edgeKinds(c, table, key, value) {
  if (typeof value !== "string") {
    c.add(`[${table}] ${key} must be a string (got ${repr(value)})`);
    return value;
  }
  const named = value.split(",").map((k) => k.trim()).filter((k) => k.length > 0);
  if (named.length === 0) {
    c.add(`[${table}] ${key} names no edge kind; the kinds this index mints are ${EDGE_KINDS.join(", ")}`);
    return value;
  }
  const unknown = [...new Set(named.filter((k) => !EDGE_KINDS.includes(k)))].sort();
  if (unknown.length > 0) {
    c.add(
      `[${table}] ${key} names ${unknown.join(", ")}, which is not an edge kind; ` +
      `the kinds this index mints are ${EDGE_KINDS.join(", ")}`,
    );
    return value;
  }
  return named.join(",");
}

function has(table, key) {
  return table !== null && typeof table === "object" && Object.prototype.hasOwnProperty.call(table, key);
}

/** `[table] key`, validated by `check` — or recorded as missing. */
function read(c, data, table, key, check) {
  const t = data[table];
  if (!has(data, table) || t === null || typeof t !== "object" || !has(t, key)) {
    c.absent(table, key);
    return undefined;
  }
  return check(c, table, key, t[key], t);
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

/** Read `.fux/tune.toml` — every key required.
 *
 * `enabled=false` is `--no-tune`: the consumer's file is not read at all and
 * the packaged template is read in its place (SR-TUNE decision 11; L12
 * decision 7). */
export function loadTune(root, { enabled }) {
  if (enabled !== true && enabled !== false) throw new FuxError("loadTune: `enabled` is required");
  if (!enabled) return resolve(parseToml(TEMPLATE_TEXT, TEMPLATE_LABEL), TEMPLATE_LABEL);

  const path = join(root, TUNE_NAME);
  const label = `${root}/${TUNE_NAME}`;
  let raw;
  try {
    if (!statSync(path).isFile()) throw new Error("not a file");
    raw = readFileSync(path, "utf8");
  } catch {
    throw new FuxError(
      `${label} is missing - \`fux setup\` writes it, and \`fux doctor --fix\` ` +
      "restores a deleted one. fux holds no copy of its values in code",
    );
  }
  if (raw.startsWith(BOM)) raw = raw.slice(BOM.length);
  rejectConflictMarkers(label, raw);
  return resolve(parseToml(raw, label), label);
}

/** Validate a parsed tune file and build the `Tune` — or throw, naming every fault. */
function resolve(data, label) {
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
      // one table report the same one every run (L4 reaches errors too).
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
  const r = (table, key, check) => read(c, data, table, key, check);

  const values = {
    k1: r("bm25f", "k1", positive),
    b: r("bm25f", "b", fraction),
    // Zero is legal for a field weight and means *ignore this field* — a
    // ranking choice, not the source exclusion `.fux/sources/` owns.
    fieldWeights: FIELD_KEYS.map((key) => r("bm25f", key, nonNegative)),
    anchorWeight: r("bm25f", "anchor", nonNegative),
    rerankWeight: r("ranking", "rerank_weight", nonNegative),
    rerankDepth: r("ranking", "rerank_depth", whole),
    rerankCoveragePower: r("ranking", "rerank_coverage_power", positive),
    rerankBase: r("ranking", "rerank_base", fraction),
    rerankSpan: r("ranking", "rerank_span", fraction),
    rerankAdjacency: r("ranking", "rerank_adjacency", fraction),
    expandWeight: r("ranking", "expand_weight", nonNegative),
    minedWeight: r("ranking", "mined_weight", nonNegative),
    intentWeight: r("ranking", "intent_weight", nonNegative),
    // W-236 — B2's λ (SR-SECTIONS decision 5). `0.0` never opens the plane.
    sectionWeight: r("ranking", "section_weight", nonNegative),
    damping: r("graph", "damping", fraction),
    iterations: r("graph", "iterations", whole),
    laziness: r("graph", "laziness", fraction),
    hopDecay: r("graph", "hop_decay", fraction),
    expandLimit: r("graph", "expand_limit", whole),
    seedDepth: r("graph", "seed_depth", whole),
    pathLimit: r("graph", "path_limit", whole),
    askBoost: r("graph", "ask_boost", boolean),
    askRelated: r("graph", "ask_related", boolean),
    askKinds: r("graph", "ask_kinds", edgeKinds),
    askLinkIdf: r("graph", "ask_link_idf", boolean),
    askMaxHops: r("graph", "ask_max_hops", whole),
    askRelatedLimit: r("graph", "ask_related_limit", whole),
    separationFloor: r("confidence", "separation_floor", fraction),
    docCoverageFloor: r("confidence", "doc_coverage_floor", fraction),
    budget: r("refer", "budget", whole),
    perDocFraction: r("refer", "per_doc_fraction", fraction),
    minPassageBytes: r("refer", "min_passage_bytes", whole),
    maxPassageBytes: r("refer", "max_passage_bytes", whole),
    citationOverhead: r("refer", "citation_overhead", whole),
    tableRowsPerPassage: r("refer", "table_rows_per_passage", whole),
    selfRetrievalK: r("enrich", "self_retrieval_k", whole),
  };
  const low = values.minPassageBytes, high = values.maxPassageBytes;
  if (Number.isInteger(low) && Number.isInteger(high) && low >= high) {
    c.add(
      `[refer] min_passage_bytes (${low}) must be smaller than ` +
      `max_passage_bytes (${high}) — the first is the floor below which a ` +
      "passage is not worth citing, the second the ceiling above which it is cut",
    );
  }

  // `[index]` is validated and discarded, exactly as Python does: those keys
  // change committed bytes at ingest, Node does not ingest, and `--no-tune`
  // does not reach them.
  r(INDEX_TABLE, "max_phrases", whole);
  r(INDEX_TABLE, "max_table_rows", whole);

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

  // W-168 step 9 — `[doctype]`, validated as `tune.py` does and sorted the same
  // way: longest first by CODE POINTS (Python's `len`), ties by code point.
  const types = intentTypes();
  const doctype = [];
  for (const [pattern, kind] of Object.entries(data.doctype ?? {})) {
    if (typeof kind !== "string" || !types.has(kind)) {
      c.add(
        `[doctype] "${pattern}" must be one of ${repr([...types].sort(cmpCodePoints))} ` +
        `(got ${repr(kind)}) — the types an intent cue can prefer ` +
        "(src/fux/constants.toml [intent.type])",
      );
      continue;
    }
    doctype.push([pattern, kind]);
  }
  const cp = (x) => Array.from(x).length;
  doctype.sort((a, b2) => (cp(a[0]) !== cp(b2[0]) ? cp(b2[0]) - cp(a[0]) : cmpCodePoints(a[0], b2[0])));

  c.raiseIfAny();
  return new Tune({ ...values, priority, doctype });
}
