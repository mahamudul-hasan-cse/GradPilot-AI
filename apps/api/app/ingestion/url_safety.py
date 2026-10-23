"""SSRF guard for outbound ingestion requests.

Only public http(s) targets are allowed. Hostnames are resolved and every
resulting address must be globally routable, so names pointing at loopback,
private, link-local or cloud metadata addresses are rejected.
"""

from __future__ import annotations

import asyncio
import ipaddress
import socket
from urllib.parse import urlparse

ALLOWED_SCHEMES = frozenset({"http", "https"})

BLOCKED_HOSTNAMES = frozenset({
    "localhost",
    "localhost.localdomain",
    "metadata",
    "metadata.google.internal",
    "metadata.azure.internal",
    "instance-data",
    "instance-data.ec2.internal",
})

# Addresses that pass the generic checks but still reach cloud control planes.
BLOCKED_IPS = frozenset({
    ipaddress.ip_address("168.63.129.16"),  # Azure WireServer / platform DNS
})


class UnsafeURLError(ValueError):
    """Raised when a URL targets a disallowed scheme, host, or address."""


def _check_ip(ip: ipaddress.IPv4Address | ipaddress.IPv6Address, host: str) -> None:
    if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped:
        ip = ip.ipv4_mapped
    if (
        ip in BLOCKED_IPS
        or ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_multicast
        or ip.is_reserved
        or ip.is_unspecified
        or not ip.is_global
    ):
        raise UnsafeURLError(f"Host {host!r} resolves to a disallowed address ({ip})")


def _parse(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme.lower() not in ALLOWED_SCHEMES:
        raise UnsafeURLError(f"URL scheme {parsed.scheme!r} is not allowed")
    host = (parsed.hostname or "").rstrip(".").lower()
    if not host:
        raise UnsafeURLError("URL has no host")
    if host in BLOCKED_HOSTNAMES or host.endswith((".localhost", ".internal", ".local")):
        raise UnsafeURLError(f"Host {host!r} is not allowed")
    return host


async def validate_public_url(url: str) -> None:
    """Raise UnsafeURLError unless ``url`` is http(s) and resolves only to public IPs."""
    host = _parse(url)
    try:
        _check_ip(ipaddress.ip_address(host), host)
        return
    except ValueError as exc:
        if isinstance(exc, UnsafeURLError):
            raise

    loop = asyncio.get_running_loop()
    try:
        infos = await loop.getaddrinfo(host, None, type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        raise UnsafeURLError(f"Host {host!r} could not be resolved") from exc
    if not infos:
        raise UnsafeURLError(f"Host {host!r} could not be resolved")
    for info in infos:
        _check_ip(ipaddress.ip_address(info[4][0]), host)
