"""The Offline Guard (ADR 0001): blocks every network connection during a Conversion Run.

`install()` must run before markitdown or any converter library is imported. It
replaces the socket functions that open connections, send datagrams or resolve
host names, so any attempt to reach a non-loopback address raises
`NetworkBlockedError`, even from a dependency. Loopback stays allowed so local
IPC keeps working. Code that bypasses Python's socket module entirely (the
low-level _socket type, or native code with its own networking) isn't covered.
"""

from __future__ import annotations

import ipaddress
import os
import re
import socket

BLOCKED_MESSAGE = "network access blocked"

_WEB_ADDRESS = re.compile(r"[A-Za-z][A-Za-z0-9+.-]+://")

_LOOPBACK_NAMES = {"localhost", "localhost.localdomain", "ip6-localhost"}

# Library switches that stop model hubs and similar from trying to download.
_OFFLINE_ENVIRONMENT = {
    "HF_HUB_OFFLINE": "1",
    "TRANSFORMERS_OFFLINE": "1",
    "HF_DATASETS_OFFLINE": "1",
}
_PROXY_VARIABLES = ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "http_proxy", "https_proxy", "all_proxy")

_blocked_attempts = 0
_installed = False


class NetworkBlockedError(ConnectionError):
    def __init__(self, destination: object):
        super().__init__(f"{BLOCKED_MESSAGE} (tried to reach {destination!r})")


def blocked_attempts() -> int:
    """How many connection or lookup attempts the guard has blocked so far."""
    return _blocked_attempts


def install() -> None:
    """Block network access for the rest of this process. Safe to call twice."""
    global _installed
    if _installed:
        return
    os.environ.update(_OFFLINE_ENVIRONMENT)
    for name in _PROXY_VARIABLES:
        os.environ.pop(name, None)

    original_connect = socket.socket.connect
    original_connect_ex = socket.socket.connect_ex
    original_sendto = socket.socket.sendto
    original_sendmsg = getattr(socket.socket, "sendmsg", None)  # not on Windows
    original_getaddrinfo = socket.getaddrinfo
    original_lookups = {
        name: getattr(socket, name) for name in ("gethostbyname", "gethostbyname_ex", "gethostbyaddr")
    }

    def connect(sock, address):
        _check(sock.family, address)
        return original_connect(sock, address)

    def connect_ex(sock, address):
        _check(sock.family, address)
        return original_connect_ex(sock, address)

    def sendto(sock, data, *flags_and_address):
        # Datagrams (UDP) reach other machines without connecting first.
        _check(sock.family, flags_and_address[-1])
        return original_sendto(sock, data, *flags_and_address)

    def sendmsg(sock, buffers, ancdata=(), flags=0, address=None):
        if address is not None:
            _check(sock.family, address)
            return original_sendmsg(sock, buffers, ancdata, flags, address)
        return original_sendmsg(sock, buffers, ancdata, flags)

    def getaddrinfo(host, *args, **kwargs):
        if not _is_local_host(host):
            _block(host)
        return original_getaddrinfo(host, *args, **kwargs)

    def lookup(name):
        def resolve(host, *args, **kwargs):
            if not _is_local_host(host):
                _block(host)
            return original_lookups[name](host, *args, **kwargs)

        return resolve

    socket.socket.connect = connect
    socket.socket.connect_ex = connect_ex
    socket.socket.sendto = sendto
    if original_sendmsg is not None:
        socket.socket.sendmsg = sendmsg
    socket.getaddrinfo = getaddrinfo
    for name in original_lookups:
        setattr(socket, name, lookup(name))
    _installed = True


def is_web_address(text: str) -> bool:
    """True for scheme://... addresses. A two-letter minimum keeps "C:\\..." a path."""
    return bool(_WEB_ADDRESS.match(text.strip()))


def self_test() -> bool:
    """True when both a direct connection and a name lookup are blocked."""
    install()
    attempts = (
        lambda: socket.create_connection(("192.0.2.1", 80), timeout=2),  # TEST-NET-1
        lambda: socket.getaddrinfo("example.com", 443),
    )
    for attempt in attempts:
        try:
            attempt()
        except NetworkBlockedError:
            continue
        except OSError:
            return False
        return False
    return True


def _check(family: int, address: object) -> None:
    if family == getattr(socket, "AF_UNIX", object()):
        return
    host = address[0] if isinstance(address, tuple) else address
    if not _is_local_host(host):
        _block(host)


def _is_local_host(host: object) -> bool:
    if host is None:
        return True
    if isinstance(host, bytes):
        host = host.decode("ascii", "replace")
    host = str(host).strip("[]").lower()
    if host in _LOOPBACK_NAMES:
        return True
    try:
        return ipaddress.ip_address(host.split("%", 1)[0]).is_loopback
    except ValueError:
        return False


def _block(destination: object) -> None:
    global _blocked_attempts
    _blocked_attempts += 1
    raise NetworkBlockedError(destination)
