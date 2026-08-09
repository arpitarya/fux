"""Hand-rolled RFC 6455 WebSocket client — stdlib `socket`/`hashlib`/`base64`.

Just enough of the protocol for CDP: client handshake with key validation,
masked client frames, text/binary/ping/pong/close, fragmentation reassembly,
16-bit and 64-bit extended payload lengths. Same ethos as the hand-rolled
frontmatter parser (CLAUDE.md): the dependency-free path is the product.
Reference: RFC 6455 §4 (handshake), §5 (framing).
"""

from __future__ import annotations

import base64
import hashlib
import os
import socket
import struct
from urllib.parse import urlsplit

from ..errors import FuxError

_GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"

OP_CONT, OP_TEXT, OP_BINARY, OP_CLOSE, OP_PING, OP_PONG = 0x0, 0x1, 0x2, 0x8, 0x9, 0xA


def accept_key_for(key: str) -> str:
    """Sec-WebSocket-Accept for a Sec-WebSocket-Key (RFC 6455 §4.2.2)."""
    digest = hashlib.sha1((key + _GUID).encode("ascii")).digest()
    return base64.b64encode(digest).decode("ascii")


def encode_frame(payload: bytes, opcode: int = OP_TEXT, *, mask: bool = True, fin: bool = True) -> bytes:
    """One client frame. Client frames MUST be masked (RFC 6455 §5.3)."""
    head = bytes([(0x80 if fin else 0) | opcode])
    length = len(payload)
    mask_bit = 0x80 if mask else 0
    if length < 126:
        head += bytes([mask_bit | length])
    elif length < 65536:
        head += bytes([mask_bit | 126]) + struct.pack(">H", length)
    else:
        head += bytes([mask_bit | 127]) + struct.pack(">Q", length)
    if not mask:
        return head + payload
    key = os.urandom(4)
    masked = bytes(b ^ key[i % 4] for i, b in enumerate(payload))
    return head + key + masked


class FrameReader:
    """Incremental frame decoder over a `recv_exact(n)` callable."""

    def __init__(self, recv_exact):
        self.recv_exact = recv_exact

    def read_frame(self) -> tuple[int, bool, bytes]:
        """Returns (opcode, fin, payload); unmasks if a mask is present."""
        b0, b1 = self.recv_exact(2)
        fin = bool(b0 & 0x80)
        opcode = b0 & 0x0F
        masked = bool(b1 & 0x80)
        length = b1 & 0x7F
        if length == 126:
            (length,) = struct.unpack(">H", self.recv_exact(2))
        elif length == 127:
            (length,) = struct.unpack(">Q", self.recv_exact(8))
        key = self.recv_exact(4) if masked else b""
        payload = self.recv_exact(length) if length else b""
        if masked:
            payload = bytes(b ^ key[i % 4] for i, b in enumerate(payload))
        return opcode, fin, payload

    def read_message(self, pong) -> tuple[int, bytes]:
        """Next complete message: reassembles fragments, answers pings inline."""
        opcode, fin, payload = self.read_frame()
        while opcode in (OP_PING, OP_PONG):
            if opcode == OP_PING:
                pong(payload)
            opcode, fin, payload = self.read_frame()
        message_op = opcode
        parts = [payload]
        while not fin:
            opcode, fin, payload = self.read_frame()
            if opcode == OP_PING:
                pong(payload)
                fin = False
                continue
            parts.append(payload)
        return message_op, b"".join(parts)


class WebSocket:
    """Blocking client socket speaking RFC 6455 — sized for CDP, not generality."""

    def __init__(self, url: str, timeout: float = 30.0):
        parts = urlsplit(url)
        if parts.scheme != "ws":
            raise FuxError(f"unsupported WebSocket scheme {parts.scheme!r} (CDP uses ws://)")
        self.host = parts.hostname or "127.0.0.1"
        self.port = parts.port or 80
        self.resource = parts.path + (f"?{parts.query}" if parts.query else "") or "/"
        self.sock = socket.create_connection((self.host, self.port), timeout=timeout)
        self.reader = FrameReader(self._recv_exact)
        self._handshake()

    def _handshake(self) -> None:
        key = base64.b64encode(os.urandom(16)).decode("ascii")
        request = (
            f"GET {self.resource} HTTP/1.1\r\n"
            f"Host: {self.host}:{self.port}\r\n"
            "Upgrade: websocket\r\n"
            "Connection: Upgrade\r\n"
            f"Sec-WebSocket-Key: {key}\r\n"
            "Sec-WebSocket-Version: 13\r\n"
            "\r\n"
        )
        self.sock.sendall(request.encode("ascii"))
        response = b""
        while b"\r\n\r\n" not in response:
            chunk = self.sock.recv(4096)
            if not chunk:
                raise FuxError("WebSocket handshake failed: connection closed")
            response += chunk
        head, _, rest = response.partition(b"\r\n\r\n")
        lines = head.decode("latin-1").split("\r\n")
        if "101" not in lines[0]:
            raise FuxError(f"WebSocket handshake rejected: {lines[0]}")
        headers = {
            k.strip().lower(): v.strip()
            for k, _, v in (line.partition(":") for line in lines[1:])
        }
        if headers.get("sec-websocket-accept") != accept_key_for(key):
            raise FuxError("WebSocket handshake failed: bad Sec-WebSocket-Accept")
        self._buffer = rest

    def _recv_exact(self, n: int) -> bytes:
        data = self._buffer[:n]
        self._buffer = self._buffer[n:]
        while len(data) < n:
            chunk = self.sock.recv(n - len(data))
            if not chunk:
                raise FuxError("WebSocket closed mid-frame")
            data += chunk
        return data

    def send_text(self, text: str) -> None:
        self.sock.sendall(encode_frame(text.encode("utf-8"), OP_TEXT))

    def recv_text(self) -> str:
        opcode, payload = self.reader.read_message(self._pong)
        if opcode == OP_CLOSE:
            raise FuxError("WebSocket closed by peer")
        return payload.decode("utf-8", errors="replace")

    def _pong(self, payload: bytes) -> None:
        self.sock.sendall(encode_frame(payload, OP_PONG))

    def close(self) -> None:
        try:
            self.sock.sendall(encode_frame(b"", OP_CLOSE))
            self.sock.close()
        except OSError:
            pass
