"""RFC 6455 client: frame round-trips, RFC vectors, handshake vs a fake server."""

from __future__ import annotations

import re
import socket
import threading

import pytest

from fux.errors import FuxError
from fux.ingest.ws import (
    OP_CONT,
    OP_PING,
    OP_TEXT,
    FrameReader,
    WebSocket,
    accept_key_for,
    encode_frame,
)


def reader_for(data: bytes) -> FrameReader:
    buf = bytearray(data)

    def recv_exact(n: int) -> bytes:
        out = bytes(buf[:n])
        del buf[:n]
        assert len(out) == n, "reader ran dry"
        return out

    return FrameReader(recv_exact)


def test_rfc6455_accept_key_vector():
    # RFC 6455 §1.3 worked example
    assert accept_key_for("dGhlIHNhbXBsZSBub25jZQ==") == "s3pPLMBiTxaQ9kYGzzhZRbK+xOo="


def test_rfc6455_masked_hello_vector():
    # RFC 6455 §5.7: a masked single-frame text message "Hello"
    frame = bytes([0x81, 0x85, 0x37, 0xFA, 0x21, 0x3D, 0x7F, 0x9F, 0x4D, 0x51, 0x58])
    opcode, fin, payload = reader_for(frame).read_frame()
    assert (opcode, fin, payload) == (OP_TEXT, True, b"Hello")


def test_rfc6455_unmasked_hello_vector():
    frame = bytes([0x81, 0x05]) + b"Hello"
    assert reader_for(frame).read_frame() == (OP_TEXT, True, b"Hello")


@pytest.mark.parametrize("size", [0, 1, 125, 126, 65535, 65536, 70000])
def test_frame_roundtrip_all_length_encodings(size):
    payload = bytes(i % 251 for i in range(size))
    encoded = encode_frame(payload, OP_TEXT, mask=True)
    opcode, fin, decoded = reader_for(encoded).read_frame()
    assert opcode == OP_TEXT and fin and decoded == payload


def test_fragmented_message_reassembled_with_interleaved_ping():
    frames = (
        encode_frame(b"Hel", OP_TEXT, mask=False, fin=False)
        + encode_frame(b"ping-payload", OP_PING, mask=False)
        + encode_frame(b"lo", OP_CONT, mask=False, fin=True)
    )
    pongs = []
    opcode, message = reader_for(frames).read_message(pongs.append)
    assert (opcode, message) == (OP_TEXT, b"Hello")
    assert pongs == [b"ping-payload"]


def _fake_server(server_sock: socket.socket, behaviour: str) -> None:
    data = b""
    while b"\r\n\r\n" not in data:
        data += server_sock.recv(4096)
    key = re.search(rb"Sec-WebSocket-Key: (\S+)", data).group(1).decode()
    if behaviour == "bad-accept":
        accept = "definitely-wrong"
    else:
        accept = accept_key_for(key)
    server_sock.sendall(
        (
            "HTTP/1.1 101 Switching Protocols\r\n"
            "Upgrade: websocket\r\nConnection: Upgrade\r\n"
            f"Sec-WebSocket-Accept: {accept}\r\n\r\n"
        ).encode()
    )
    if behaviour != "echo-fragmented":
        return

    def recv_exact(n: int) -> bytes:
        out = b""
        while len(out) < n:
            out += server_sock.recv(n - len(out))
        return out

    _, _, payload = FrameReader(recv_exact).read_frame()
    server_sock.sendall(encode_frame(payload[:2], OP_TEXT, mask=False, fin=False))
    server_sock.sendall(encode_frame(b"keepalive", OP_PING, mask=False))
    server_sock.sendall(encode_frame(payload[2:], OP_CONT, mask=False, fin=True))
    try:  # stay alive (absorbing the pong) until the client closes
        while server_sock.recv(4096):
            pass
    except OSError:
        pass


def _client(monkeypatch, behaviour: str) -> WebSocket:
    server_sock, client_sock = socket.socketpair()
    thread = threading.Thread(target=_fake_server, args=(server_sock, behaviour), daemon=True)
    thread.start()
    monkeypatch.setattr(
        "fux.ingest.ws.socket.create_connection", lambda addr, timeout=None: client_sock
    )
    return WebSocket("ws://fake-host:9999/devtools/page/1")


def test_handshake_and_fragmented_echo(monkeypatch):
    ws = _client(monkeypatch, "echo-fragmented")
    ws.send_text("héllo")  # client frames are masked; server unmasks + echoes
    assert ws.recv_text() == "héllo"
    ws.close()


def test_handshake_rejects_bad_accept(monkeypatch):
    with pytest.raises(FuxError, match="Sec-WebSocket-Accept"):
        _client(monkeypatch, "bad-accept")


def test_non_ws_scheme_rejected():
    with pytest.raises(FuxError, match="scheme"):
        WebSocket("wss://secure.test/")
