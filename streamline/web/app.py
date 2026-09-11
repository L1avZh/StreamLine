"""FastAPI app for the StreamLine web interface.

This module contains no chat protocol logic of its own. It is a thin
adapter: HTTP/WebSocket endpoints that create and drive the exact same
:class:`~streamline.server.ChatServer` and :class:`~streamline.session.ChatSession`
the CLI uses, and translate :class:`~streamline.events.ChatEvent` objects to
and from JSON.
"""

from __future__ import annotations

import asyncio
import contextlib
import logging
import time
from collections import deque
from collections.abc import AsyncIterator
from dataclasses import asdict, dataclass
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .. import __version__
from .. import settings as settings_store
from ..errors import describe_connection_error
from ..events import ChatEvent
from ..server import ChatServer
from ..session import AuthenticationError, ChatSession
from ..utils import create_client_ssl_context, find_free_port, validate_nickname
from .security import is_local_origin

logger = logging.getLogger(__name__)

STATIC_DIR = Path(__file__).resolve().parent / "static"

# How many recent host-side events a newly-opened activity feed sees
# immediately, before live updates start arriving.
HOST_EVENT_HISTORY = 100

# Bind failures (e.g. "port already in use") raise almost immediately once
# the server starts listening; this is how long we wait before assuming a
# background host task has started successfully.
HOST_START_GRACE = 0.2


def _require_local_origin(request: Request) -> None:
    """Block cross-site requests from a page the user has open elsewhere.

    See :mod:`streamline.web.security` for why this matters even though
    the server only binds to localhost.
    """
    if not is_local_origin(request.headers.get("origin")):
        raise HTTPException(403, "Cross-origin requests are not allowed.")


@dataclass
class HostSession:
    server: ChatServer
    task: asyncio.Task[None]
    host: str
    port: int
    started_at: float


class WebState:
    """Everything the web endpoints need that isn't part of a single request."""

    def __init__(self) -> None:
        self.host_session: HostSession | None = None
        self.host_events: deque[ChatEvent] = deque(maxlen=HOST_EVENT_HISTORY)
        self._subscribers: set[asyncio.Queue[ChatEvent]] = set()

    async def on_host_event(self, event: ChatEvent) -> None:
        self.host_events.append(event)
        for queue in list(self._subscribers):
            await queue.put(event)

    @contextlib.asynccontextmanager
    async def subscribe(self) -> AsyncIterator[asyncio.Queue[ChatEvent]]:
        queue: asyncio.Queue[ChatEvent] = asyncio.Queue()
        self._subscribers.add(queue)
        try:
            yield queue
        finally:
            self._subscribers.discard(queue)

    def host_status(self) -> dict[str, object]:
        if self.host_session is None:
            return {"hosting": False}
        session = self.host_session
        return {
            "hosting": True,
            "host": session.host,
            "port": session.port,
            "started_at": session.started_at,
            "connected": sorted(c.nickname for c in session.server.clients.values()),
            "has_password": session.server.password is not None,
        }

    async def stop_host(self) -> None:
        if self.host_session is None:
            return
        task = self.host_session.task
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task
        self.host_session = None


def _event_to_json(event: ChatEvent) -> dict[str, object]:
    return {"kind": event.kind, "text": event.text, "sender": event.sender}


class HostStartRequest(BaseModel):
    host: str = "0.0.0.0"
    port: int | None = None
    password: str | None = None
    max_clients: int = Field(default=200, ge=1, le=10_000)


class JoinRequest(BaseModel):
    host: str
    port: int = Field(ge=1, le=65535)
    nickname: str
    password: str | None = None
    use_ssl: bool = False


class SettingsUpdate(BaseModel):
    """All fields optional: only what's included in the request is changed."""

    nickname: str | None = None
    default_interface: str | None = None
    default_host: str | None = None
    default_port: int | None = None
    connection_timeout: float | None = None
    web_open_browser: bool | None = None
    log_level: str | None = None


def _apply_settings_update(update: SettingsUpdate) -> settings_store.Settings:
    changes = update.model_dump(exclude_unset=True, exclude_none=True)
    if "nickname" in changes and validate_nickname(changes["nickname"]) is None:
        raise HTTPException(400, "Nickname must be 1-32 characters: letters, numbers, _ . -")
    if "default_interface" in changes and changes["default_interface"] not in ("ask", "cli", "web"):
        raise HTTPException(400, "default_interface must be 'ask', 'cli', or 'web'")
    if "log_level" in changes and changes["log_level"] not in ("normal", "debug"):
        raise HTTPException(400, "log_level must be 'normal' or 'debug'")
    port = changes.get("default_port")
    if port is not None and not (1 <= port <= 65535):
        raise HTTPException(400, "default_port must be between 1 and 65535")

    data = asdict(settings_store.load())
    data.update(changes)
    updated = settings_store.Settings(**data).validated()
    try:
        settings_store.save(updated)
    except OSError as exc:
        raise HTTPException(500, f"Could not save settings: {exc}") from exc
    return updated


