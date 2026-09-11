# Contributing

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Before opening a PR

```bash
ruff check .
ruff format .
mypy
pytest
```

CI runs the same checks against Python 3.11, 3.12, and 3.13 on every push and pull request.

## Guidelines

- Keep the wire protocol (`streamline/protocol.py`) as the single source of truth for literal
  tokens shared between the client and server; don't duplicate them.
- Any text that came from another client (nicknames, messages) must pass through
  `streamline.utils.sanitize_text` before being displayed or re-broadcast.
- Add a regression test for any bug you fix.
