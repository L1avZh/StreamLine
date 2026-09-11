# Configuration

StreamLine stores your preferences automatically — there's no file to create or edit by hand.

## Where settings live

Settings are saved outside the app itself, in the OS-standard per-user config location, so they
survive reinstalls and upgrades:

| OS | Location |
|---|---|
| macOS | `~/Library/Application Support/StreamLine/settings.json` |
| Linux | `~/.config/StreamLine/settings.json` (or `$XDG_CONFIG_HOME`) |
| Windows | `%LOCALAPPDATA%\StreamLine\settings.json` |

Logs live in the equivalent per-user *log* directory (`~/Library/Logs/StreamLine` on macOS,
`~/.local/state/StreamLine/log` on Linux, `%LOCALAPPDATA%\StreamLine\Logs` on Windows).

Set `STREAMLINE_CONFIG_DIR` to use a different location for both (useful for testing, containers,
or running more than one isolated instance on the same machine).

## Changing settings

**Web interface:** the gear icon in the top bar.

**CLI, interactively:** option `3` in the main menu.

**CLI, directly:**

```bash
streamline settings show
streamline settings set nickname alice
streamline settings set default_interface web
streamline settings reset
```

## What's stored

| Setting | Meaning |
|---|---|
| `nickname` | Pre-fills the nickname field when joining a chat |
| `default_interface` | What `streamline` with no arguments does: `ask`, `cli`, or `web` |
| `default_host`, `default_port` | Pre-fills the "join" address |
| `web_bind_host` | Interface the web control panel binds to (`127.0.0.1` by default — see [security.md](security.md)) |
| `web_port` | Preferred web interface port (automatic if unset or taken) |
| `web_open_browser` | Whether starting the web interface opens a browser automatically |
| `tls_cafile` | Default CA file for verifying a server's TLS certificate |
| `log_level` | `normal` or `debug` — see below |

**Passwords are never stored.** You're asked for one each time you host or join a
password-protected chat.

## Corrupted settings

If `settings.json` is ever unreadable (manual editing gone wrong, a bad write, etc.), StreamLine
falls back to defaults automatically and renames the broken file to
`settings.corrupted-<timestamp>.json` next to it, rather than silently deleting your data or
crashing.

## Debug logging

Pass `--debug` to any command, or set `STREAMLINE_DEBUG=1`, to also print diagnostic detail to the
console. Full diagnostics are always written to the log file regardless — `--debug` only affects
what's echoed to the terminal.
