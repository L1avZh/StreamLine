# StreamLine

[![CI](https://github.com/L1avZh/StreamLine/actions/workflows/ci.yml/badge.svg)](https://github.com/L1avZh/StreamLine/actions/workflows/ci.yml)

Real-time chat over TCP, from your terminal or your browser.

## Why StreamLine?

Spinning up a quick, private chat room shouldn't require a hosted service or an account. StreamLine
is a single, self-contained app you run yourself — on your machine or a server you control — with
password protection and TLS when you need them.

## Features

- One command to start: pick CLI or web interface, nothing to configure up front
- Real-time group chat over TCP, with optional password auth and TLS encryption
- A local web interface for hosting or joining a chat visually — no separate frontend to install
- A guided CLI for beginners, and direct flags/subcommands for scripting and power users
- Server-owned identities: nicknames are validated and de-duplicated automatically
- Hardened against oversized messages, terminal-escape injection, and unbounded connections

## Quick Start

```bash
pip install -e ".[dev]"
streamline
```

You'll be asked how you want to use StreamLine:

```
Choose how you want to continue:

  1  Command Line Interface
  2  Web Interface
```

- **CLI** walks you through hosting or joining a chat with a few prompts.
- **Web Interface** starts a local server, opens your browser, and shows you the URL.

That's it — no separate frontend build, no manually starting a backend.

## Usage

### CLI

`streamline` with no arguments gives you a guided flow. If you already know what you want, skip the
menu:

```bash
streamline server --password secret        # host a chat
streamline client --nickname alice --host 127.0.0.1 --port 12345   # join one
```

Run `streamline server --help` / `streamline client --help` for the full set of options (TLS,
config files, max clients, and more).

### Web Interface

```bash
streamline web
```

This starts a local server, picks a free port automatically, opens your default browser, and prints
the URL. From the page you can **host a chat** (start a room others can join) or **join a chat**
(connect to a running StreamLine server) — both talk to the exact same chat engine the CLI uses.

The web interface binds to `127.0.0.1` (this machine only) by default. Pass `--host 0.0.0.0` only if
you deliberately want it reachable from your network.

## Configuration

Server and client CLI commands accept `--config path/to/config.json` for defaults you don't want to
retype:

```json
{
  "host": "0.0.0.0",
  "server_port": 54140,
  "nickname": "guest"
}
```

Any matching CLI flag overrides the config file. For TLS, generate a local development certificate
with `./scripts/generate_dev_certs.sh` — see `streamline server --help` for how to use it.

## Architecture

The CLI and the web interface are two thin front ends over the same core: connecting, authenticating,
and sending/receiving chat messages all live in one place, so neither interface can drift out of sync
with the other.

```
        streamline
      (single entry point)
             │
     choose CLI or Web
             │
      ┌──────┴──────┐
      │             │
  Terminal CLI   Web Interface
  (Rich + Click) (FastAPI, local-only)
      │             │
      └──────┬──────┘
             │
      Shared chat core
   (ChatServer / ChatSession)
```

## Development

```bash
pip install -e ".[dev]"
ruff check . && ruff format .   # lint + format
mypy                             # type check
pytest                           # test
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for more.

## Security

- Without a password, anyone who can reach the port can join.
- Without TLS, traffic (including the password) is sent in plaintext — use `--certfile`/`--keyfile`
  (server) and `--use-ssl` (client) on any network you don't fully trust.
- The web interface binds to `127.0.0.1` by default; exposing it further is an explicit choice, not
  the default.

## License

MIT — see [LICENSE](LICENSE).
