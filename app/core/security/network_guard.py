"""Ag guvenligi - SSRF ve network korumasi.

Strict IPv4/IPv6 kontrolleri, SSRF engelleme,
response body boyut limitleme.
"""

import ipaddress
import logging
import re
from typing import Any
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

_PRIVATE_RANGES = [
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("0.0.0.0/8"),
]

_PRIVATE_RANGES_V6 = [
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
    ipaddress.ip_network("fe80::/10"),
    ipaddress.ip_network("::ffff:0:0/96"),
    ipaddress.ip_network("2002::/16"),
    ipaddress.ip_network("2001::/32"),
]

_MAX_RESPONSE_BODY = 10 * 1024 * 1024
SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "X-Frame-Options": "DENY",
    "Content-Security-Policy": "default-src 'self'",
}


class NetworkGuard:
    """Ag guvenligi koruyucu."""

    def __init__(self, max_body_size=_MAX_RESPONSE_BODY, block_plaintext_ws=True):
        """NetworkGuard baslatir."""
        self._allowed_hosts = set()
        self._blocked_hosts = set()
        self._max_body_size = max_body_size
        self._block_plaintext_ws = block_plaintext_ws
        self._request_count = 0
        self._blocked_count = 0

    def is_private_ip(self, ip_str):
        """IP private/reserved kontrolu."""
        try:
            addr = ipaddress.ip_address(ip_str)
        except ValueError:
            return True
        if isinstance(addr, ipaddress.IPv4Address):
            return any(addr in n for n in _PRIVATE_RANGES)
        elif isinstance(addr, ipaddress.IPv6Address):
            return any(addr in n for n in _PRIVATE_RANGES_V6)
        return True
    def validate_url(self, url):
        """URL SSRF guvenlik kontrolu."""
        self._request_count += 1
        if not url:
            return False, "Bos URL"
        try:
            parsed = urlparse(url)
        except Exception:
            return False, "URL parse hatasi"
        scheme = parsed.scheme.lower()
        if scheme not in ("http", "https", "wss"):
            if scheme == "ws":
                if self._block_plaintext_ws:
                    host = parsed.hostname or ""
                    if host not in ("localhost", "127.0.0.1", "::1"):
                        self._blocked_count += 1
                        return False, "Plaintext ws:// non-loopback engellendi"
            elif scheme not in ("ws",):
                self._blocked_count += 1
                return False, f"Izin verilmeyen scheme: {scheme}"
        host = parsed.hostname or ""
        if not host:
            self._blocked_count += 1
            return False, "Host bulunamadi"
        if host in self._blocked_hosts:
            self._blocked_count += 1
            return False, f"Engellenen host: {host}"
        if self._allowed_hosts and host not in self._allowed_hosts:
            if self.is_private_ip(host):
                self._blocked_count += 1
                return False, f"Private IP engellendi: {host}"
        if self.is_private_ip(host):
            self._blocked_count += 1
            return False, f"Private/reserved IP: {host}"
        return True, "OK"
    def validate_ipv4_literal(self, ip_str):
        """Strict dotted-decimal IPv4."""
        pat = r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$"
        if not re.match(pat, ip_str):
            return False
        try:
            addr = ipaddress.IPv4Address(ip_str)
            return not self.is_private_ip(str(addr))
        except ipaddress.AddressValueError:
            return False

    def check_response_size(self, content_length):
        """Yanit boyut kontrolu."""
        if content_length > self._max_body_size:
            return False, f"Body {content_length} > max {self._max_body_size}"
        return True, "OK"

    def get_security_headers(self):
        """Baseline guvenlik basliklarini dondurur."""
        return dict(SECURITY_HEADERS)
    def sanitize_otlp_url(self, url):
        """OTLP endpoint URL sanitizasyonu."""
        if not url:
            return ""
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            return ""
        clean = f"{parsed.scheme}://{parsed.hostname or ''}"
        if parsed.port:
            clean += f":{parsed.port}"
        clean += parsed.path or "/"
        return clean

    def add_allowed_host(self, host):
        """Izin verilen host ekler."""
        self._allowed_hosts.add(host)

    def add_blocked_host(self, host):
        """Engellenen host ekler."""
        self._blocked_hosts.add(host)

    def get_stats(self):
        """Istatistikleri dondurur."""
        return {
            "total_requests": self._request_count,
            "blocked_requests": self._blocked_count,
            "allowed_hosts": len(self._allowed_hosts),
            "blocked_hosts": len(self._blocked_hosts),
        }
