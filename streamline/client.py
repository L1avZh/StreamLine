"""Terminal presentation for a StreamLine chat session.

All protocol logic lives in :class:`streamline.session.ChatSession`; this
module only adapts it to a terminal: printing events with Rich and reading
outgoing messages from stdin.
"""

from __future__ import annotations

import asyncio
import contextlib
import logging
import ssl

from .errors import describe_connection_error
from .events import ChatEvent
from .session import AuthenticationError, ChatSession
from .utils import console

logger = logging.getLogger(__name__)

__all__ = ["AuthenticationError", "TerminalChatClient", "run_client"]


class TerminalChatClient:
    """Drives a :class:`ChatSession` from an interactive terminal."""

    def __init__(
        self,
        host: str,
        port: int,
        nickname: str,
        password: str | None = None,
        ssl_context: ssl.SSLContext | None = None,
    ) -> None:
        self.session = ChatSession(
            host,
            port,
            nickname,
            password=password,
            ssl_context=ssl_context,
            on_event=self._on_event,
        )

    async def _on_event(self, event: ChatEvent) -> None:
        if event.kind == "system":
            console.print(f"* {event.text}", style="yellow")
        elif event.kind == "error":
            console.print(event.text, style="bold red")
        elif event.sender:
            console.print(f"{event.sender}: {event.text}", style="cyan")
        else:
            console.print(event.text, style="cyan")

    async def run(self) -> None:
        try:
            await self.session.connect()
        except (ConnectionError, OSError, ssl.SSLError) as exc:
            logger.info("Connection to %s:%s failed: %s", self.session.host, self.session.port, exc)
            console.print(
                describe_connection_error(exc, self.session.host, self.session.port),
                style="bold red",
            )
            return
        except AuthenticationError as exc:
            console.print(str(exc), style="bold red")
            return

        console.print(
            f"Connected to {self.session.host}:{self.session.port} "
            f"as [bold]{self.session.nickname}[/bold]",
            style="green",
        )
        console.print(
            "Type a message and press Enter. Use /exit to quit, /list to see who's online.",
            style="dim",
        )
        try:
            await self._run_message_loops()
        except (ConnectionError, OSError) as exc:
            logger.info(
                "Connection to %s:%s dropped: %s", self.session.host, self.session.port, exc
            )
            console.print(
                describe_connection_error(exc, self.session.host, self.session.port),
                style="bold red",
            )
        finally:
            await self.session.close()
            console.print("Connection closed", style="red")

    async def _run_message_loops(self) -> None:
        """Run send/receive concurrently; stop both as soon as either ends.

        Without this, typing ``/exit`` (or piping EOF into stdin) would only
        stop the send loop, leaving the client hanging forever waiting for
        the receive loop, which has nothing left to wait for.
        """
        receive_task = asyncio.create_task(self.session.receive_forever())
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

    async def _send_messages(self) -> None:
        loop = asyncio.get_running_loop()
        while True:
            try:
                message = await loop.run_in_executor(None, input)
            except (EOFError, KeyboardInterrupt):
                break
            if message.strip().lower() == "/exit":
                break
            try:
                await self.session.send(message)
            except (ConnectionError, OSError):
                break


async def run_client(
    host: str,
    port: int,
    nickname: str,
    password: str | None,
    ssl_context: ssl.SSLContext | None,
) -> None:
    """Convenience function to run :class:`TerminalChatClient`."""
    await TerminalChatClient(host, port, nickname, password=password, ssl_context=ssl_context).run()
