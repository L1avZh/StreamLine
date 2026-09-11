"""Adversarial / edge-case testing for ChatServer.

These tests exist to break things: malformed input, misbehaving clients,
concurrency, and resource cleanup — not just the happy path already
covered by test_server.py.
"""

from __future__ import annotations

import asyncio
import contextlib
import socket
import struct

import pytest

from streamline import protocol
from streamline.server import ChatServer
from streamline.utils import find_free_port

from .conftest import do_handshake


def _abrupt_rst_connection(port: int) -> None:
    """Open a TCP connection to *port* and kill it with a real RST packet
    (SO_LINGER with a zero timeout), not a graceful FIN close.

    A plain ``writer.close()`` sends a FIN, which readline() sees as a
    clean EOF — that path was already handled. A RST is what a client
    crashing, a mobile network dropping, or a firewall resetting the
    connection actually looks like on the wire, and it surfaces to the
    reader as ``ConnectionResetError`` instead of EOF.
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(("127.0.0.1", port))
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, struct.pack("ii", 1, 0))
    sock.close()


@pytest.mark.parametrize(
    "nickname",
    [
        "",  # empty
        "   ",  # whitespace only
        "a" * 33,  # over the limit
        "álice",  # unicode
        "🙂",  # emoji
        "alice bob",  # embedded space
        "alice\tbob",  # tab
        "../../etc/passwd",  # path-traversal-shaped
        "<script>alert(1)</script>",  # HTML/script injection shaped
        "NICK_OK:fake",  # protocol-token-shaped
    ],
)
async def test_invalid_nicknames_are_all_rejected(running_server, nickname):
    _, port = running_server
    reader, writer = await asyncio.open_connection("127.0.0.1", port)
    await reader.readline()  # AUTH_NONE
    writer.write(nickname.encode("utf-8", errors="surrogateescape") + b"\n")
    with contextlib.suppress(ConnectionError, OSError):
        await writer.drain()
    response = await asyncio.wait_for(reader.readline(), timeout=2)
    assert response.decode(errors="replace").startswith(protocol.NICK_FAIL_PREFIX)
    writer.close()
    with contextlib.suppress(ConnectionError, OSError):
        await writer.wait_closed()


async def test_nickname_at_exactly_max_length_is_accepted(running_server):
    _, port = running_server
    reader, writer = await asyncio.open_connection("127.0.0.1", port)
    nickname = "a" * protocol.MAX_NICKNAME_LENGTH
    assigned = await do_handshake(reader, writer, nickname)
    assert assigned == nickname
    writer.close()
    with contextlib.suppress(ConnectionError, OSError):
        await writer.wait_closed()


async def test_client_disconnecting_immediately_after_connect_does_not_crash_server(
    running_server,
):
    server, port = running_server
    reader, writer = await asyncio.open_connection("127.0.0.1", port)
    writer.close()  # no handshake at all
    with contextlib.suppress(ConnectionError, OSError):
        await writer.wait_closed()
    await asyncio.sleep(0.2)

    # Server must still be fully functional afterwards.
    reader2, writer2 = await asyncio.open_connection("127.0.0.1", port)
    nickname = await do_handshake(reader2, writer2, "alice")
    assert nickname == "alice"
    assert len(server.clients) == 1
    writer2.close()
    with contextlib.suppress(ConnectionError, OSError):
        await writer2.wait_closed()


async def test_client_sending_garbage_bytes_before_handshake_does_not_crash_server(
    running_server,
):
    server, port = running_server
    reader, writer = await asyncio.open_connection("127.0.0.1", port)
    await reader.readline()  # AUTH_NONE
    writer.write(b"\xff\xfe\x00\x01not valid utf-8 \xdd\xee\n")
    with contextlib.suppress(ConnectionError, OSError):
        await writer.drain()
    data = await asyncio.wait_for(reader.readline(), timeout=2)
    assert data == b""  # server closed the connection rather than crashing
    writer.close()
    with contextlib.suppress(ConnectionError, OSError):
        await writer.wait_closed()

    # Server must still work for the next client.
    reader2, writer2 = await asyncio.open_connection("127.0.0.1", port)
    assert await do_handshake(reader2, writer2, "alice") == "alice"
    writer2.close()
    with contextlib.suppress(ConnectionError, OSError):
        await writer2.wait_closed()


async def test_abrupt_connection_reset_during_handshake_does_not_crash_server(running_server):
    """Regression test: ChatServer._read_line() only caught
    LimitOverrunError/ValueError, not ConnectionError/OSError. A real RST
    mid-handshake (as opposed to a graceful FIN) raised ConnectionResetError
    out of readline(), which propagated all the way past handle_client as
    an unhandled exception in client_connected_cb — skipping cleanup and
    showing up as a scary error for a completely ordinary event (a client's
    network dropping)."""
    server, port = running_server
    _abrupt_rst_connection(port)
    await asyncio.sleep(0.3)

    # Server must still be fully healthy for a real client afterwards.
    reader, writer = await asyncio.open_connection("127.0.0.1", port)
    assert await do_handshake(reader, writer, "alice") == "alice"
    assert len(server.clients) == 1
    writer.close()
    with contextlib.suppress(ConnectionError, OSError):
        await writer.wait_closed()


async def test_abrupt_connection_reset_after_joining_does_not_crash_server(running_server):
    server, port = running_server
    reader, writer = await asyncio.open_connection("127.0.0.1", port)
    await do_handshake(reader, writer, "alice")

    # Simulate alice's network dropping mid-session: a real RST, not /exit.
    sock = writer.get_extra_info("socket")
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, struct.pack("ii", 1, 0))
    writer.close()

    await asyncio.sleep(0.3)
    assert server.clients == {}, "the reset client must be cleaned up, not left as a ghost entry"

    # Server must still be fully healthy for a new client afterwards.
    reader2, writer2 = await asyncio.open_connection("127.0.0.1", port)
    assert await do_handshake(reader2, writer2, "bob") == "bob"
    writer2.close()
    with contextlib.suppress(ConnectionError, OSError):
        await writer2.wait_closed()


async def test_handshake_timeout_disconnects_silent_client(running_server, monkeypatch):
    server, port = running_server
    monkeypatch.setattr("streamline.server.HANDSHAKE_TIMEOUT", 0.3)
    reader, writer = await asyncio.open_connection("127.0.0.1", port)
    await reader.readline()  # AUTH_NONE — then just... never send a nickname.
    data = await asyncio.wait_for(reader.readline(), timeout=2)
    assert data == b""  # server gave up and closed the connection
    writer.close()
    with contextlib.suppress(ConnectionError, OSError):
        await writer.wait_closed()
    assert len(server.clients) == 0


async def test_ansi_escape_sequences_are_stripped_end_to_end(running_server):
    _, port = running_server
    r1, w1 = await asyncio.open_connection("127.0.0.1", port)
    r2, w2 = await asyncio.open_connection("127.0.0.1", port)
    await do_handshake(r1, w1, "alice")
    await do_handshake(r2, w2, "bob")
    await asyncio.wait_for(r1.readline(), timeout=1)  # bob-joined notice

    malicious = "\x1b[2J\x1b[31mFAKE SYSTEM MESSAGE\x1b[0m"
    w1.write(malicious.encode() + b"\n")
    await w1.drain()
    received = await asyncio.wait_for(r2.readline(), timeout=1)
    text = received.decode()
    assert "\x1b" not in text
    assert text == "alice: FAKE SYSTEM MESSAGE\n"

    for w in (w1, w2):
        w.close()
        with contextlib.suppress(ConnectionError, OSError):
            await w.wait_closed()


async def test_purely_whitespace_message_is_dropped_not_broadcast(running_server):
    _, port = running_server
    r1, w1 = await asyncio.open_connection("127.0.0.1", port)
    r2, w2 = await asyncio.open_connection("127.0.0.1", port)
    await do_handshake(r1, w1, "alice")
    await do_handshake(r2, w2, "bob")
    await asyncio.wait_for(r1.readline(), timeout=1)  # bob-joined notice

    w1.write(b"   \n")  # whitespace-only
    await w1.drain()
    w1.write(b"real message\n")
    await w1.drain()
    # The whitespace-only message must never arrive; the next thing bob sees
    # is the real message.
    received = await asyncio.wait_for(r2.readline(), timeout=1)
    assert received == b"alice: real message\n"

    for w in (w1, w2):
        w.close()
        with contextlib.suppress(ConnectionError, OSError):
            await w.wait_closed()


async def test_fifty_concurrent_clients_all_connect_and_broadcast_reaches_everyone():
    port = find_free_port()
    server = ChatServer("127.0.0.1", port, max_clients=100)
    task = asyncio.create_task(server.run())
    await asyncio.sleep(0.1)
    try:
        n = 50
        conns = []
        for i in range(n):
            reader, writer = await asyncio.open_connection("127.0.0.1", port)
            nickname = await do_handshake(reader, writer, f"user{i}")
            assert nickname == f"user{i}"
            conns.append((reader, writer))
        assert len(server.clients) == n

        # Drain everyone's join-notice backlog before the broadcast test.
        for reader, _ in conns[:-1]:
            with contextlib.suppress(TimeoutError):
                while True:
                    await asyncio.wait_for(reader.readline(), timeout=0.05)

        sender_reader, sender_writer = conns[-1]
        sender_writer.write(b"broadcast to everyone\n")
        await sender_writer.drain()

        received_count = 0
        for reader, _writer in conns[:-1]:
            with contextlib.suppress(TimeoutError):
                line = await asyncio.wait_for(reader.readline(), timeout=2)
                if line.endswith(b"broadcast to everyone\n"):
                    received_count += 1
        assert received_count == n - 1
    finally:
        for _, writer in conns:
            writer.close()
            with contextlib.suppress(ConnectionError, OSError):
                await writer.wait_closed()
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task


async def test_rapid_connect_disconnect_cycles_leave_no_leaked_state():
    port = find_free_port()
    server = ChatServer("127.0.0.1", port)
    task = asyncio.create_task(server.run())
    await asyncio.sleep(0.1)
    try:
        for i in range(30):
            reader, writer = await asyncio.open_connection("127.0.0.1", port)
            await do_handshake(reader, writer, f"cycler{i}")
            writer.close()
            with contextlib.suppress(ConnectionError, OSError):
                await writer.wait_closed()
        # Give the server a moment to process the last disconnect.
        for _ in range(20):
            if not server.clients:
                break
            await asyncio.sleep(0.05)
        assert server.clients == {}, "server still thinks disconnected clients are connected"
    finally:
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task


async def test_concurrent_password_authentication_does_not_corrupt_state():
    port = find_free_port()
    server = ChatServer("127.0.0.1", port, password="secret")
    task = asyncio.create_task(server.run())
    await asyncio.sleep(0.1)

    async def connect_one(i: int) -> str:
        reader, writer = await asyncio.open_connection("127.0.0.1", port)
        nickname = await do_handshake(reader, writer, f"user{i}", password="secret")
        writer.close()
        with contextlib.suppress(ConnectionError, OSError):
            await writer.wait_closed()
        return nickname

    try:
        results = await asyncio.gather(*(connect_one(i) for i in range(20)))
        assert sorted(results) == sorted(f"user{i}" for i in range(20))
    finally:
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task
