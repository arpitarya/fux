/** Python float semantics JS does not share. No Python twin — declared exempt.
 *
 * Two of them reach the sort key, so both are correctness, not cosmetics.
 */

/** Python's `round(x, ndigits)` — round-HALF-EVEN on the exact binary value.
 *
 * ⚠ `Number(x.toFixed(9))` agrees on ~200 000 random doubles and **fails on
 * exact binary ties**, where `toFixed` rounds half-UP and Python rounds
 * half-even. `round(score, 9)` is the sort key's own resolution
 * ([ADR-RANKING decision 8a](../../../docs/adr/0111_ranking.md)), so a tie
 * resolved the other way is a different ORDER — the one thing
 * PRE-REGISTRATION-NODE §2 calls non-negotiable.
 *
 * The tie is detected by asking for more digits than `toFixed(9)` kept: if
 * everything past the 9th digit is exactly `5` followed by zeros, the value
 * sits on the boundary and the winner is the even neighbour.
 */
export function pyRound9(x) {
  if (!Number.isFinite(x)) return x;
  const s = x.toFixed(20);                 // enough digits to see the tie exactly
  const dot = s.indexOf(".");
  const tail = s.slice(dot + 1 + 9);       // digits past the 9th decimal
  const naive = Number(x.toFixed(9));
  if (!/^50*$/.test(tail)) return naive;   // not a tie — toFixed is already right

  // Exact tie: choose the even neighbour.
  const keep = s.slice(0, dot + 1 + 9);
  const lower = Number(keep);
  const step = 1e-9;
  const lastDigit = Number(keep[keep.length - 1]);
  if (lastDigit % 2 === 0) return lower;
  return Number((lower + (x < 0 ? -step : step)).toFixed(9));
}

/** Python's `repr(float)` layout, which differs from `String(Number)`.
 *
 * Both are shortest-round-trip, so the DIGITS always agree; the exponent
 * thresholds and the integral form do not:
 *
 *     value      Python repr     JS String
 *     2.0        "2.0"           "2"
 *     1e-5       "1e-05"         "0.00001"
 *     1e16       "1e+16"         "10000000000000000"
 *
 * Python switches to exponent when `e < -4 or e >= 16`; JS at `-6 / 21`.
 */
export function pyRepr(x) {
  if (Number.isNaN(x)) return "nan";
  if (x === Infinity) return "inf";
  if (x === -Infinity) return "-inf";
  if (Number.isInteger(x) && Math.abs(x) < 1e16) {
    return Object.is(x, -0) ? "-0.0" : `${x}.0`;
  }
  const sign = x < 0 ? "-" : "";
  const a = Math.abs(x);
  const e = Math.floor(Math.log10(a));
  if (e < -4 || e >= 16) {
    // ⚠ Python does NOT pad the mantissa here: repr(1e-5) is "1e-05", not
    // "1.0e-05". The ".0" padding applies only to the integral form above.
    const [mant, exp] = a.toExponential().split("e");
    const n = Number(exp);
    const es = (n < 0 ? "-" : "+") + String(Math.abs(n)).padStart(2, "0");
    return `${sign}${mant}e${es}`;
  }
  return `${sign}${String(a)}`;
}

/** Compare two strings by CODE POINT, the way Python compares `str`.
 *
 * 🔴 **This is W-107 hazard H1, and it is why `<` is not used anywhere on a
 * doc id.** JS compares strings by UTF-16 code UNIT, so a surrogate pair
 * (anything above U+FFFF — an emoji, a rare CJK extension character) sorts
 * BELOW U+E000–U+FFFF in JS and ABOVE it in Python. The sort key ends in
 * `id`, so one such document orders differently in the two runtimes and the
 * byte-equal ordering assertion fails with nothing else wrong.
 *
 * Iterating a string with `for..of` yields code points, not units, which is
 * exactly the comparison Python makes.
 */
export function cmpCodePoints(a, b) {
  if (a === b) return 0;
  const ai = a[Symbol.iterator]();
  const bi = b[Symbol.iterator]();
  for (;;) {
    const x = ai.next();
    const y = bi.next();
    if (x.done && y.done) return 0;
    if (x.done) return -1;
    if (y.done) return 1;
    const cx = x.value.codePointAt(0);
    const cy = y.value.codePointAt(0);
    if (cx !== cy) return cx < cy ? -1 : 1;
  }
}
