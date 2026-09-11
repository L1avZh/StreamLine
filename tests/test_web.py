from __future__ import annotations

from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from streamline import settings as settings_store
from streamline.web.app import create_app


def make_client() -> TestClient:
    return TestClient(create_app())


def test_status_reports_not_hosting():
    with make_client() as client:
        response = client.get("/api/status")
        assert response.status_code == 200
        assert response.json()["hosting"] is False


def test_host_start_and_stop():
    with make_client() as client:
        response = client.post("/api/host/start", json={"host": "127.0.0.1", "port": None})
        assert response.status_code == 200
        data = response.json()
        assert data["hosting"] is True
        assert data["host"] == "127.0.0.1"
        assert isinstance(data["port"], int)

        status = client.get("/api/status")
        assert status.json()["hosting"] is True

        stopped = client.post("/api/host/stop")
        assert stopped.json()["hosting"] is False


def test_host_start_conflict_when_already_hosting():
    with make_client() as client:
        first = client.post("/api/host/start", json={"host": "127.0.0.1", "port": None})
        assert first.status_code == 200
        second = client.post("/api/host/start", json={"host": "127.0.0.1", "port": None})
        assert second.status_code == 409
        client.post("/api/host/stop")


def test_join_websocket_rejects_invalid_nickname():
    with make_client() as client:
        start = client.post("/api/host/start", json={"host": "127.0.0.1", "port": None})
        port = start.json()["port"]
        with client.websocket_connect("/ws/join") as ws:
            ws.send_json({"host": "127.0.0.1", "port": port, "nickname": "not valid!!"})
            data = ws.receive_json()
            assert data["kind"] == "error"
        client.post("/api/host/stop")


def test_join_websocket_connects_and_relays_messages():
    with make_client() as client:
        start = client.post("/api/host/start", json={"host": "127.0.0.1", "port": None})
        port = start.json()["port"]

        with (
            client.websocket_connect("/ws/join") as alice,
            client.websocket_connect("/ws/join") as bob,
        ):
            alice.send_json({"host": "127.0.0.1", "port": port, "nickname": "alice"})
            assert alice.receive_json() == {"kind": "connected", "text": "alice"}

            bob.send_json({"host": "127.0.0.1", "port": port, "nickname": "bob"})
            assert bob.receive_json() == {"kind": "connected", "text": "bob"}

            # alice sees bob's join notice
            join_notice = alice.receive_json()
            assert join_notice["kind"] == "system"
            assert "bob joined" in join_notice["text"]

            alice.send_json({"type": "send", "text": "hello bob"})
            received = bob.receive_json()
            assert received == {"kind": "chat", "text": "hello bob", "sender": "alice"}

        client.post("/api/host/stop")


def test_join_websocket_reports_connection_error_for_unreachable_host():
    with make_client() as client, client.websocket_connect("/ws/join") as ws:
        ws.send_json({"host": "127.0.0.1", "port": 1, "nickname": "alice"})
        data = ws.receive_json()
        assert data["kind"] == "error"


def test_get_settings_returns_persisted_defaults():
    with make_client() as client:
        response = client.get("/api/settings")
        assert response.status_code == 200
        assert response.json()["nickname"] == "guest"


def test_post_settings_persists_changes():
    with make_client() as client:
        response = client.post(
            "/api/settings", json={"nickname": "alice", "web_open_browser": False}
        )
        assert response.status_code == 200
        assert response.json()["nickname"] == "alice"
        assert response.json()["web_open_browser"] is False

        persisted = settings_store.load()
        assert persisted.nickname == "alice"
        assert persisted.web_open_browser is False


def test_post_settings_rejects_invalid_nickname():
    with make_client() as client:
        response = client.post("/api/settings", json={"nickname": "not valid!!"})
        assert response.status_code == 400


def test_post_settings_rejects_invalid_default_interface():
    with make_client() as client:
        response = client.post("/api/settings", json={"default_interface": "carrier-pigeon"})
        assert response.status_code == 400


def test_mutating_requests_reject_foreign_origin():
    with make_client() as client:
        response = client.post(
            "/api/host/start",
            json={"host": "127.0.0.1", "port": None},
            headers={"Origin": "https://evil.example"},
        )
        assert response.status_code == 403


def test_mutating_requests_allow_localhost_origin():
    with make_client() as client:
        response = client.post(
            "/api/host/start",
            json={"host": "127.0.0.1", "port": None},
            headers={"Origin": "http://127.0.0.1:8765"},
        )
        assert response.status_code == 200
        client.post("/api/host/stop")


def test_websocket_rejects_foreign_origin():
    with make_client() as client:
        try:
            with client.websocket_connect("/ws/join", headers={"Origin": "https://evil.example"}):
                raise AssertionError("connection should have been rejected")
        except WebSocketDisconnect as exc:
            assert exc.code == 1008
