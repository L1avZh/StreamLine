"""Core client-side chat session: connect, handshake, send, receive.

This is the single implementation of "being a StreamLine chat client" —
everything that talks to a :class:`~streamline.server.ChatServer` over the
wire. It has no idea whether it's being driven from a terminal or a browser;
:mod:`streamline.client` (terminal) and :mod:`streamline.web.app` (browser,
over a WebSocket) both wrap it instead of re-implementing the protocol.
"""

from __future__ import annotations

import asyncio
import contextlib
import ssl
from asyncio import StreamReader, StreamWriter

from . import protocol
from .events import ChatEvent, OnEvent
from .utils import sanitize_text


class AuthenticationError(RuntimeError):
    """Raised when the server rejects credentials or a nickname."""


class ChatSession:
    """A connection to a StreamLine server: handshake, then send/receive."""

    def __init__(
        self,
        host: str,
        port: int,
        nickname: str,
        password: str | None = None,
        ssl_context: ssl.SSLContext | None = None,
        on_event: OnEvent | None = None,
    ) -> None:
        self.host = host
        self.port = port
        self.requested_nickname = nickname
        self.password = password
        self.ssl_context = ssl_context
        self.nickname: str | None = None
        self._on_event = on_event
        self.reader: StreamReader | None = None
        self.writer: StreamWriter | None = None

    async def _emit(self, event: ChatEvent) -> None:
        if self._on_event is not None:
            await self._on_event(event)

    async def connect(self) -> None:
        """Open the TCP/TLS connection and complete the auth/nickname handshake.

        Raises :class:`AuthenticationError` if the password or nickname is
        rejected, or :class:`ConnectionError`/:class:`OSError` if the
        connection itself fails.
        """
        self.reader, self.writer = await asyncio.open_connection(
            self.host, self.port, ssl=self.ssl_context
        )
        try:
            await self._handshake()
        except BaseException:
            await self.close()
            raise

    async def send(self, message: str) -> None:
        """Send one chat message. Blank messages and ``/exit`` are ignored."""
        message = message.strip()
        if not message or message.lower() == protocol.EXIT_COMMAND:
            return
        await self._write_line(message)

    async def list_online(self) -> None:
        """Ask the server who else is online; the reply arrives as an event."""
        await self._write_line(protocol.LIST_COMMAND)

    async def receive_forever(self) -> None:
        """Read events until the connection closes. Runs until EOF."""
        while True:
            line = await self._read_line()
            if line is None:
                break
            text = sanitize_text(line)
            if not text:
                continue
            if text.startswith(protocol.SYSTEM_PREFIX):
                await self._emit(ChatEvent(kind="system", text=text[len(protocol.SYSTEM_PREFIX) :]))
                continue
            sender, sep, body = text.partition(": ")
            if sep:
                await self._emit(ChatEvent(kind="chat", text=body, sender=sender))
            else:
                await self._emit(ChatEvent(kind="chat", text=text))

    async def close(self) -> None:
        if self.writer:
            self.writer.close()
            with contextlib.suppress(ConnectionError, OSError):
                await self.writer.wait_closed()

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
                raise AuthenticationError("Server requires a password.")
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
                await self._emit(
                    ChatEvent(
                        kind="system",
                        text=f"Nickname '{self.requested_nickname}' was taken; "
                        f"you are '{self.nickname}'.",
                    )
                )
        elif nick_line.startswith(protocol.NICK_FAIL_PREFIX):
            raise AuthenticationError(
                f"Server rejected nickname: {nick_line[len(protocol.NICK_FAIL_PREFIX) :]}"
            )
        else:
            raise AuthenticationError(
                "Unexpected response from server during nickname registration."
            )
