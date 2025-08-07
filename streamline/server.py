"""Asynchronous chat server for StreamLine."""
from __future__ import annotations

import asyncio
import logging
import ssl
from asyncio import StreamReader, StreamWriter
from typing import Optional, Set

from .utils import console


class ChatServer:
    """Asynchronous TCP chat server with optional password authentication."""

    def __init__(
        self,
        host: str,
        port: int,
        password: Optional[str] = None,
        ssl_context: Optional[ssl.SSLContext] = None,
    ) -> None:
        self.host = host
        self.port = port
        self.password = password
        self.ssl_context = ssl_context
        self.clients: Set[StreamWriter] = set()
        self.logger = logging.getLogger(__name__)

    async def handle_client(self, reader: StreamReader, writer: StreamWriter) -> None:
        addr = writer.get_extra_info("peername")
        self.logger.info("Client connected %s", addr)

        if self.password is not None:
            writer.write(b"Password: ")
            await writer.drain()
            try:
                received = await reader.readline()
                entered = received.decode().strip()
            except Exception:
                entered = ""
            if entered != self.password:
                writer.write(b"Invalid password\n")
                await writer.drain()
                writer.close()
                await writer.wait_closed()
                self.logger.warning("Client %s failed authentication", addr)
                return
            writer.write(b"Welcome!\n")
            await writer.drain()

        self.clients.add(writer)
        try:
            while True:
                data = await reader.readline()
                if not data:
                    break
                message = data.decode().rstrip()
                await self.broadcast(message, writer)
        except Exception as exc:
            self.logger.error("Error with client %s: %s", addr, exc)
        finally:
            self.clients.discard(writer)
            writer.close()
            await writer.wait_closed()
            self.logger.info("Client disconnected %s", addr)

    async def broadcast(self, message: str, sender: StreamWriter) -> None:
        """Send *message* to all connected clients except *sender*."""
        for client in set(self.clients):
            if client is sender:
                continue
            try:
                client.write(message.encode() + b"\n")
                await client.drain()
            except Exception as exc:
                self.logger.error("Broadcast error: %s", exc)
                self.clients.discard(client)

    async def run(self) -> None:
        server = await asyncio.start_server(
            self.handle_client, self.host, self.port, ssl=self.ssl_context
        )
        addr = ", ".join(str(sock.getsockname()) for sock in server.sockets or [])
        self.logger.info("Server running on %s", addr)
        console.print(f"Server running on [bold]{addr}[/bold]")
        async with server:
            await server.serve_forever()


async def run_server(host: str, port: int, password: Optional[str], ssl_context: Optional[ssl.SSLContext]) -> None:
    """Convenience function to run :class:`ChatServer`."""
    server = ChatServer(host=host, port=port, password=password, ssl_context=ssl_context)
    await server.run()
