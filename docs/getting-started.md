# Getting Started

After [installing](installation.md) StreamLine, run:

```bash
streamline
```

## First run

You'll be asked two questions: whether you'd rather use the web interface or the terminal by
default, and what nickname to use. That's it — both are stored so you're never asked again
(change them later from **Settings**).

## The main menu

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

- **Web Interface** starts a local server, opens your browser, and shows you a page to host or
  join a chat.
- **Command Line** asks a couple of questions (host or join, address, nickname) and drops you
  straight into the chat.
- **Settings** lets you change your nickname, default interface, and other preferences —
  no file editing required.

## Hosting a chat

Pick **Host a Chat** (web) or answer `host` (CLI). You'll be asked for a bind address, an
optional port, and an optional password. Once it starts, share the address it shows you with
whoever you want to join.

## Joining a chat

Pick **Join a Chat** (web) or answer `join` (CLI). Enter the host and port someone gave you,
your nickname, and a password if one is required.

## Next

- [cli.md](cli.md) — every command and flag, for scripting and automation
- [configuration.md](configuration.md) — what settings exist and where they live
- [security.md](security.md) — what's safe by default and what to change deliberately
