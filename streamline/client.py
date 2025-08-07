"""Asynchronous chat client for StreamLine."""
from __future__ import annotations

import asyncio
import logging
import ssl
from asyncio import StreamReader, StreamWriter
from typing import Optional

from .utils import console


class ChatClient:
    """Asynchronous chat client with optional password authentication."""

    def __init__(
        self,
        host: str,
        port: int,
        nickname: str,
        password: Optional[str] = None,
        ssl_context: Optional[ssl.SSLContext] = None,
    ) -> None:
        self.host = host
        self.port = port
        self.nickname = nickname
        self.password = password
        self.ssl_context = ssl_context
        self.reader: Optional[StreamReader] = None
        self.writer: Optional[StreamWriter] = None
        self.logger = logging.getLogger(__name__)

    async def connect(self) -> None:
        try:
            self.reader, self.writer = await asyncio.open_connection(
                self.host, self.port, ssl=self.ssl_context
            )
            await self._authenticate()
            console.print(f"Connected to {self.host}:{self.port}", style="green")
            await asyncio.gather(self._receive_messages(), self._send_messages())
        except Exception as exc:
            self.logger.error("Connection error: %s", exc)
        finally:
            if self.writer:
                self.writer.close()
                await self.writer.wait_closed()
            console.print("Connection closed", style="red")

    async def _authenticate(self) -> None:
        if not (self.reader and self.writer) or self.password is None:
            return
        try:
            prompt = await asyncio.wait_for(self.reader.readline(), timeout=1)
        except asyncio.TimeoutError:
            return
        if b"Password" in prompt:
            self.writer.write((self.password + "\n").encode())
            await self.writer.drain()
            response = await self.reader.readline()
            console.print(response.decode().strip(), style="yellow")
            if b"Invalid" in response:
                raise RuntimeError("Authentication failed")

    async def _receive_messages(self) -> None:
        assert self.reader
        while True:
            data = await self.reader.readline()
            if not data:
                break
            console.print(data.decode().rstrip(), style="cyan")

    async def _send_messages(self) -> None:
        assert self.writer
        loop = asyncio.get_running_loop()
        while True:
            try:
                message = await loop.run_in_executor(None, input)
            except (EOFError, KeyboardInterrupt):
                break
            if message.lower() == "/exit":
                break
            full = f"{self.nickname}: {message}\n"
            self.writer.write(full.encode())
            await self.writer.drain()


async def run_client(host: str, port: int, nickname: str, password: Optional[str], ssl_context: Optional[ssl.SSLContext]) -> None:
    """Convenience function to run :class:`ChatClient`."""
    client = ChatClient(host, port, nickname, password=password, ssl_context=ssl_context)
    await client.connect()
