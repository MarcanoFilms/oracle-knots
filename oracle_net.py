#!/usr/bin/env python3
"""Outbound network policy for the Oracle Knots Control Center.

The node is meant to run behind Tor: the README's recommended bitcoin.conf sets
`proxy=127.0.0.1:9050`. A price lookup that went out in the clear would undo
that, telling a third party which IP address runs this node. So every outbound
request the Control Center makes goes through this module, which:

  * sends the request through the node's own SOCKS5 proxy when one is configured,
    letting the proxy resolve the hostname so the name never leaks to a local
    resolver either;
  * fails closed. If a proxy is configured but unusable (PySocks missing, proxy
    down), the fetch is refused instead of quietly falling back to a direct
    connection.

Operator overrides, via environment variables:

  ORACLE_OUTBOUND_PROXY=host:port   use this SOCKS5 proxy instead of the node's
  ORACLE_PRICE_FETCH=off            make no outbound requests at all
  ORACLE_PRICE_FETCH=direct         allow direct connections even behind a proxy
"""

import http.client
import json
import os
import urllib.error
import urllib.request

__all__ = [
    "OutboundBlocked",
    "resolve_proxy",
    "outbound_mode",
    "build_opener",
    "open_json",
    "proxies_for_requests",
    "set_node_conf_provider",
    "node_conf",
]

USER_AGENT = "OracleKnots/2.0"


class OutboundBlocked(Exception):
    """Raised instead of making a request that would leak the operator's IP."""


_node_conf_provider = None


def set_node_conf_provider(provider):
    """Register a callable returning the running node's parsed bitcoin.conf.

    gui.py registers one that knows the live datadir; without it this module
    falls back to the default datadir, so the proxy setting is still honoured.
    """
    global _node_conf_provider
    _node_conf_provider = provider


