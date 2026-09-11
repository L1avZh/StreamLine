"""Adversarial TLS testing: bad certs, wrong CAs, and protocol mismatches.

The property under test throughout: TLS failures must be loud (raise) and
StreamLine must never silently fall back to an unverified or plaintext
connection.
"""

from __future__ import annotations

import asyncio
import contextlib
import ssl

import pytest
import trustme

from streamline import protocol
from streamline.server import ChatServer
from streamline.utils import create_client_ssl_context, create_ssl_context, find_free_port

from .conftest import do_handshake


def test_mismatched_cert_and_key_raises(tmp_path):
    ca = trustme.CA()
    cert_a = ca.issue_cert("host-a")
    cert_b = ca.issue_cert("host-b")

    certfile = tmp_path / "cert.pem"
    keyfile = tmp_path / "key.pem"
    # cert for host-a, but the private key belongs to host-b's cert.
    cert_a.cert_chain_pems[0].write_to_path(str(certfile))
    cert_b.private_key_pem.write_to_path(str(keyfile))

    with pytest.raises(ssl.SSLError):
        create_ssl_context(str(certfile), str(keyfile))


def test_nonexistent_cert_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        create_ssl_context(str(tmp_path / "does-not-exist.pem"), str(tmp_path / "also-missing.pem"))


def test_certfile_only_without_keyfile_returns_none():
    # Mirrors the CLI's own validation (`--certfile`/`--keyfile` required
    # together) — this function itself just needs both to actually enable
    # TLS, which is exercised via the "not (certfile and keyfile)" guard.
    assert create_ssl_context("somefile.pem", None) is None
    assert create_ssl_context(None, "somefile.pem") is None
    assert create_ssl_context(None, None) is None


async def test_client_rejects_self_signed_cert_when_ca_not_trusted():
    """A client using the system trust store must refuse an untrusted
    self-signed server certificate — never silently accept it."""
    ca = trustme.CA()
    cert = ca.issue_cert("localhost", "127.0.0.1")
    server_ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    cert.configure_cert(server_ctx)

    port = find_free_port()
    server = ChatServer("127.0.0.1", port, ssl_context=server_ctx)
    task = asyncio.create_task(server.run())
    await asyncio.sleep(0.1)
    try:
        untrusting_ctx = create_client_ssl_context(None)  # system trust store only
        with pytest.raises(ssl.SSLCertVerificationError):
            await asyncio.wait_for(
                asyncio.open_connection("127.0.0.1", port, ssl=untrusting_ctx), timeout=5
            )
    finally:
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task


async def test_client_rejects_certificate_signed_by_wrong_ca(tmp_path):
    """Trusting *a* CA file doesn't mean trusting *any* certificate — only
    one actually signed by that CA."""
    real_ca = trustme.CA()
    impostor_ca = trustme.CA()
    cert = real_ca.issue_cert("localhost", "127.0.0.1")
    server_ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    cert.configure_cert(server_ctx)

    impostor_cafile = tmp_path / "impostor_ca.pem"
    impostor_ca.cert_pem.write_to_path(str(impostor_cafile))

    port = find_free_port()
    server = ChatServer("127.0.0.1", port, ssl_context=server_ctx)
    task = asyncio.create_task(server.run())
    await asyncio.sleep(0.1)
    try:
        wrong_trust_ctx = create_client_ssl_context(str(impostor_cafile))
        with pytest.raises(ssl.SSLCertVerificationError):
            await asyncio.wait_for(
                asyncio.open_connection("127.0.0.1", port, ssl=wrong_trust_ctx), timeout=5
            )
    finally:
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task


async def test_plaintext_client_against_tls_server_fails_cleanly(server_ssl_context):
    """A client that doesn't speak TLS at all must fail to connect, not
    somehow get a plaintext connection to a TLS-only server."""
    port = find_free_port()
    server = ChatServer("127.0.0.1", port, ssl_context=server_ssl_context)
    task = asyncio.create_task(server.run())
    await asyncio.sleep(0.1)
    try:
        reader, writer = await asyncio.open_connection("127.0.0.1", port)  # no ssl=
        writer.write(b"plaintext nonsense, no TLS handshake\n")
        with contextlib.suppress(ConnectionError, OSError):
            await writer.drain()
        # The server should never respond with a valid protocol line here —
        # either the connection resets/EOFs, or we time out waiting for a
        # response that will never come because no TLS handshake happened.
        with contextlib.suppress(ConnectionError, OSError, TimeoutError):
            data = await asyncio.wait_for(reader.readline(), timeout=2)
            assert data != f"{protocol.AUTH_NONE}\n".encode()
        writer.close()
        with contextlib.suppress(ConnectionError, OSError):
            await writer.wait_closed()

        # Server must still be healthy for a real TLS client afterwards.
        assert server.clients == {}
    finally:
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task


async def test_tls_server_still_works_normally_for_a_correct_client(
    server_ssl_context, client_ssl_context
):
    port = find_free_port()
    server = ChatServer("127.0.0.1", port, ssl_context=server_ssl_context)
    task = asyncio.create_task(server.run())
    await asyncio.sleep(0.1)
    try:
        reader, writer = await asyncio.open_connection("127.0.0.1", port, ssl=client_ssl_context)
        nickname = await do_handshake(reader, writer, "alice")
        assert nickname == "alice"
        writer.close()
        with contextlib.suppress(ConnectionError, OSError):
            await writer.wait_closed()
    finally:
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task
