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
 * Transcribed from RFC 7693 §3.1–§3.3. Pinned in `test/blake2b.test.mjs`
 * against RFC 7693 Appendix A and against Python `hashlib` at digest sizes
 * 1, 8 and 20 — the three fux uses (shard bucket, term key, content sha).
 */

// IV — RFC 7693 §2.6, the SHA-512 IV. lo, hi per word.
const IV32 = new Uint32Array([
  0xf3bcc908, 0x6a09e667, 0x84caa73b, 0xbb67ae85,
  0xfe94f82b, 0x3c6ef372, 0x5f1d36f1, 0xa54ff53a,
  0xade682d1, 0x510e527f, 0x2b3e6c1f, 0x9b05688c,
  0xfb41bd6b, 0x1f83d9ab, 0x137e2179, 0x5be0cd19,
]);

// SIGMA — RFC 7693 §2.7, ten permutations, rounds 11/12 reuse 0/1.
// Pre-doubled: these index the 32-bit halves directly.
const SIGMA82 = new Uint8Array([
  0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15,
  14, 10, 4, 8, 9, 15, 13, 6, 1, 12, 0, 2, 11, 7, 5, 3,
  11, 8, 12, 0, 5, 2, 15, 13, 10, 14, 3, 6, 7, 1, 9, 4,
  7, 9, 3, 1, 13, 12, 11, 14, 2, 6, 5, 10, 4, 0, 15, 8,
  9, 0, 5, 7, 2, 4, 10, 15, 14, 1, 11, 12, 6, 8, 3, 13,
  2, 12, 6, 10, 0, 11, 8, 3, 4, 13, 7, 5, 15, 14, 1, 9,
  12, 5, 1, 15, 14, 13, 4, 10, 0, 7, 6, 3, 9, 2, 8, 11,
  13, 11, 7, 14, 12, 1, 3, 9, 5, 0, 15, 4, 8, 6, 2, 10,
  6, 15, 14, 9, 11, 3, 0, 8, 12, 2, 13, 7, 1, 4, 10, 5,
  10, 2, 8, 4, 7, 6, 1, 5, 15, 11, 9, 14, 3, 12, 13, 0,
  0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15,
  14, 10, 4, 8, 9, 15, 13, 6, 1, 12, 0, 2, 11, 7, 5, 3,
].map((x) => x * 2));

const v = new Uint32Array(32);
const m = new Uint32Array(32);

/** v[a] += v[b], 64-bit, carrying lo into hi. */
function add64AA(dst, a, b) {
  const o0 = dst[a] + dst[b];
  let o1 = dst[a + 1] + dst[b + 1];
  if (o0 >= 0x100000000) o1++;
  dst[a] = o0;
  dst[a + 1] = o1;
}

/** v[a] += (b1 << 32) | b0. `b0 < 0` is a sign-extended 32-bit value. */
function add64AC(dst, a, b0, b1) {
  let o0 = dst[a] + b0;
  if (b0 < 0) o0 += 0x100000000;
  let o1 = dst[a + 1] + b1;
  if (o0 >= 0x100000000) o1++;
  dst[a] = o0;
  dst[a + 1] = o1;
}

function get32(arr, i) {
  return (arr[i] ^ (arr[i + 1] << 8) ^ (arr[i + 2] << 16) ^ (arr[i + 3] << 24));
}

/** The G mixing function — RFC 7693 §3.1. Rotations 32, 24, 16, 63. */
function g(a, b, c, d, ix, iy) {
  const x0 = m[ix], x1 = m[ix + 1];
  const y0 = m[iy], y1 = m[iy + 1];

  add64AA(v, a, b);
  add64AC(v, a, x0, x1);

  // rotr 32 — a whole-word swap, so it is free
  let xor0 = v[d] ^ v[a];
  let xor1 = v[d + 1] ^ v[a + 1];
  v[d] = xor1;
  v[d + 1] = xor0;

  add64AA(v, c, d);

  // rotr 24
  xor0 = v[b] ^ v[c];
  xor1 = v[b + 1] ^ v[c + 1];
  v[b] = (xor0 >>> 24) ^ (xor1 << 8);
  v[b + 1] = (xor1 >>> 24) ^ (xor0 << 8);

  add64AA(v, a, b);
  add64AC(v, a, y0, y1);

  // rotr 16
  xor0 = v[d] ^ v[a];
  xor1 = v[d + 1] ^ v[a + 1];
  v[d] = (xor0 >>> 16) ^ (xor1 << 16);
  v[d + 1] = (xor1 >>> 16) ^ (xor0 << 16);

  add64AA(v, c, d);

  // rotr 63
  xor0 = v[b] ^ v[c];
  xor1 = v[b + 1] ^ v[c + 1];
  v[b] = (xor1 >>> 31) ^ (xor0 << 1);
  v[b + 1] = (xor0 >>> 31) ^ (xor1 << 1);
}