def _read_default_conf():
    path = os.path.join(os.path.expanduser("~"), ".bitcoin", "bitcoin.conf")
    conf = {}
    try:
        with open(path, "r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, value = line.partition("=")
                conf.setdefault(key.strip(), value.strip())
    except OSError:
        return {}
    return conf


def node_conf():
    """The node's configuration, from the registered provider or the default datadir."""
    if _node_conf_provider is not None:
        try:
            return _node_conf_provider() or {}
        except Exception:
            return {}
    return _read_default_conf()


def outbound_mode():
    """'off', 'direct' or 'auto' (the default: proxy when the node uses one)."""
    mode = (os.environ.get("ORACLE_PRICE_FETCH") or "auto").strip().lower()
    return mode if mode in ("off", "direct", "auto") else "auto"


def _split_host_port(value):
    value = (value or "").strip()
    if not value:
        return None
    if value.startswith("["):  # [::1]:9050
        host, _, port = value.partition("]")
        host = host.lstrip("[")
        port = port.lstrip(":")
    else:
        host, _, port = value.rpartition(":")
        if not host:  # no colon at all
            return None
    try:
        return (host, int(port))
    except ValueError:
        return None


def resolve_proxy(node_conf=None):
    """The SOCKS5 proxy to use, as (host, port), or None for a direct connection.

    Precedence: ORACLE_OUTBOUND_PROXY, then the node's -proxy, then -onion.
    node_conf is a parsed bitcoin.conf mapping.
    """
    override = _split_host_port(os.environ.get("ORACLE_OUTBOUND_PROXY"))
    if override:
        return override
    conf = node_conf or {}
    for key in ("proxy", "onion"):
        found = _split_host_port(conf.get(key))
        if found:
            return found
    return None


class _SocksHTTPSConnection(http.client.HTTPSConnection):
    """HTTPS over a SOCKS5 proxy, with remote DNS resolution."""

    def __init__(self, host, socks_proxy, **kwargs):
        self._socks_proxy = socks_proxy
        super().__init__(host, **kwargs)

    def connect(self):
        import socks  # imported here so a missing PySocks is a clear failure

        proxy_host, proxy_port = self._socks_proxy
        self.sock = socks.create_connection(
            (self.host, self.port),
            timeout=self.timeout,
            proxy_type=socks.SOCKS5,
            proxy_addr=proxy_host,
            proxy_port=proxy_port,
            # Let the proxy resolve the name; resolving it here would leak the
            # domain to the local DNS resolver.
            proxy_rdns=True,
        )
        if self._tunnel_host:
            self._tunnel()
        server_hostname = self._tunnel_host or self.host
        self.sock = self._context.wrap_socket(self.sock, server_hostname=server_hostname)


class _SocksHTTPSHandler(urllib.request.HTTPSHandler):
    def __init__(self, socks_proxy, context=None):
        super().__init__(context=context)
        self._socks_proxy = socks_proxy

    def _new_connection(self, host, **kwargs):
        return _SocksHTTPSConnection(host, socks_proxy=self._socks_proxy, **kwargs)

    def https_open(self, req):
        return self.do_open(self._new_connection, req, context=self._context)


def build_opener(conf=None):
    """Return (opener, proxy) honouring the outbound policy.

    Raises OutboundBlocked when a request must not be made.
    """
    mode = outbound_mode()
    if mode == "off":
        raise OutboundBlocked(
            "Outbound price lookups are disabled (ORACLE_PRICE_FETCH=off)."
        )

    proxy = resolve_proxy(conf if conf is not None else node_conf())
    if proxy is None or mode == "direct":
        # No proxy configured, or the operator accepted direct connections.
        return urllib.request.build_opener(urllib.request.HTTPSHandler()), None

    try:
        import socks  # noqa: F401
    except ImportError:
        raise OutboundBlocked(
            f"The node routes traffic through {proxy[0]}:{proxy[1]}, but PySocks is "
            "not installed, so this request would bypass the proxy and expose your "
            "IP address. Install PySocks (it is in requirements.txt), or set "
            "ORACLE_PRICE_FETCH=direct to accept direct connections."
        )
    return urllib.request.build_opener(_SocksHTTPSHandler(proxy)), proxy


def open_json(url, timeout=8.0, conf=None, headers=None):
    """Fetch and decode JSON under the outbound policy.

    Raises OutboundBlocked if the request is not allowed, or the underlying
    urllib/socket error if it simply failed.
    """
    opener, proxy = build_opener(conf if conf is not None else node_conf())
    if proxy is not None and not url.lower().startswith("https://"):
        raise OutboundBlocked(
            "Refusing to send a plaintext http:// request through the proxy; "
            "use an https:// endpoint."
        )
    request_headers = {"Accept": "application/json", "User-Agent": USER_AGENT}
    if headers:
        request_headers.update(headers)
    req = urllib.request.Request(url, headers=request_headers)
    with opener.open(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8", "replace"))


def proxies_for_requests(conf=None):
    """Proxy mapping for the `requests` library under the same policy.

    Returns {} for a direct connection, or a socks5h:// mapping so the proxy
    resolves the hostname. Raises OutboundBlocked when the request must not
    be made at all.
    """
    mode = outbound_mode()
    if mode == "off":
        raise OutboundBlocked(
            "Outbound price lookups are disabled (ORACLE_PRICE_FETCH=off)."
        )
    proxy = resolve_proxy(conf if conf is not None else node_conf())
    if proxy is None or mode == "direct":
        return {}
    try:
        import socks  # noqa: F401  (requests needs PySocks for socks5h://)
    except ImportError:
        raise OutboundBlocked(
            f"The node routes traffic through {proxy[0]}:{proxy[1]}, but PySocks is "
            "not installed, so this request would bypass the proxy and expose your "
            "IP address. Install PySocks (it is in requirements.txt), or set "
            "ORACLE_PRICE_FETCH=direct to accept direct connections."
        )
    # socks5h keeps DNS resolution on the proxy side.
    url = f"socks5h://{proxy[0]}:{proxy[1]}"
    return {"http": url, "https": url}
