#!/usr/bin/env python3
"""End-to-end checks of the Control Center guard against a real HTTP server.

The unit tests in test_control_center.py pin the individual predicates; these
run the actual WSGI app so the guard is exercised the way a browser, another
local user, or a rebinding attack would reach it.
"""

import http.client
import os
import sys
import threading
import unittest
from wsgiref.simple_server import WSGIRequestHandler, make_server

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

import bottle  # noqa: E402

import gui  # noqa: E402


class QuietHandler(WSGIRequestHandler):
    def log_message(self, *args):
        pass


class ApiGuardLiveTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # gui.index() reads gui/index.html relative to the repository.
        cls._cwd = os.getcwd()
        os.chdir(REPO_ROOT)
        cls.server = make_server("127.0.0.1", 0, bottle.default_app(),
                                 handler_class=QuietHandler)
        cls.port = cls.server.server_address[1]
        gui._dashboard_port = cls.port
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.thread.join(timeout=5)
        cls.server.server_close()
        os.chdir(cls._cwd)

    def call(self, path, method="GET", host=None, headers=None, body=None):
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=10)
        sent = dict(headers or {})
        if host:
            sent["Host"] = host
        if body is not None:
            sent.setdefault("Content-Type", "application/json")
        try:
            conn.request(method, path, body=body, headers=sent)
            resp = conn.getresponse()
            return resp.status, resp.read()
        finally:
            conn.close()

    @property
    def token(self):
        return gui.GUI_API_TOKEN

    # --- the page itself ---

    def test_page_requires_the_token(self):
        status, _ = self.call("/")
        self.assertEqual(status, 403)

    def test_page_with_token_is_served_with_the_token_substituted(self):
        status, body = self.call(f"/?token={self.token}")
        self.assertEqual(status, 200)
        self.assertIn(self.token.encode(), body)
        self.assertNotIn(b"__ORACLE_API_TOKEN__", body)

    # --- the API ---

    def test_api_requires_the_token(self):
        status, _ = self.call("/api/status")
        self.assertEqual(status, 403)

    def test_api_accepts_the_token_header(self):
        status, _ = self.call("/api/status", headers={"X-Oracle-Token": self.token})
        self.assertEqual(status, 200)

    def test_api_rejects_a_wrong_token(self):
        status, _ = self.call("/api/status", headers={"X-Oracle-Token": "wrong"})
        self.assertEqual(status, 403)

    def test_price_routes_are_guarded_too(self):
        # These are registered by api/routes_bitcoin_price.py, not by gui.py.
        status, _ = self.call("/api/bitcoin/price")
        self.assertEqual(status, 403)

    # --- rebinding and cross-site ---

    def test_foreign_host_header_is_refused_even_with_a_valid_token(self):
        status, _ = self.call("/api/status", host="attacker.example",
                              headers={"X-Oracle-Token": self.token})
        self.assertEqual(status, 403)

    def test_explicit_loopback_host_is_accepted(self):
        status, _ = self.call("/api/status", host=f"127.0.0.1:{self.port}",
                              headers={"X-Oracle-Token": self.token})
        self.assertEqual(status, 200)

    def test_cross_site_origin_is_refused_on_post(self):
        status, _ = self.call("/api/wallet/send", method="POST",
                              body=b'{"name":"w","address":"a","amount":1}',
                              headers={"X-Oracle-Token": self.token,
                                       "Origin": "http://evil.example"})
        self.assertEqual(status, 403)

    def test_own_origin_passes_the_guard(self):
        # The node is offline in tests, so the route answers 200 with an error
        # body; what matters here is that the guard let it through.
        status, _ = self.call("/api/wallet/send", method="POST",
                              body=b'{"name":"w","address":"a","amount":1}',
                              headers={"X-Oracle-Token": self.token,
                                       "Origin": f"http://127.0.0.1:{self.port}"})
        self.assertEqual(status, 200)

    # --- static assets ---

    def test_static_assets_need_no_token(self):
        status, body = self.call("/static/api-client.js")
        self.assertEqual(status, 200)
        self.assertIn(b"X-Oracle-Token", body)

    def test_static_assets_still_reject_a_foreign_host(self):
        status, _ = self.call("/static/api-client.js", host="attacker.example")
        self.assertEqual(status, 403)


if __name__ == "__main__":
    unittest.main()
