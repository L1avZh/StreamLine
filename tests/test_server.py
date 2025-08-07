import asyncio
import contextlib
import sys
from pathlib import Path

# Add repository root to path for imports
sys.path.append(str(Path(__file__).resolve().parent.parent))

from streamline.server import ChatServer
from streamline.utils import find_free_port


def test_server_broadcast():
    async def runner():
        port = find_free_port()
        server = ChatServer("127.0.0.1", port)
        server_task = asyncio.create_task(server.run())
        await asyncio.sleep(0.1)
        r1, w1 = await asyncio.open_connection("127.0.0.1", port)
        r2, w2 = await asyncio.open_connection("127.0.0.1", port)
        w1.write(b"hello\n")
        await w1.drain()
        data = await asyncio.wait_for(r2.readline(), timeout=1)
        assert data == b"hello\n"
        w1.close(); await w1.wait_closed()
        w2.close(); await w2.wait_closed()
        server_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await server_task
    asyncio.run(runner())
