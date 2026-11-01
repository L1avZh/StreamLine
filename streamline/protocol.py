"""Wire protocol constants shared by the StreamLine client and server.

The protocol is a simple, line-oriented (``\\n``-terminated) text protocol
over TCP/TLS. It exists as its own module so the client and server never
drift out of sync on the literal tokens exchanged during the handshake.

Handshake sequence
-------------------
1. Server -> Client: ``AUTH_REQUIRED`` if a password is configured,
   otherwise ``AUTH_NONE``.
2. *(only if AUTH_REQUIRED)* Client -> Server: the password.
   Server -> Client: ``AUTH_OK`` or ``AUTH_FAIL``. The connection is closed
   immediately after ``AUTH_FAIL``.
3. Client -> Server: the requested nickname.
   Server -> Client: ``NICK_OK:<assigned nickname>`` (the server may
   rename on collision) or ``NICK_FAIL:<reason>``.
4. Normal chat: each line is either a chat message or a ``/``-prefixed
   command.
"""

from __future__ import annotations

AUTH_REQUIRED = "AUTH_REQUIRED"
AUTH_NONE = "AUTH_NONE"
AUTH_OK = "AUTH_OK"
AUTH_FAIL = "AUTH_FAIL"

NICK_OK_PREFIX = "NICK_OK:"
NICK_FAIL_PREFIX = "NICK_FAIL:"

SYSTEM_PREFIX = "* "
LIST_COMMAND = "/list"
EXIT_COMMAND = "/exit"

# Hard limits that bound resource usage per connection. These are
# deliberately generous for interactive chat while still making a
# single misbehaving or malicious client cheap to reject.
MAX_LINE_BYTES = 8 * 1024
MAX_NICKNAME_LENGTH = 32
MIN_NICKNAME_LENGTH = 1
