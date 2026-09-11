# StreamLine

[![CI](https://github.com/L1avZh/StreamLine/actions/workflows/ci.yml/badge.svg)](https://github.com/L1avZh/StreamLine/actions/workflows/ci.yml)

Modern asynchronous terminal chat application with optional password authentication and TLS encryption.

## Features

- Asynchronous server and client built on `asyncio`
- Server-owned identity: nicknames are validated and de-duplicated by the server, not trusted from clients
- Join/leave notifications and a `/list` command to see who's online
- Colorful output powered by [`rich`](https://rich.readthedocs.io)
- Command line interface using [`click`](https://click.palletsprojects.com)
- Optional pre-shared password authentication (constant-time comparison)
- Optional TLS encryption using user-supplied certificates
- Hardened against oversized messages, terminal-escape injection, and unbounded client counts

## Requirements

Python 3.11 or newer.

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"   # editable install with dev tooling (lint, type-check, tests)
```

Or, for just the runtime dependencies:

```bash
pip install -r requirements.txt
```

## Usage

All commands are exposed through the `streamline` console script (or `python -m streamline.cli`).

### Start the server

```bash
streamline server --password secret
```

Options:

- `--host` *(default: 0.0.0.0)* – interface to bind
- `--port` – port to bind (defaults to a free port)
- `--password` – optional password clients must supply
- `--certfile` / `--keyfile` – enable TLS by providing certificate and key (see [TLS](#tls))
- `--max-clients` *(default: 200)* – maximum simultaneous connections
- `--config` – load options from a JSON configuration file

### Start a client

```bash
streamline client --nickname alice --host 127.0.0.1 --port 12345
```

Options:

- `--nickname` – requested nickname (prompted if omitted; the server may rename you on collision)
- `--password` – password if the server requires one
- `--use-ssl` – enable TLS; supply `--cafile` to verify a self-signed server certificate
- `--config` – load defaults from a JSON configuration file

Type a message and press Enter to chat. Use `/exit` to disconnect, `/list` to see who's online.

## TLS

StreamLine never ships with TLS certificates or keys in the repository. Generate a throwaway
self-signed certificate for local development with:

```bash
./scripts/generate_dev_certs.sh
streamline server --certfile certs/cert.pem --keyfile certs/key.pem
streamline client --use-ssl --cafile certs/cert.pem ...
```

For anything beyond local development, use a certificate from a real CA (or your internal PKI) and
never commit private keys to version control.

## Security notes

- Without `--password`, anyone who can reach the port can join.
- Without TLS, all traffic — including the password — is sent in plaintext. Use `--certfile`/`--keyfile`
  (server) and `--use-ssl` (client) on any network you don't fully trust.
- Messages are capped at 8 KiB and stripped of ANSI/control characters before being displayed or
  relayed, to prevent terminal-injection and memory-exhaustion attacks from a malicious peer.

## Configuration

Both client and server commands accept `--config` pointing to a JSON file. Values in the config act
as defaults and can be overridden by CLI options. Example:

```json
{
  "host": "0.0.0.0",
  "server_port": 54140,
  "server_password": null,
  "port": 12345,
  "nickname": "guest",
  "password": null
}
```

## Docker

The server (not the interactive client) can run in a container:

```bash
docker build -t streamline .
docker run --rm -p 54140:54140 streamline
```

## Development

```bash
pip install -e ".[dev]"
ruff check .              # lint
ruff format .             # format
mypy                       # type check
pytest                    # test
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## License

MIT — see [LICENSE](LICENSE).
