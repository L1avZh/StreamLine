from __future__ import annotations

import asyncio
import contextlib

from streamline import paths
from streamline.server import ChatServer
from streamline.utils import find_free_port, setup_logging

from .conftest import do_handshake

SECRET = "correct-horse-battery-staple"


async def test_password_never_appears_in_log_file():
    setup_logging(debug=True)  # debug=True maximizes what's captured, worst case for a leak
    port = find_free_port()
    server = ChatServer("127.0.0.1", port, password=SECRET)
    task = asyncio.create_task(server.run())
    await asyncio.sleep(0.1)
    try:
        reader, writer = await asyncio.open_connection("127.0.0.1", port)
        await do_handshake(reader, writer, "alice", password=SECRET)
        writer.close()
        await writer.wait_closed()

        reader2, writer2 = await asyncio.open_connection("127.0.0.1", port)
        with contextlib.suppress(RuntimeError):
            await do_handshake(reader2, writer2, "bob", password="wrong-but-also-secret")
        writer2.close()
        await writer2.wait_closed()
    finally:
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task

    log_path = paths.log_file_path()
    assert log_path.exists()
    contents = log_path.read_text(encoding="utf-8")
    assert SECRET not in contents
    assert "wrong-but-also-secret" not in contents
