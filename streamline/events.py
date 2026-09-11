"""Presentation-agnostic events emitted by the chat core.

Both :class:`~streamline.server.ChatServer` (server-side activity) and
:class:`~streamline.session.ChatSession` (a connected client's view of the
chat) emit :class:`ChatEvent` objects instead of printing directly. This is
what lets the terminal client and the web interface render the same
underlying activity in their own way without duplicating any protocol or
business logic.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Literal

EventKind = Literal["system", "chat", "error"]


@dataclass(frozen=True, slots=True)
class ChatEvent:
    """A single unit of chat activity.

    ``kind`` is ``"system"`` for join/leave/server notices, ``"chat"`` for a
    normal message (``sender`` is the nickname it came from), and
    ``"error"`` for a problem the user should be told about.
    """

    kind: EventKind
    text: str
    sender: str | None = None


OnEvent = Callable[[ChatEvent], Awaitable[None]]
