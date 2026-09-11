# Development

## Setup

```bash
git clone https://github.com/L1avZh/StreamLine.git
cd StreamLine
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Day-to-day workflow

```bash
ruff check . && ruff format .   # lint + format
mypy                             # type check
pytest                          # test
```

See [CONTRIBUTING.md](../CONTRIBUTING.md) for the full checklist before opening a PR.

## Project layout

The user-facing product is one command, `streamline`, but internally it's organized by
responsibility:

```
streamline/
  protocol.py     Wire protocol constants — the single source of truth for the chat protocol
  session.py      ChatSession — connect, handshake, send/receive (shared by CLI and web)
  server.py       ChatServer — the hosting side
  client.py       Terminal presentation over ChatSession
  events.py       ChatEvent — the shared vocabulary ChatServer/ChatSession use to report activity
  settings.py     Persistent user settings (schema, validation, load/save)
  paths.py        OS-appropriate config/log directory resolution
  errors.py       Human-readable connection-error messages, shared by CLI and web
  utils.py        Logging setup, sanitization, TLS context helpers
  cli.py          The Click CLI: menu, guided flow, and server/client/web/settings subcommands
  web/            FastAPI app (app.py), launcher (launcher.py), Origin protection
                  (security.py), and the static frontend (static/)
```

The rule that keeps the CLI and web interface from drifting apart: **all chat protocol logic
lives in `session.py` and `server.py`.** The terminal client and the web interface's WebSocket
handlers are both thin adapters over those — see the note in
[CONTRIBUTING.md](../CONTRIBUTING.md).

## Building release artifacts

See [releases.md](releases.md).
