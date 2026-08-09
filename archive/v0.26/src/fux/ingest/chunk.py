"""Structure-aware, heading-based chunker.

Targets 256–512 tokens per chunk (token ≈ whitespace word for v1 — recorded in
ADR 0002); small sibling sections merge, oversize paragraphs split with ~12 %
word overlap, code fences and tables are atomic. Every chunk keeps its heading
path and its 1-based line span in the *body* it was cut from — the caller maps
body lines to source lines via the converter's line offset.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

_HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")

TARGET_MIN = 256
TARGET_MAX = 512
OVERLAP_RATIO = 0.12


@dataclass(frozen=True)
class Chunk:
    heading_path: str  # "Guide > Install", "" when no headings above
    text: str
    start_line: int  # 1-based, body coordinates
    end_line: int
    words: int


@dataclass(frozen=True)
class _Block:
    kind: str  # heading | fence | table | para
    lines: tuple[str, ...]
    start: int
    end: int
    level: int = 0  # heading only

    @property
    def words(self) -> int:
        return sum(len(ln.split()) for ln in self.lines)


def chunk_markdown(
    body: str,
    target_min: int = TARGET_MIN,
    target_max: int = TARGET_MAX,
    overlap_ratio: float = OVERLAP_RATIO,
) -> list[Chunk]:
    blocks = _parse_blocks(body)
    chunks: list[Chunk] = []
    stack: list[tuple[int, str]] = []  # (level, heading text)
    cur: list[_Block] = []
    cur_words = 0
    cur_path = ""

    def path() -> str:
        return " > ".join(text for _, text in stack)

    def flush() -> None:
        nonlocal cur, cur_words
        if cur:
            text = "\n".join("\n".join(b.lines) for b in cur)
            chunks.append(Chunk(cur_path, text, cur[0].start, cur[-1].end, cur_words))
        cur, cur_words = [], 0

    def append(block: _Block) -> None:
        nonlocal cur_path, cur_words
        if not cur:
            cur_path = path()
        cur.append(block)
        cur_words += block.words

    for block in blocks:
        if block.kind == "heading":
            if cur_words >= target_min:
                flush()
            match = _HEADING_RE.match(block.lines[0].strip())
            level, text = len(match.group(1)), match.group(2).strip()
            while stack and stack[-1][0] >= level:
                stack.pop()
            stack.append((level, text))
            if not cur:  # heading opens the next chunk; path includes itself
                cur_path = path()
                cur.append(block)
                cur_words += block.words
            else:
                append(block)
            continue
        if block.kind == "para" and block.words > target_max:
            flush()
            chunks.extend(_split_paragraph(block, path(), target_max, overlap_ratio))
            continue
        if cur_words and cur_words + block.words > target_max:
            flush()
        append(block)
    flush()
    return chunks


def _split_paragraph(
    block: _Block, heading_path: str, target_max: int, overlap_ratio: float
) -> list[Chunk]:
    words = " ".join(block.lines).split()
    overlap = int(target_max * overlap_ratio)
    step = target_max - overlap
    out = []
    for start in range(0, len(words), step):
        piece = words[start : start + target_max]
        out.append(
            Chunk(heading_path, " ".join(piece), block.start, block.end, len(piece))
        )
        if start + target_max >= len(words):
            break
    return out


def _parse_blocks(body: str) -> list[_Block]:
    lines = body.split("\n")
    blocks: list[_Block] = []
    i, n = 0, len(lines)
    while i < n:
        stripped = lines[i].strip()
        if not stripped:
            i += 1
            continue
        if _HEADING_RE.match(stripped):
            blocks.append(_Block("heading", (lines[i],), i + 1, i + 1))
            i += 1
        elif stripped.startswith(("```", "~~~")):
            fence = stripped[:3]
            j = i + 1
            while j < n and not lines[j].strip().startswith(fence):
                j += 1
            end = j if j < n else n - 1
            blocks.append(_Block("fence", tuple(lines[i : end + 1]), i + 1, end + 1))
            i = end + 1
        elif stripped.startswith("|"):
            j = i
            while j < n and lines[j].strip().startswith("|"):
                j += 1
            blocks.append(_Block("table", tuple(lines[i:j]), i + 1, j))
            i = j
        else:
            j = i
            while j < n:
                s = lines[j].strip()
                if not s or _HEADING_RE.match(s) or s.startswith(("```", "~~~", "|")):
                    break
                j += 1
            blocks.append(_Block("para", tuple(lines[i:j]), i + 1, j))
            i = j
    return blocks