def create_app() -> FastAPI:
    state = WebState()

    @contextlib.asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        yield
        await state.stop_host()

    app = FastAPI(title="StreamLine", version=__version__, lifespan=lifespan)
    app.state.streamline = state

    @app.get("/api/status")
    async def status() -> dict[str, object]:
        return {"version": __version__, **state.host_status()}

    @app.get("/api/settings")
    async def get_settings() -> dict[str, object]:
        return asdict(settings_store.load())

    @app.post("/api/settings")
    async def update_settings(update: SettingsUpdate, request: Request) -> dict[str, object]:
        _require_local_origin(request)
        return asdict(_apply_settings_update(update))

    @app.post("/api/host/start")
    async def host_start(req: HostStartRequest, request: Request) -> dict[str, object]:
        _require_local_origin(request)
        if state.host_session is not None:
            raise HTTPException(409, "Already hosting a chat. Stop it first.")
        port = req.port or find_free_port()
        server = ChatServer(
            req.host,
            port,
            password=req.password or None,
            max_clients=req.max_clients,
            on_event=state.on_host_event,
            # This server runs inside the web process's own event loop;
            # uvicorn already owns SIGINT/SIGTERM there (Ctrl+C should stop
            # the whole web interface, not just the hosted chat), and the
            # `lifespan` shutdown hook stops this server explicitly anyway.
            install_signal_handlers=False,
        )
        task = asyncio.create_task(server.run())
        await asyncio.sleep(HOST_START_GRACE)
        if task.done():
            exc = task.exception()
            raise HTTPException(400, f"Could not start: {exc or 'unknown error'}")
        state.host_session = HostSession(
            server=server, task=task, host=req.host, port=port, started_at=time.time()
        )
        state.host_events.clear()
        return state.host_status()

    @app.post("/api/host/stop")
    async def host_stop(request: Request) -> dict[str, object]:
        _require_local_origin(request)
        await state.stop_host()
        return state.host_status()

    @app.get("/api/host/status")
    async def host_status() -> dict[str, object]:
        return state.host_status()

    @app.websocket("/ws/host")
    async def ws_host(websocket: WebSocket) -> None:
        if not is_local_origin(websocket.headers.get("origin")):
            await websocket.close(code=1008)
            return
        await websocket.accept()
        async with state.subscribe() as queue:
            for event in list(state.host_events):
                await websocket.send_json(_event_to_json(event))
            try:
                while True:
                    event = await queue.get()
                    await websocket.send_json(_event_to_json(event))
            except WebSocketDisconnect:
                pass

    @app.websocket("/ws/join")
    async def ws_join(websocket: WebSocket) -> None:
        if not is_local_origin(websocket.headers.get("origin")):
            await websocket.close(code=1008)
            return
        await websocket.accept()
        try:
            raw = await websocket.receive_json()
            req = JoinRequest.model_validate(raw)
        except Exception:
            await websocket.send_json({"kind": "error", "text": "Invalid connection request."})
            await websocket.close()
            return

        if validate_nickname(req.nickname) is None:
            await websocket.send_json({"kind": "error", "text": "Invalid nickname."})
            await websocket.close()
            return

        async def forward(event: ChatEvent) -> None:
            await websocket.send_json(_event_to_json(event))

        ssl_context = create_client_ssl_context(None) if req.use_ssl else None
        session = ChatSession(
            req.host,
            req.port,
            req.nickname,
            password=req.password or None,
            ssl_context=ssl_context,
            on_event=forward,
        )
        try:
            await session.connect()
        except AuthenticationError as exc:
            await websocket.send_json({"kind": "error", "text": str(exc)})
            await websocket.close()
            return
        except (ConnectionError, OSError) as exc:
            await websocket.send_json(
                {"kind": "error", "text": describe_connection_error(exc, req.host, req.port)}
            )
            await websocket.close()
            return

        await websocket.send_json({"kind": "connected", "text": session.nickname})
        receive_task = asyncio.create_task(session.receive_forever())
        try:
            while True:
                try:
                    message = await websocket.receive_json()
                except ValueError:
                    # Malformed JSON from the client (or, once decoded, not an
                    # object at all). Not our peer's fault to worry the user
                    # with — drop the one bad frame and keep the connection.
                    logger.debug("Ignoring malformed WebSocket frame from client")
                    continue
                if not isinstance(message, dict):
                    logger.debug("Ignoring non-object WebSocket message from client")
                    continue
                action = message.get("type")
                if action == "send":
                    await session.send(str(message.get("text", "")))
                elif action == "list":
                    await session.list_online()
        except (WebSocketDisconnect, ConnectionError, OSError):
            pass
        finally:
            receive_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await receive_task
            await session.close()

    app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")

    return app
