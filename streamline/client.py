"""Asynchronous chat client for StreamLine."""

from __future__ import annotations

import asyncio
import contextlib
import logging
import ssl
from asyncio import StreamReader, StreamWriter

from . import protocol
from .utils import console, sanitize_text

logger = logging.getLogger(__name__)


class AuthenticationError(RuntimeError):
    """Raised when the server rejects credentials or nickname."""


class ChatClient:
    """Asynchronous chat client with optional password authentication."""

    def __init__(
        self,
        host: str,
        port: int,
        nickname: str,
        password: str | None = None,
        ssl_context: ssl.SSLContext | None = None,
    ) -> None:
        self.host = host
        self.port = port
        self.requested_nickname = nickname
        self.password = password
        self.ssl_context = ssl_context
        self.reader: StreamReader | None = None
        self.writer: StreamWriter | None = None
        self.nickname: str | None = None

    async def connect(self) -> None:
        try:
            self.reader, self.writer = await asyncio.open_connection(
                self.host, self.port, ssl=self.ssl_context
            )
        except (ConnectionError, OSError, ssl.SSLError) as exc:
            console.print(f"Could not connect to {self.host}:{self.port}: {exc}", style="bold red")
            return

        try:
            await self._handshake()
            console.print(
                f"Connected to {self.host}:{self.port} as [bold]{self.nickname}[/bold]",
                style="green",
            )
            console.print(
                "Type a message and press Enter. Use /exit to quit, /list to see who's online.",
                style="dim",
            )
            await self._run_message_loops()
        except AuthenticationError as exc:
            console.print(str(exc), style="bold red")
        except (ConnectionError, OSError) as exc:
            logger.error("Connection error: %s", exc)
            console.print(f"Connection error: {exc}", style="bold red")
        finally:
            if self.writer:
                self.writer.close()
                with contextlib.suppress(ConnectionError, OSError):
                    await self.writer.wait_closed()
            console.print("Connection closed", style="red")

    async def _read_line(self) -> str | None:
        assert self.reader is not None
        data = await self.reader.readline()
        if not data:
            return None
        return data.decode("utf-8", errors="replace").rstrip("\r\n")

    async def _write_line(self, line: str) -> None:
        assert self.writer is not None
        self.writer.write(line.encode("utf-8") + b"\n")
        await self.writer.drain()

    async def _handshake(self) -> None:
        auth_line = await self._read_line()
        if auth_line == protocol.AUTH_REQUIRED:
            if self.password is None:
                raise AuthenticationError("Server requires a password (use --password).")
            await self._write_line(self.password)
            response = await self._read_line()
            if response != protocol.AUTH_OK:
                raise AuthenticationError("Authentication failed: incorrect password.")
        elif auth_line != protocol.AUTH_NONE:
            raise AuthenticationError("Unexpected response from server during authentication.")

        await self._write_line(self.requested_nickname)
        nick_line = await self._read_line()
        if nick_line is None:
            raise AuthenticationError("Server closed the connection during handshake.")
        if nick_line.startswith(protocol.NICK_OK_PREFIX):
            self.nickname = nick_line[len(protocol.NICK_OK_PREFIX) :]
            if self.nickname != self.requested_nickname:
                console.print(
                    f"Nickname '{self.requested_nickname}' was taken; you are '{self.nickname}'.",
                    style="yellow",
                )
        elif nick_line.startswith(protocol.NICK_FAIL_PREFIX):
            raise AuthenticationError(
                f"Server rejected nickname: {nick_line[len(protocol.NICK_FAIL_PREFIX) :]}"
            )
        else:
            raise AuthenticationError(
                "Unexpected response from server during nickname registration."
            )

    async def _run_message_loops(self) -> None:
        """Run send/receive concurrently; stop both as soon as either ends.

        Without this, typing ``/exit`` (or piping EOF into stdin) would only
        stop the send loop, leaving the client hanging forever waiting for
        the receive loop, which has nothing left to wait for.
        """
        receive_task = asyncio.create_task(self._receive_messages())
        send_task = asyncio.create_task(self._send_messages())
        done, pending = await asyncio.wait(
            {receive_task, send_task}, return_when=asyncio.FIRST_COMPLETED
        )
        for task in pending:
            task.cancel()
        for task in pending:
            with contextlib.suppress(asyncio.CancelledError):
                await task
        for task in done:
            task.result()

    async def _receive_messages(self) -> None:
        while True:
            line = await self._read_line()
            if line is None:
                break
            text = sanitize_text(line)
            if text.startswith(protocol.SYSTEM_PREFIX):
                console.print(text, style="yellow")
            else:
                console.print(text, style="cyan")

    async def _send_messages(self) -> None:
        assert self.writer is not None
        loop = asyncio.get_running_loop()
        while True:
            try:
                message = await loop.run_in_executor(None, input)
            except (EOFError, KeyboardInterrupt):
                break
            message = message.strip()
            if not message:
                continue
            if message.lower() == protocol.EXIT_COMMAND:
                break
            try:
                await self._write_line(message)
            except (ConnectionError, OSError):
                break


async def run_client(
    host: str,
    port: int,
    nickname: str,
    password: str | None,
    ssl_context: ssl.SSLContext | None,
) -> None:
    """Convenience function to run :class:`ChatClient`."""
    client = ChatClient(host, port, nickname, password=password, ssl_context=ssl_context)
    await client.connect()
