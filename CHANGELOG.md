# Changelog

All notable changes to this project are documented here.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [3.0.0] - 2026-09-11

Unified entry point, guided CLI, and a new local web interface.

### Added

- `streamline` with no arguments now shows an interactive menu to choose the CLI or the web
  interface, instead of requiring a subcommand up front.
- A guided CLI flow (host vs. join, then a few prompts) for users who don't want to learn flags.
- A local web interface (`streamline web`, or option 2 in the menu): host a chat or join one from
  the browser, with a live activity feed, online-user list, and inline error handling. Binds to
  `127.0.0.1` by default and picks a free port automatically.
- `streamline/session.py`: a new presentation-agnostic `ChatSession` (connect, handshake,
  send/receive) that the terminal client and the web interface both wrap, so neither
  re-implements the wire protocol.
- `streamline/events.py`: a shared `ChatEvent` type emitted by both `ChatServer` (join/leave/
  message activity) and `ChatSession`, letting the web interface show live status without
  polling.

### Changed

- `streamline/client.py` is now a thin terminal adapter (`TerminalChatClient`) over
  `ChatSession`; behavior is unchanged, but the protocol logic it used to own now lives in one
  shared place.
- `ChatServer` gained an optional `on_event` hook and an `install_signal_handlers` flag (off when
  hosted from inside the web interface's process, so it doesn't fight uvicorn for `SIGINT`/
  `SIGTERM`).
- README rewritten to be shorter and scannable; the old wall-of-text version is gone.

### Fixed

- `ChatServer.run()` only guarded `NotImplementedError` when installing signal handlers, but
  installing them off the main thread raises `ValueError` — surfaced by embedding `ChatServer`
  inside the web interface's test client. Both are now handled.

### Dependencies

- Added `fastapi`, `uvicorn`, and `websockets` (runtime) for the web interface; `httpx` (dev) for
  testing it. The CLI-only path (`streamline server` / `streamline client`) does not import any of
  these until the web interface is actually requested, so plain CLI usage stays as fast as before.

## [2.0.0] - 2026-09-11

Full modernization and security hardening pass.

### Security

- Passwords are compared in constant time (`hmac.compare_digest`) instead of `!=`, closing a
  timing side channel.
- The server never closed a client's socket on authentication failure, leaking a connection per
  failed attempt and, under load, exhausting file descriptors; it now always closes.
- Incoming text (nicknames and messages) is stripped of ANSI escape sequences and control
  characters before being displayed or relayed, preventing terminal-injection attacks from a
  malicious peer.
- Lines are capped at 8 KiB; a client that sends an oversized line is disconnected instead of
  being allowed to grow the server's read buffer unbounded.
- The server now owns client identity: nicknames are validated (length/charset) and
  de-duplicated server-side, instead of trusting an arbitrary client-supplied `"name: text"`
  prefix that allowed trivial identity spoofing.
- TLS contexts now pin a minimum of TLS 1.2 on both client and server.
- Removed the empty placeholder `certs/cert.pm` / `certs/key.pm` files that were tracked in git;
  added `scripts/generate_dev_certs.sh` and `.gitignore` rules so real certificates/keys are
  never committed.
- The server now enforces a configurable `--max-clients` cap (default 200) and a per-handshake
  timeout, bounding resource use from unauthenticated or slow connections.

### Reliability

- Fixed a client bug (present in the original implementation) where typing `/exit` or hitting
  EOF only stopped the outgoing-message loop, leaving the process hanging forever waiting on the
  incoming-message loop; both now stop together.
- The server no longer lets one slow/stalled client block message delivery to everyone else
  (broadcasts now fan out concurrently with a per-write timeout).
- Replaced the client's fragile "wait up to 1 second and guess if that was the password prompt"
  handshake with an explicit, deterministic `AUTH_REQUIRED` / `AUTH_NONE` protocol message.
- Added graceful shutdown on `SIGINT`/`SIGTERM`: connected clients get a shutdown notice instead
  of a silent disconnect.

### Added

- `/list` command to see who else is online.
- Join/leave broadcast notifications.
- Nickname collisions are resolved automatically (`alice`, `alice-2`, ...) instead of silently
  allowing two clients to share an identity.

### Developer experience

- `pyproject.toml` (PEP 621) packaging with a `streamline` console script entry point.
- `ruff` for linting/formatting and `mypy --strict` for type checking.
- GitHub Actions CI running lint, format check, type check, and tests on Python 3.11/3.12/3.13.
- Expanded test suite (3 → 28 tests) covering authentication, TLS, nickname collisions,
  oversized messages, max-client limits, and disconnect broadcasts.
- Added `LICENSE` (MIT, as already stated in the README but previously missing as a file),
  `CONTRIBUTING.md`, and a `Dockerfile` for running the server in a container.

### Changed

- Minimum supported Python raised from unspecified/3.9 to 3.11 (3.9 is past end of life).
- Server startup now warns explicitly when running without a password or without TLS.
