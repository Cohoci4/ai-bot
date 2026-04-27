"""Shared network safety utilities."""

from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urlparse


def is_internal_address(url: str) -> bool:
    """Check if a URL resolves to a private/loopback/link-local IP address."""
    try:
        parsed = urlparse(url)
        hostname = parsed.hostname
        if not hostname:
            return True

        addr_info = socket.getaddrinfo(hostname, None, socket.AF_UNSPEC, socket.SOCK_STREAM)
        for family, _, _, _, sockaddr in addr_info:
            ip_str = sockaddr[0]
            ip = ipaddress.ip_address(ip_str)
            if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
                return True
    except (socket.gaierror, ValueError, OSError):
        return True
    return False
