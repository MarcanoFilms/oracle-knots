#!/usr/bin/env python3
"""Tests for oracle_net, the outbound network policy.

The property under test: a price lookup must never quietly leave the machine in
the clear when the node itself is configured to go through a proxy.
"""

import builtins
import os
import sys
import unittest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

import oracle_net  # noqa: E402


class EnvGuard(unittest.TestCase):
    """Keeps the policy environment variables from leaking between tests."""

    ENV_KEYS = ("ORACLE_PRICE_FETCH", "ORACLE_OUTBOUND_PROXY")

    def setUp(self):
        self._saved = {k: os.environ.get(k) for k in self.ENV_KEYS}
        for k in self.ENV_KEYS:
            os.environ.pop(k, None)
        oracle_net.set_node_conf_provider(None)

    def tearDown(self):
        for k, v in self._saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        oracle_net.set_node_conf_provider(None)


class HostPortParsingTests(EnvGuard):
    def test_parses_ipv4_and_ipv6_and_rejects_junk(self):
        self.assertEqual(oracle_net._split_host_port("127.0.0.1:9050"), ("127.0.0.1", 9050))
        self.assertEqual(oracle_net._split_host_port("[::1]:9050"), ("::1", 9050))
        self.assertIsNone(oracle_net._split_host_port("9050"))
        self.assertIsNone(oracle_net._split_host_port("127.0.0.1:not-a-port"))
        self.assertIsNone(oracle_net._split_host_port(""))
        self.assertIsNone(oracle_net._split_host_port(None))


class ProxyResolutionTests(EnvGuard):
    def test_node_proxy_is_used(self):
        self.assertEqual(oracle_net.resolve_proxy({"proxy": "127.0.0.1:9050"}),
                         ("127.0.0.1", 9050))

    def test_onion_is_the_fallback(self):
        self.assertEqual(oracle_net.resolve_proxy({"onion": "127.0.0.1:9051"}),
                         ("127.0.0.1", 9051))

    def test_proxy_wins_over_onion(self):
        self.assertEqual(
            oracle_net.resolve_proxy({"proxy": "127.0.0.1:9050", "onion": "127.0.0.1:9051"}),
            ("127.0.0.1", 9050))

    def test_env_override_wins(self):
        os.environ["ORACLE_OUTBOUND_PROXY"] = "10.0.0.2:1080"
        self.assertEqual(oracle_net.resolve_proxy({"proxy": "127.0.0.1:9050"}),
                         ("10.0.0.2", 1080))

    def test_no_proxy_configured(self):
        self.assertIsNone(oracle_net.resolve_proxy({}))
        self.assertIsNone(oracle_net.resolve_proxy({"listen": "1"}))

    def test_conf_provider_is_consulted(self):
        oracle_net.set_node_conf_provider(lambda: {"proxy": "127.0.0.1:9150"})
        self.assertEqual(oracle_net.resolve_proxy(oracle_net.node_conf()),
                         ("127.0.0.1", 9150))

    def test_broken_conf_provider_does_not_crash(self):
        def boom():
            raise RuntimeError("no node")
        oracle_net.set_node_conf_provider(boom)
        self.assertEqual(oracle_net.node_conf(), {})


class ModeTests(EnvGuard):
    def test_default_is_auto(self):
        self.assertEqual(oracle_net.outbound_mode(), "auto")

    def test_recognised_modes(self):
        for value, expected in (("off", "off"), ("direct", "direct"), ("AUTO", "auto"),
                                ("nonsense", "auto"), ("", "auto")):
            os.environ["ORACLE_PRICE_FETCH"] = value
            self.assertEqual(oracle_net.outbound_mode(), expected, value)


class FailClosedTests(EnvGuard):
    def test_off_blocks_every_request(self):
        os.environ["ORACLE_PRICE_FETCH"] = "off"
        with self.assertRaises(oracle_net.OutboundBlocked):
            oracle_net.build_opener({})
        with self.assertRaises(oracle_net.OutboundBlocked):
            oracle_net.proxies_for_requests({})

    def test_proxy_without_pysocks_is_blocked_not_leaked(self):
        real_import = builtins.__import__

        def refuse_socks(name, *args, **kwargs):
            if name == "socks":
                raise ImportError("simulated: PySocks not installed")
            return real_import(name, *args, **kwargs)

        builtins.__import__ = refuse_socks
        try:
            with self.assertRaises(oracle_net.OutboundBlocked) as ctx:
                oracle_net.build_opener({"proxy": "127.0.0.1:9050"})
            self.assertIn("PySocks", str(ctx.exception))
            with self.assertRaises(oracle_net.OutboundBlocked):
                oracle_net.proxies_for_requests({"proxy": "127.0.0.1:9050"})
        finally:
            builtins.__import__ = real_import

    def test_direct_mode_is_an_explicit_opt_out(self):
        os.environ["ORACLE_PRICE_FETCH"] = "direct"
        _, proxy = oracle_net.build_opener({"proxy": "127.0.0.1:9050"})
        self.assertIsNone(proxy)
        self.assertEqual(oracle_net.proxies_for_requests({"proxy": "127.0.0.1:9050"}), {})

    def test_plaintext_url_through_a_proxy_is_refused(self):
        with self.assertRaises(oracle_net.OutboundBlocked):
            oracle_net.open_json("http://neoxa.example/ticker",
                                 conf={"proxy": "127.0.0.1:9050"})


class SocksWiringTests(EnvGuard):
    """The proxy details must reach PySocks, with DNS left to the proxy."""

    def test_connect_uses_socks5_with_remote_dns(self):
        recorded = {}

        class FakeSocket:
            def close(self):
                pass

        class FakeSocks:
            SOCKS5 = 2

            @staticmethod
            def create_connection(dest, **kwargs):
                recorded["dest"] = dest
                recorded.update(kwargs)
                return FakeSocket()

        class FakeContext:
            def wrap_socket(self, sock, server_hostname=None):
                recorded["server_hostname"] = server_hostname
                return sock

        conn = oracle_net._SocksHTTPSConnection(
            "neoxa.exchange", socks_proxy=("127.0.0.1", 9050), timeout=8)
        conn._context = FakeContext()
        sys.modules["socks"] = FakeSocks
        try:
            conn.connect()
        finally:
            sys.modules.pop("socks", None)

        self.assertEqual(recorded["dest"], ("neoxa.exchange", 443))
        self.assertEqual(recorded["proxy_addr"], "127.0.0.1")
        self.assertEqual(recorded["proxy_port"], 9050)
        self.assertEqual(recorded["proxy_type"], FakeSocks.SOCKS5)
        # Without remote DNS the hostname would still be resolved locally,
        # which leaks which sites this node looks up.
        self.assertTrue(recorded["proxy_rdns"])
        self.assertEqual(recorded["server_hostname"], "neoxa.exchange")

    def test_opener_uses_the_socks_handler_when_a_proxy_is_set(self):
        opener, proxy = oracle_net.build_opener({"proxy": "127.0.0.1:9050"})
        self.assertEqual(proxy, ("127.0.0.1", 9050))
        self.assertTrue(any(isinstance(h, oracle_net._SocksHTTPSHandler)
                            for h in opener.handlers))

    def test_requests_mapping_uses_socks5h(self):
        mapping = oracle_net.proxies_for_requests({"proxy": "127.0.0.1:9050"})
        # socks5h, not socks5: the "h" is what keeps DNS on the proxy.
        self.assertEqual(mapping["https"], "socks5h://127.0.0.1:9050")
        self.assertEqual(mapping["http"], "socks5h://127.0.0.1:9050")


if __name__ == "__main__":
    unittest.main()
