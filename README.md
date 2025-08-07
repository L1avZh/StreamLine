# StreamLine

Modern asynchronous terminal chat application with optional authentication and TLS encryption.

## Features

- Asynchronous server and client built on `asyncio`
- Colorful output powered by [`rich`](https://rich.readthedocs.io)
- Command line interface using [`click`](https://click.palletsprojects.com)
- Optional pre-shared password authentication
- Optional TLS encryption using user supplied certificates

## Installation

```bash
pip install -r requirements.txt  # if using a virtual environment
```

Rich and Click are required. They are lightweight and will be installed automatically when running the project inside this repository.

## Usage

All commands are exposed through the module `streamline.cli`.

### Start the server

```bash
python -m streamline.cli server --password secret
```

Options:

- `--host` *(default: 0.0.0.0)* – interface to bind
- `--port` – port to bind (defaults to a free port)
- `--password` – optional password clients must supply
- `--certfile`/`--keyfile` – enable TLS by providing certificate and key

### Start a client

```bash
python -m streamline.cli client --nickname alice --host 127.0.0.1 --port 12345
```

Options:

- `--nickname` – name shown with each message (prompted if omitted)
- `--password` – password if the server requires one
- `--use-ssl` – enable TLS; supply `--cafile` to verify server cert

Type messages and press Enter to chat. Use `/exit` to disconnect.

## Development

Run the test suite with:

```bash
pytest
```

## License

MIT