/** The compression function F — RFC 7693 §3.2. */
function compress(ctx, last) {
  let i = 0;
  for (i = 0; i < 16; i++) {
    v[i] = ctx.h[i];
    v[i + 16] = IV32[i];
  }

  // v[12,13] ^= t (the byte counter); v[14,15] ^= 0xff.. on the final block
  v[24] = v[24] ^ ctx.t;
  v[25] = v[25] ^ (ctx.t / 0x100000000);
  if (last) {
    v[28] = ~v[28];
    v[29] = ~v[29];
  }

  for (i = 0; i < 32; i++) m[i] = get32(ctx.b, 4 * i);

  for (i = 0; i < 12; i++) {
    const s = SIGMA82.subarray(i * 16, i * 16 + 16);
    g(0, 8, 16, 24, s[0], s[1]);
    g(2, 10, 18, 26, s[2], s[3]);
    g(4, 12, 20, 28, s[4], s[5]);
    g(6, 14, 22, 30, s[6], s[7]);
    g(0, 10, 20, 30, s[8], s[9]);
    g(2, 12, 22, 24, s[10], s[11]);
    g(4, 14, 16, 26, s[12], s[13]);
    g(6, 8, 18, 28, s[14], s[15]);
  }

  for (i = 0; i < 16; i++) ctx.h[i] = ctx.h[i] ^ v[i] ^ v[i + 16];
}

/** Init — RFC 7693 §3.3. The parameter block is why truncation is wrong. */
function init(outlen, key) {
  if (!Number.isInteger(outlen) || outlen < 1 || outlen > 64) {
    throw new RangeError(`blake2b digest size must be 1..64, got ${outlen}`);
  }
  const keylen = key ? key.length : 0;
  if (keylen > 64) throw new RangeError("blake2b key must be <= 64 bytes");

  const ctx = {
    b: new Uint8Array(128),
    h: new Uint32Array(16),
    t: 0,   // bytes compressed
    c: 0,   // bytes in the buffer
    outlen,
  };
  for (let i = 0; i < 16; i++) ctx.h[i] = IV32[i];
  // h[0] ^= 0x01010000 ^ (keylen << 8) ^ outlen
  ctx.h[0] ^= 0x01010000 ^ (keylen << 8) ^ outlen;

  if (keylen > 0) {
    update(ctx, key);
    ctx.c = 128;
  }
  return ctx;
}

function update(ctx, input) {
  for (let i = 0; i < input.length; i++) {
    if (ctx.c === 128) {
      ctx.t += ctx.c;
      compress(ctx, false);
      ctx.c = 0;
    }
    ctx.b[ctx.c++] = input[i];
  }
  return ctx;
}

function final(ctx) {
  ctx.t += ctx.c;
  while (ctx.c < 128) ctx.b[ctx.c++] = 0;
  compress(ctx, true);

  const out = new Uint8Array(ctx.outlen);
  for (let i = 0; i < ctx.outlen; i++) {
    out[i] = (ctx.h[i >> 2] >> (8 * (i & 3))) & 0xff;
  }
  return out;
}

const HEX = [];
for (let i = 0; i < 256; i++) HEX.push(i.toString(16).padStart(2, "0"));

/** `blake2b(bytes, digestSize)` -> Uint8Array. */
export function blake2b(input, digestSize = 64, key = null) {
  return final(update(init(digestSize, key), input));
}

/** `blake2b(bytes, digestSize)` -> lowercase hex, like Python's `.hexdigest()`. */
export function blake2bHex(input, digestSize = 64, key = null) {
  const out = blake2b(input, digestSize, key);
  let s = "";
  for (let i = 0; i < out.length; i++) s += HEX[out[i]];
  return s;
}
