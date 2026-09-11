# StreamLine

Private, self-hosted chat — one app, a terminal or a browser, no account required.

[![CI](https://github.com/L1avZh/StreamLine/actions/workflows/ci.yml/badge.svg)](https://github.com/L1avZh/StreamLine/actions/workflows/ci.yml)

## Why StreamLine?

Spinning up a quick, private chat room shouldn't require a hosted service, an account, or reading
documentation first. StreamLine is a single app you run yourself — on your machine or a server you
control — with password protection and TLS when you need them.

## Features

- **One command to start.** `streamline` asks how you want to use it and takes it from there —
  nothing to configure up front, nothing to install separately.
- **Two ways in, one engine.** A guided terminal experience for the keyboard-first, a local web
  interface for everyone else — both talk to the exact same chat engine, so neither one lags
  behind the other.
- **Real settings, not a config file to hand-edit.** Nickname, default interface, and connection
  preferences persist automatically, editable from the CLI or the web UI.
- **Private by default.** The web control panel binds to this machine only; nothing phones home.
- **Power-user CLI intact.** `streamline server` / `client` / `web` still work directly, with every
  flag, for scripting and automation.

## Install

**Standalone executable** — no Python required. Download for your platform from the
[latest release](https://github.com/L1avZh/StreamLine/releases/latest) and run it.

**Homebrew** (macOS) — see [docs/installation.md](docs/installation.md) for setup status.

```bash
brew install streamline
```

**Python** (developers, or anyone with Python 3.11+):

```bash
pip install streamline
```

Full details, including Windows/Linux notes: [docs/installation.md](docs/installation.md).

## Quick Start

```bash
streamline
```

```
╭─────────────── StreamLine ───────────────╮
│ Private. Simple. Connected.              │
│                                          │
│   1  Web Interface                       │
│   2  Command Line                        │
│   3  Settings                            │
│   4  Help                                │
│   5  Exit                                │
╰──────────────────────────────────────────╯
```

Pick **Web Interface** and your browser opens automatically to a page where you can host or join
a chat. Pick **Command Line** and a couple of prompts get you straight into one. First time only,
you'll also be asked for a nickname and a default — see
[docs/getting-started.md](docs/getting-started.md).

## Usage

### Web Interface

```bash
streamline web
```

Starts a local server, picks a free port automatically, opens your browser, and prints the URL.
Binds to `127.0.0.1` by default — see [Security](#security).

### CLI

```bash
streamline server --password secret                                 # host a chat
streamline client --nickname alice --host 127.0.0.1 --port 12345    # join one
```

Full reference: [docs/cli.md](docs/cli.md).

## Architecture

The CLI and the web interface are two thin front ends over the same core — connecting,
authenticating, and sending/receiving messages all live in one place, so neither interface can
drift out of sync with the other. Details: [docs/development.md](docs/development.md).

```
        streamline
      (single entry point)
             │
     choose CLI or Web
      ┌──────┴──────┐
  Terminal CLI   Web Interface
  (Rich + Click) (FastAPI, local-only)
      └──────┬──────┘
      Shared chat core
   (ChatServer / ChatSession)
```

## Security

- The web control panel binds to `127.0.0.1` unless you explicitly opt into `--host 0.0.0.0`.
- No password is required by default; anyone who can reach a hosted chat's port can join unless
  you set one.
- TLS is off by default — traffic (including the password) is plaintext until you enable it.
- Passwords are never stored or logged.

Details: [docs/security.md](docs/security.md).

## Development

```bash
pip install -e ".[dev]"
ruff check . && ruff format .   # lint + format
mypy                             # type check
pytest                           # test
```

See [CONTRIBUTING.md](CONTRIBUTING.md) and [docs/development.md](docs/development.md).

## License

MIT — see [LICENSE](LICENSE).
