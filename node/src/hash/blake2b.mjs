/** BLAKE2b (RFC 7693), stdlib-free, at arbitrary digest sizes.
 *
 * ⚠ **`node:crypto` cannot do this job.** It exposes `blake2b512` and nothing
 * else, and **truncating a 512-bit digest is a different function**: BLAKE2b's
 * parameter block folds the digest length into `h[0]`, so `blake2b(x, 8)` and
 * `blake2b(x, 64)[:8]` disagree on every input. Fux keys its postings on
 * `blake2b(term, digest_size=8)`, so a truncation here would produce an index
 * that reads as valid and matches nothing.
 *
 * **64-bit words as 32-bit halves, never BigInt** (W-107 §6.3). Each 64-bit
 * word is two `Uint32Array` slots — lo at `2i`, hi at `2i+1`. BigInt would be
 * correct and roughly an order of magnitude slower on the hot path, and the
 * hot path is every term of every query.
 *
 * **Every number the RFC fixes is read from `src/fux/constants.toml
 * [blake2b]`** (SR-LAW-12 decision 6a, R7) — the IV, the message schedule, the
 * G steps, the rotations, the block and parameter-block layout. What is left
 * here is the arithmetic: a carry, a rotation, a little-endian read.
 *
 * Transcribed from RFC 7693 §3.1–§3.3. Pinned in `test/pins.test.mjs` against
 * RFC 7693 Appendix A and against Python `hashlib` at digest sizes 1, 8 and 20
 * — the three fux uses (shard bucket, term key, content sha).
 */
import { Buffer } from "node:buffer";
import { fixed } from "../config/constants.mjs";

/** Bytes in one 32-bit half, and halves in one 64-bit word. */
const HALF_BYTES = Uint32Array.BYTES_PER_ELEMENT;
const HALVES = BigUint64Array.BYTES_PER_ELEMENT / HALF_BYTES;
const HALF_BITS = fixed("blake2b", "word_bits") / HALVES;

// IV — RFC 7693 §2.6, the SHA-512 IV, lo then hi per word.
const IV32 = Uint32Array.from(fixed("blake2b", "iv"));

// SIGMA — RFC 7693 §2.7, one row per round; indexes MESSAGE WORDS.
const SIGMA = fixed("blake2b", "sigma");

// The eight G applications of a round, (a, b, c, d) as indexes into the halves.
const G_STEPS = fixed("blake2b", "g_steps").map((step) => step.map((w) => w * HALVES));

const [R0, R1, R2, R3] = fixed("blake2b", "rotations");
const BLOCK_BYTES = fixed("blake2b", "block_bytes");
const MAX_DIGEST = fixed("blake2b", "max_digest_bytes");
const MAX_KEY = fixed("blake2b", "max_key_bytes");
const PARAM_BLOCK = fixed("blake2b", "param_block");
const KEY_SHIFT = fixed("blake2b", "key_length_shift");
const COUNTER = fixed("blake2b", "counter_word") * HALVES;
const FINAL = fixed("blake2b", "final_word") * HALVES;

// v = h ‖ IV (RFC 7693 §3.2); m is one block.
const v = new Uint32Array(IV32.length + IV32.length);
const m = new Uint32Array(BLOCK_BYTES / HALF_BYTES);

/** v[a] += (hi << 32) | lo, 64-bit: the lo half's overflow carries into hi. */
function add64(a, lo, hi) {
  const o = (v[a] + lo) >>> 0;
  v[a + 1] = v[a + 1] + hi + (o < v[a] ? 1 : 0);
  v[a] = o;
}

/** v[x] = rotr64(v[x] ^ v[y], n). A rotation by a whole half is a swap. */
function xorRotr(x, y, n) {
  const lo = v[x] ^ v[y];
  const hi = v[x + 1] ^ v[y + 1];
  const low = n < HALF_BITS;
  const p = low ? lo : hi;
  const q = low ? hi : lo;
  const k = low ? n : n - HALF_BITS;
  if (!k) {
    v[x] = p;
    v[x + 1] = q;
    return;
  }
  v[x] = (p >>> k) ^ (q << (HALF_BITS - k));
  v[x + 1] = (q >>> k) ^ (p << (HALF_BITS - k));
}

