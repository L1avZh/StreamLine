from __future__ import annotations

import asyncio
import contextlib
import ssl

import pytest

from streamline import protocol
from streamline.server import ChatServer
from streamline.utils import find_free_port

from .conftest import do_handshake


async def test_broadcast_excludes_sender(running_server):
    _, port = running_server
    r1, w1 = await asyncio.open_connection("127.0.0.1", port)
    r2, w2 = await asyncio.open_connection("127.0.0.1", port)
    await do_handshake(r1, w1, "alice")
    await do_handshake(r2, w2, "bob")
    # bob joining broadcasts a system message to alice; drain it first.
    await asyncio.wait_for(r1.readline(), timeout=1)

    w1.write(b"hello\n")
    await w1.drain()
    data = await asyncio.wait_for(r2.readline(), timeout=1)
    assert data == b"alice: hello\n"

    for w in (w1, w2):
        w.close()
        await w.wait_closed()


async def test_nickname_collision_gets_renamed(running_server):
    _, port = running_server
    r1, w1 = await asyncio.open_connection("127.0.0.1", port)
    r2, w2 = await asyncio.open_connection("127.0.0.1", port)
    first = await do_handshake(r1, w1, "alice")
    second = await do_handshake(r2, w2, "alice")
    assert first == "alice"
    assert second == "alice-2"

    for w in (w1, w2):
        w.close()
        await w.wait_closed()


async def test_invalid_nickname_rejected(running_server):
    _, port = running_server
    reader, writer = await asyncio.open_connection("127.0.0.1", port)
    await reader.readline()  # AUTH_NONE
    writer.write(b"not a valid nickname!!\n")
    await writer.drain()
    response = (await reader.readline()).decode().strip()
    assert response.startswith(protocol.NICK_FAIL_PREFIX)
    writer.close()
    await writer.wait_closed()


async def test_list_command_reports_online_users(running_server):
    _, port = running_server
    r1, w1 = await asyncio.open_connection("127.0.0.1", port)
    r2, w2 = await asyncio.open_connection("127.0.0.1", port)
    await do_handshake(r1, w1, "alice")
    await do_handshake(r2, w2, "bob")
    await asyncio.wait_for(r1.readline(), timeout=1)  # bob-joined notice

    w1.write(b"/list\n")
    await w1.drain()
    response = (await asyncio.wait_for(r1.readline(), timeout=1)).decode().strip()
    assert "alice" in response and "bob" in response

    for w in (w1, w2):
        w.close()
        await w.wait_closed()


async def test_leave_message_broadcast_on_disconnect(running_server):
    _, port = running_server
    r1, w1 = await asyncio.open_connection("127.0.0.1", port)
    r2, w2 = await asyncio.open_connection("127.0.0.1", port)
    await do_handshake(r1, w1, "alice")
    await do_handshake(r2, w2, "bob")
    await asyncio.wait_for(r1.readline(), timeout=1)  # bob-joined notice

    w2.close()
    await w2.wait_closed()
    leave_notice = await asyncio.wait_for(r1.readline(), timeout=1)
    assert b"bob left the chat" in leave_notice

    w1.close()
    await w1.wait_closed()


async def test_password_authentication_success_and_failure():
    port = find_free_port()
    server = ChatServer("127.0.0.1", port, password="secret")
    task = asyncio.create_task(server.run())
    await asyncio.sleep(0.1)
    try:
        reader, writer = await asyncio.open_connection("127.0.0.1", port)
        nickname = await do_handshake(reader, writer, "alice", password="secret")
        assert nickname == "alice"
        writer.close()
        await writer.wait_closed()

        reader2, writer2 = await asyncio.open_connection("127.0.0.1", port)
        with pytest.raises(RuntimeError, match=protocol.AUTH_FAIL):
            await do_handshake(reader2, writer2, "bob", password="wrong")
        writer2.close()
        await writer2.wait_closed()
    finally:
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task


async def test_max_clients_rejects_extra_connections():
    port = find_free_port()
    server = ChatServer("127.0.0.1", port, max_clients=1)
    task = asyncio.create_task(server.run())
    await asyncio.sleep(0.1)
    try:
        r1, w1 = await asyncio.open_connection("127.0.0.1", port)
        await do_handshake(r1, w1, "alice")

        r2, w2 = await asyncio.open_connection("127.0.0.1", port)
        response = (await asyncio.wait_for(r2.readline(), timeout=1)).decode().strip()
        assert response.startswith(protocol.NICK_FAIL_PREFIX)

        for w in (w1, w2):
            w.close()
            await w.wait_closed()
    finally:
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task


async def test_oversized_line_disconnects_client(running_server):
    _, port = running_server
    reader, writer = await asyncio.open_connection("127.0.0.1", port)
    await do_handshake(reader, writer, "alice")

    writer.write(b"x" * (protocol.MAX_LINE_BYTES + 1024) + b"\n")
    with contextlib.suppress(ConnectionError, OSError):
        await writer.drain()
    data = await asyncio.wait_for(reader.readline(), timeout=2)
    assert data == b""  # server closed the connection
    writer.close()
    with contextlib.suppress(ConnectionError, OSError):
        await writer.wait_closed()


async def test_tls_handshake_succeeds(
    server_ssl_context: ssl.SSLContext, client_ssl_context: ssl.SSLContext
):
    port = find_free_port()
    server = ChatServer("127.0.0.1", port, ssl_context=server_ssl_context)
    task = asyncio.create_task(server.run())
    await asyncio.sleep(0.1)
    try:
        reader, writer = await asyncio.open_connection("127.0.0.1", port, ssl=client_ssl_context)
        nickname = await do_handshake(reader, writer, "alice")
        assert nickname == "alice"
        writer.close()
        await writer.wait_closed()
    finally:
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task
