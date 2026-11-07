from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urlparse


def is_safe_public_url(url: str) -> bool:
    """Reject non-web, credential-bearing, local, and private-network URLs."""
    try:
        parsed = urlparse(url.strip())
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            return False
        if parsed.username or parsed.password:
            return False
        host = parsed.hostname.rstrip(".").lower()
        if host in {"localhost", "localhost.localdomain"} or host.endswith(".local"):
            return False
        try:
            addresses = {
                info[4][0]
                for info in socket.getaddrinfo(host, None, type=socket.SOCK_STREAM)
            }
        except socket.gaierror:
            return False
        for address in addresses:
            ip = ipaddress.ip_address(address)
            if (
                ip.is_private
                or ip.is_loopback
                or ip.is_link_local
                or ip.is_multicast
                or ip.is_reserved
                or ip.is_unspecified
            ):
                return False
        return True
    except (ValueError, TypeError):
        return False
