# Security

StreamLine is meant to be self-hosted and private. This page is a straight explanation of what's
safe by default, what isn't, and why.

## Defaults

- **The web control panel binds to `127.0.0.1`** (this machine only) unless you explicitly pass
  `--host 0.0.0.0` to `streamline web`. It is never exposed to your network by default.
- **A hosted chat server defaults to `0.0.0.0`**, matching `streamline server`'s long-standing
  default — the whole point of hosting is that others can join. If you only want to chat with
  yourself or test locally, bind it to `127.0.0.1` instead.
- **No password is required by default.** Anyone who can reach a chat server's host and port can
  join unless you set one.
- **TLS is off by default.** Without `--certfile`/`--keyfile` (server) and `--use-ssl` (client),
  traffic — including the password — is sent in plaintext. Turn it on for anything beyond a
  trusted local network.
- **Passwords are never persisted or logged.** They're asked for each time and never written to
  `settings.json` or the log file (there's a regression test enforcing this).
- **No telemetry.** StreamLine does not phone home, collect usage data, or check for updates
  without you asking it to.

## Protocol hardening

- Passwords are compared in constant time (`hmac.compare_digest`), not `==`, to avoid timing
  side-channels.
- Messages are capped at 8 KiB; an oversized line disconnects the sender rather than growing the
  server's memory without bound.
- Nicknames and messages are stripped of ANSI escape sequences and control characters before
  being displayed or relayed, preventing terminal-injection from a malicious peer.
- The server enforces a maximum client count (`--max-clients`, default 200) and a handshake
  timeout, so an unauthenticated or slow connection can't tie up resources indefinitely.

## Web interface hardening

Because a browser doesn't apply the usual cross-origin protections to WebSocket connections
against `localhost`, a malicious page open in another tab could otherwise drive your local
StreamLine instance without your knowledge (a well-known class of "attack a service on
localhost via the browser" vulnerability). Every state-changing HTTP endpoint and WebSocket
connection checks the request's `Origin` header and rejects anything that isn't `localhost` or
`127.0.0.1`.

## TLS certificate verification

The client uses the system's default trust store to verify a server's certificate unless you
supply `--cafile` (self-signed certificates). Never disable certificate verification.

## Generating a local TLS certificate

StreamLine never ships with certificates or keys in the repository. For local development or
testing, generate a throwaway self-signed certificate:

```bash
./scripts/generate_dev_certs.sh
streamline server --certfile certs/cert.pem --keyfile certs/key.pem
streamline client --use-ssl --cafile certs/cert.pem ...
```

For anything beyond local development, use a certificate from a real CA (or your internal PKI)
and never commit private keys to version control (`certs/`, `*.pem`, `*.key` are gitignored).

## Reporting a vulnerability

Open a GitHub issue, or a private security advisory if the repository has that enabled, describing
the problem and how to reproduce it.
