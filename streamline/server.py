"""Asynchronous chat server for StreamLine."""

from __future__ import annotations

import asyncio
import contextlib
import logging
import signal
import ssl
from asyncio import StreamReader, StreamWriter
from dataclasses import dataclass, field

from . import protocol
from .events import ChatEvent, OnEvent
from .utils import console, constant_time_equals, sanitize_text, validate_nickname

logger = logging.getLogger(__name__)

# How long the server waits for a slow client's socket buffer to drain
# before giving up on it. Without this, one stalled client could delay
# message delivery to every other connected client.
WRITE_TIMEOUT = 5.0

# How long a client has to complete the auth/nickname handshake before
# being disconnected. Prevents connections that open a socket and never
# speak from tying up server resources indefinitely.
HANDSHAKE_TIMEOUT = 30.0


@dataclass
class ClientState:
    writer: StreamWriter
    nickname: str = field(default="")


class ChatServer:
    """Asynchronous TCP chat server with optional password authentication."""

    def __init__(
        self,
        host: str,
        port: int,
        password: str | None = None,
        ssl_context: ssl.SSLContext | None = None,
        max_clients: int = 200,
        on_event: OnEvent | None = None,
        install_signal_handlers: bool = True,
    ) -> None:
        self.host = host
        self.port = port
        self.password = password
        self.ssl_context = ssl_context
        self.max_clients = max_clients
        self.clients: dict[StreamWriter, ClientState] = {}
        self._on_event = on_event
        self._install_signal_handlers = install_signal_handlers

    async def _emit(self, event: ChatEvent) -> None:
        if self._on_event is not None:
            await self._on_event(event)

    async def _write_line(self, writer: StreamWriter, line: str) -> bool:
        """Write *line* (plus newline) to *writer*. Returns False on failure."""
        try:
            writer.write(line.encode("utf-8") + b"\n")
            await asyncio.wait_for(writer.drain(), timeout=WRITE_TIMEOUT)
            return True
        except (ConnectionError, TimeoutError, OSError):
            return False

    async def _read_line(self, reader: StreamReader) -> str | None:
        """Read one line, enforcing the max line length.

        Returns ``None`` on EOF, a dropped/reset connection, or if the peer
        violated the protocol (oversized line, invalid UTF-8) — any of
        which mean the caller should treat the connection as over and
        clean up, the same as a normal disconnect.
        """
        try:
            data = await reader.readline()
        except (asyncio.LimitOverrunError, ValueError, ConnectionError, OSError):
            return None
        if not data:
            return None
        try:
            return data.decode("utf-8").rstrip("\r\n")
        except UnicodeDecodeError:
            return None

    async def _authenticate(self, reader: StreamReader, writer: StreamWriter) -> bool:
        if self.password is None:
            return await self._write_line(writer, protocol.AUTH_NONE)

        if not await self._write_line(writer, protocol.AUTH_REQUIRED):
            return False
        entered = await self._read_line(reader)
        if entered is not None and constant_time_equals(entered, self.password):
            return await self._write_line(writer, protocol.AUTH_OK)
        await self._write_line(writer, protocol.AUTH_FAIL)
        return False

    def _unique_nickname(self, requested: str) -> str:
        taken = {c.nickname for c in self.clients.values()}
        if requested not in taken:
            return requested
        suffix = 2
        while f"{requested}-{suffix}" in taken:
            suffix += 1
        return f"{requested}-{suffix}"

    async def _register_nickname(self, reader: StreamReader, writer: StreamWriter) -> str | None:
        raw = await self._read_line(reader)
        if raw is None:
            return None
        requested = validate_nickname(sanitize_text(raw))
        if requested is None:
            await self._write_line(writer, f"{protocol.NICK_FAIL_PREFIX}invalid nickname")
            return None
        nickname = self._unique_nickname(requested)
        if not await self._write_line(writer, f"{protocol.NICK_OK_PREFIX}{nickname}"):
            return None
        return nickname

    async def handle_client(self, reader: StreamReader, writer: StreamWriter) -> None:
        addr = writer.get_extra_info("peername")
        logger.info("Client connecting %s", addr)

        if len(self.clients) >= self.max_clients:
            await self._write_line(writer, f"{protocol.NICK_FAIL_PREFIX}server full")
            await self._close(writer)
            logger.warning("Rejected %s: server full (%d clients)", addr, self.max_clients)
            return

        nickname: str | None = None
        try:
            async with asyncio.timeout(HANDSHAKE_TIMEOUT):
                if await self._authenticate(reader, writer):
                    nickname = await self._register_nickname(reader, writer)
                else:
                    logger.warning("Client %s failed authentication", addr)
        except TimeoutError:
            logger.warning("Client %s timed out during handshake", addr)

        if nickname is None:
            await self._close(writer)
            return

        self.clients[writer] = ClientState(writer=writer, nickname=nickname)
        logger.info("Client %s joined as %r", addr, nickname)
        await self.broadcast(f"{protocol.SYSTEM_PREFIX}{nickname} joined the chat", exclude=writer)
        await self._emit(ChatEvent(kind="system", text=f"{nickname} joined the chat"))

        try:
            while True:
                line = await self._read_line(reader)
                if line is None:
                    break
                await self._handle_line(writer, nickname, line)
        finally:
            self.clients.pop(writer, None)
            await self._close(writer)
            logger.info("Client %s (%r) disconnected", addr, nickname)
            await self.broadcast(f"{protocol.SYSTEM_PREFIX}{nickname} left the chat")
            await self._emit(ChatEvent(kind="system", text=f"{nickname} left the chat"))

    @staticmethod
    async def _close(writer: StreamWriter) -> None:
        writer.close()
        with contextlib.suppress(ConnectionError, OSError):
            await writer.wait_closed()

    async def _handle_line(self, writer: StreamWriter, nickname: str, line: str) -> None:
        if line == protocol.LIST_COMMAND:
            names = ", ".join(sorted(c.nickname for c in self.clients.values())) or "(no one else)"
            await self._write_line(writer, f"{protocol.SYSTEM_PREFIX}Online: {names}")
            return
        if line == protocol.EXIT_COMMAND:
            return
        text = sanitize_text(line)
        if not text:
            return
        await self.broadcast(f"{nickname}: {text}", exclude=writer)
        await self._emit(ChatEvent(kind="chat", text=text, sender=nickname))

    async def broadcast(self, message: str, exclude: StreamWriter | None = None) -> None:
        """Send *message* to all connected clients except *exclude*."""
        targets = [w for w in self.clients if w is not exclude]
        results = await asyncio.gather(
            *(self._write_line(w, message) for w in targets), return_exceptions=True
        )
        for target, ok in zip(targets, results, strict=True):
            if ok is not True:
                self.clients.pop(target, None)

    async def _shutdown(self, reason: str) -> None:
        await self.broadcast(f"{protocol.SYSTEM_PREFIX}{reason}")
        for writer in list(self.clients):
            writer.close()
        self.clients.clear()

    async def run(self) -> None:
        loop = asyncio.get_running_loop()
        stop_event = asyncio.Event()
        if self._install_signal_handlers:
            for sig in (signal.SIGINT, signal.SIGTERM):
                # NotImplementedError: unsupported platform (e.g. Windows).
                # ValueError: signal handlers can only be installed from
                # the main thread of the main interpreter.
                with contextlib.suppress(NotImplementedError, ValueError):
                    loop.add_signal_handler(sig, stop_event.set)

        server = await asyncio.start_server(
            self.handle_client,
            self.host,
            self.port,
            ssl=self.ssl_context,
            limit=protocol.MAX_LINE_BYTES,
        )
        addr = ", ".join(str(sock.getsockname()) for sock in server.sockets or [])
        logger.info("Server running on %s", addr)
        console.print(f"Server running on [bold]{addr}[/bold]")

        async with server:
            serve_task = asyncio.create_task(server.serve_forever())
            stop_task = asyncio.create_task(stop_event.wait())
            try:
                await asyncio.wait({serve_task, stop_task}, return_when=asyncio.FIRST_COMPLETED)
            finally:
                stop_task.cancel()
                serve_task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await serve_task
                with contextlib.suppress(asyncio.CancelledError):
                    await stop_task

        logger.info("Server shutting down")
        await self._shutdown("Server is shutting down.")


async def run_server(
    host: str,
    port: int,
    password: str | None,
    ssl_context: ssl.SSLContext | None,
    max_clients: int = 200,
) -> None:
    """Convenience function to run :class:`ChatServer`."""
    server = ChatServer(
        host=host, port=port, password=password, ssl_context=ssl_context, max_clients=max_clients
    )
    await server.run()
