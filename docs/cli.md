# CLI Reference

`streamline` with no arguments opens the [main menu](getting-started.md). Everything below runs
directly, without the menu — useful for scripting, automation, or muscle memory.

## `streamline server`

Host a chat.

```bash
streamline server --password secret
```

| Flag | Default | Meaning |
|---|---|---|
| `--host` | `0.0.0.0` | Interface to bind |
| `--port` | random free port | Port to bind |
| `--password` | none | Password clients must supply |
| `--certfile`, `--keyfile` | none | Enable TLS (both required together) |
| `--max-clients` | `200` | Maximum simultaneous connections |
| `--config` | none | Load defaults from a JSON file (see below) |

## `streamline client`

Join a chat.

```bash
streamline client --nickname alice --host 127.0.0.1 --port 12345
```

| Flag | Default | Meaning |
|---|---|---|
| `--host` | `127.0.0.1` | Server host |
| `--port` | `12345` | Server port |
| `--nickname` | prompted | Nickname to use |
| `--password` | none | Password, if the server requires one |
| `--use-ssl` | off | Enable TLS |
| `--cafile` | system trust store | CA file to verify a self-signed server certificate |
| `--config` | none | Load defaults from a JSON file |

Once connected: type a message and press Enter. `/exit` disconnects, `/list` shows who's online.

## `streamline web`

Start the web interface without going through the menu.

```bash
streamline web --port 8765
```

| Flag | Default | Meaning |
|---|---|---|
| `--host` | `127.0.0.1` | Interface the control panel binds to — keep this local |
| `--port` | `8765`, or next free | Port to use |
| `--no-browser` | off | Don't open a browser automatically |

## `streamline settings`

```bash
streamline settings show
streamline settings set <key> <value>
streamline settings reset
```

See [configuration.md](configuration.md) for the full list of keys.

## Global options

| Flag | Meaning |
|---|---|
| `--debug` | Verbose diagnostic logging on the console (also settable via `STREAMLINE_DEBUG=1`) |
| `--version` | Print the version and exit |
| `--help` | Available on every command |

## `--config` file format

`--host`/`--port`/`--nickname`/`--password` in this JSON file act as defaults; any matching CLI
flag overrides them.

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

This is separate from the persistent settings described in
[configuration.md](configuration.md) — `--config` is a one-off file you point at explicitly,
useful for scripting a specific server/client invocation.
