from __future__ import annotations

import asyncio
import contextlib
import ssl
from collections.abc import AsyncIterator, Iterator
from pathlib import Path

import pytest
import pytest_asyncio
import trustme

from streamline import protocol
from streamline.server import ChatServer
from streamline.utils import find_free_port


@pytest.fixture(autouse=True)
def isolated_config_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[Path]:
    """Never touch the real user's StreamLine settings/logs while testing."""
    monkeypatch.setenv("STREAMLINE_CONFIG_DIR", str(tmp_path / "config"))
    yield tmp_path


@pytest.fixture
def ca() -> trustme.CA:
    return trustme.CA()


@pytest.fixture
def server_ssl_context(ca: trustme.CA) -> ssl.SSLContext:
    cert = ca.issue_cert("localhost", "127.0.0.1")
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    cert.configure_cert(context)
    return context


@pytest.fixture
def client_ssl_context(ca: trustme.CA) -> ssl.SSLContext:
    context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
    ca.configure_trust(context)
    context.check_hostname = False
    return context


@pytest_asyncio.fixture
async def running_server() -> AsyncIterator[tuple[ChatServer, int]]:
    port = find_free_port()
    server = ChatServer("127.0.0.1", port)
    task = asyncio.create_task(server.run())
    await asyncio.sleep(0.1)
    try:
        yield server, port
    finally:
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task


async def do_handshake(
    reader: asyncio.StreamReader,
    writer: asyncio.StreamWriter,
    nickname: str,
    password: str | None = None,
) -> str:
    """Perform the client side of the handshake; return the assigned nickname."""
    auth_line = (await reader.readline()).decode().strip()
    if auth_line == protocol.AUTH_REQUIRED:
        assert password is not None
        writer.write((password + "\n").encode())
        await writer.drain()
        response = (await reader.readline()).decode().strip()
        if response != protocol.AUTH_OK:
            raise RuntimeError(response)
    writer.write((nickname + "\n").encode())
    await writer.drain()
    nick_line = (await reader.readline()).decode().strip()
    if not nick_line.startswith(protocol.NICK_OK_PREFIX):
        raise RuntimeError(nick_line)
    return nick_line[len(protocol.NICK_OK_PREFIX) :]