/** The G mixing function — RFC 7693 §3.1. `ix`, `iy` index message words. */
function g(a, b, c, d, ix, iy) {
  const x = ix * HALVES;
  const y = iy * HALVES;
  add64(a, v[b], v[b + 1]);
  add64(a, m[x], m[x + 1]);
  xorRotr(d, a, R0);
  add64(c, v[d], v[d + 1]);
  xorRotr(b, c, R1);
  add64(a, v[b], v[b + 1]);
  add64(a, m[y], m[y + 1]);
  xorRotr(d, a, R2);
  add64(c, v[d], v[d + 1]);
  xorRotr(b, c, R3);
}

/** The compression function F — RFC 7693 §3.2. */
function compress(ctx, last) {
  v.set(ctx.h);
  v.set(IV32, ctx.h.length);

  // v[12] ^= t (the byte counter); v[14] = ~v[14] on the final block
  v[COUNTER] ^= ctx.tLo;
  v[COUNTER + 1] ^= ctx.tHi;
  if (last) {
    v[FINAL] = ~v[FINAL];
    v[FINAL + 1] = ~v[FINAL + 1];
  }

  for (let i = 0; i < m.length; i++) m[i] = ctx.view.getUint32(i * HALF_BYTES, true);

  for (const row of SIGMA) {
    let s = 0;
    for (const [a, b, c, d] of G_STEPS) g(a, b, c, d, row[s++], row[s++]);
  }

  for (let i = 0; i < ctx.h.length; i++) ctx.h[i] = ctx.h[i] ^ v[i] ^ v[i + ctx.h.length];
}

/** t += n, carried across the two halves. */
function count(ctx, n) {
  const lo = (ctx.tLo + n) >>> 0;
  ctx.tHi += lo < ctx.tLo ? 1 : 0;
  ctx.tLo = lo;
}

/** Init — RFC 7693 §3.3. The parameter block is why truncation is wrong. */
function init(outlen, key) {
  if (!Number.isInteger(outlen) || outlen < 1 || outlen > MAX_DIGEST) {
    throw new RangeError(`blake2b digest size must be 1..${MAX_DIGEST}, got ${outlen}`);
  }
  const keylen = key ? key.length : 0;
  if (keylen > MAX_KEY) throw new RangeError(`blake2b key must be <= ${MAX_KEY} bytes`);

  const b = new Uint8Array(BLOCK_BYTES);
  const ctx = {
    b,
    view: new DataView(b.buffer),
    h: Uint32Array.from(IV32),
    tLo: 0, // bytes compressed, lo half
    tHi: 0, // bytes compressed, hi half
    c: 0, // bytes in the buffer
    outlen,
  };
  // h[0] ^= 0x0101kknn — fanout 1, depth 1, key length, digest length
  ctx.h[0] ^= PARAM_BLOCK ^ (keylen << KEY_SHIFT) ^ outlen;

  if (keylen > 0) {
    update(ctx, key);
    ctx.c = BLOCK_BYTES;
  }
  return ctx;
}

function update(ctx, input) {
  for (let i = 0; i < input.length; i++) {
    if (ctx.c === BLOCK_BYTES) {
      count(ctx, ctx.c);
      compress(ctx, false);
      ctx.c = 0;
    }
    ctx.b[ctx.c++] = input[i];
  }
  return ctx;
}

function final(ctx) {
  count(ctx, ctx.c);
  ctx.b.fill(0, ctx.c);
  ctx.c = BLOCK_BYTES;
  compress(ctx, true);

  // h, little-endian, cut to the digest size
  const out = new Uint8Array(ctx.h.length * HALF_BYTES);
  const view = new DataView(out.buffer);
  ctx.h.forEach((w, i) => view.setUint32(i * HALF_BYTES, w, true));
  return out.slice(0, ctx.outlen);
}

/** `blake2b(bytes, digestSize)` -> Uint8Array. */
export function blake2b(input, digestSize, key) {
  return final(update(init(digestSize, key), input));
}

/** `blake2b(bytes, digestSize)` -> lowercase hex, like Python's `.hexdigest()`. */
export function blake2bHex(input, digestSize, key) {
  return Buffer.from(blake2b(input, digestSize, key)).toString("hex");
}
