#!/usr/bin/env python3
"""Tests for the Control Center's local API guard and secret handling.

These cover the two properties that are easy to regress and expensive to get
wrong: the dashboard API must refuse requests that are not from the dashboard
itself, and wallet secrets must never reach a command line.
"""

import io
import json
import os
import stat
import sys
import tempfile
import unittest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

import bottle  # noqa: E402

import gui  # noqa: E402


def bind_json_request(payload, method="POST", path="/api/test"):
    """Point bottle's thread-local request at a synthetic JSON request."""
    body = json.dumps(payload).encode()
    bottle.request.bind({
        "REQUEST_METHOD": method,
        "PATH_INFO": path,
        "CONTENT_TYPE": "application/json",
        "CONTENT_LENGTH": str(len(body)),
        "wsgi.input": io.BytesIO(body),
    })


class RecordingCli:
    """Stands in for run_bitcoin_cli and records how it was called."""

    def __init__(self, result=(True, "ok")):
        self.calls = []
        self.result = result

    def __call__(self, args_list, datadir=None, network="mainnet", wallet_name=None,
                 timeout=5.0, flags=None, stdin_lines=None):
        self.calls.append({
            "args_list": list(args_list),
            "flags": list(flags or []),
            "stdin_lines": list(stdin_lines or []),
            "wallet_name": wallet_name,
        })
        return self.result


class HostHeaderTests(unittest.TestCase):
    def test_loopback_hosts_accepted(self):
        for host in ("127.0.0.1", "127.0.0.1:8080", "localhost", "localhost:8081",
                     "LOCALHOST:8080", "[::1]:8080", "::1"):
            self.assertTrue(gui.host_header_is_local(host), host)

    def test_missing_host_accepted(self):
        # HTTP/1.0 clients (curl --http1.0) send no Host header.
        self.assertTrue(gui.host_header_is_local(None))
        self.assertTrue(gui.host_header_is_local(""))

    def test_rebinding_hosts_rejected(self):
        # A page served from a hostname that resolves to 127.0.0.1 still sends
        # its own name here, which is what makes this check worth having.
        for host in ("attacker.example", "attacker.example:8080", "127.0.0.1.evil.com",
                     "192.168.1.10:8080", "oracle.local"):
            self.assertFalse(gui.host_header_is_local(host), host)


class OriginTests(unittest.TestCase):
    def test_own_origin_accepted(self):
        for origin in ("http://127.0.0.1:8080", "http://localhost:8080", "http://[::1]:8080"):
            self.assertTrue(gui.origin_is_local(origin, 8080), origin)

    def test_absent_origin_accepted(self):
        self.assertTrue(gui.origin_is_local(None, 8080))

    def test_foreign_origin_rejected(self):
        for origin in ("http://evil.example", "https://127.0.0.1:8080",
                       "http://127.0.0.1:9999", "http://127.0.0.1:8080.evil.com", "null"):
            self.assertFalse(gui.origin_is_local(origin, 8080), origin)


class TokenTests(unittest.TestCase):
    def test_real_token_accepted_others_rejected(self):
        self.assertTrue(gui.token_matches(gui.GUI_API_TOKEN))
        self.assertFalse(gui.token_matches(""))
        self.assertFalse(gui.token_matches(None))
        self.assertFalse(gui.token_matches("not-the-token"))
        self.assertFalse(gui.token_matches(gui.GUI_API_TOKEN + "x"))

    def test_token_is_not_guessable(self):
        self.assertGreaterEqual(len(gui.GUI_API_TOKEN), 32)
        self.assertNotEqual(gui.GUI_API_TOKEN, gui.GUI_TOKEN_PLACEHOLDER)

    def test_token_file_is_owner_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "nested", "gui.token")
            written = gui.write_gui_token_file("s3cret-token", path=path)
            self.assertEqual(written, path)
            with open(path) as f:
                self.assertEqual(f.read().strip(), "s3cret-token")
            self.assertEqual(stat.S_IMODE(os.stat(path).st_mode), 0o600)
            self.assertEqual(stat.S_IMODE(os.stat(os.path.dirname(path)).st_mode), 0o700)

    def test_static_paths_recognised(self):
        self.assertTrue(gui.request_is_static("/static/app.js"))
        self.assertTrue(gui.request_is_static("/static"))
        self.assertFalse(gui.request_is_static("/api/wallet/send"))
        self.assertFalse(gui.request_is_static("/"))


class PageTokenInjectionTests(unittest.TestCase):
    def test_placeholder_on_disk_and_token_in_response(self):
        with open(os.path.join(REPO_ROOT, "gui", "index.html")) as f:
            on_disk = f.read()
        self.assertIn(gui.GUI_TOKEN_PLACEHOLDER, on_disk)
        self.assertNotIn(gui.GUI_API_TOKEN, on_disk)

        bottle.request.bind({"REQUEST_METHOD": "GET", "PATH_INFO": "/"})
        bottle.response.bind()
        html = gui.index()
        self.assertIn(gui.GUI_API_TOKEN, html)
        self.assertNotIn(gui.GUI_TOKEN_PLACEHOLDER, html)


class SecretInputTests(unittest.TestCase):
    def test_newlines_rejected(self):
        # bitcoin-cli reads one stdin argument per line, so a newline inside a
        # secret would silently split it into two arguments.
        for bad in ("pass\nword", "pass\r\nword", "trailing\n"):
            with self.assertRaises(gui.SecretInputError):
                gui.check_stdin_secret(bad, "Passphrase")

    def test_ordinary_passphrase_passes_through(self):
        self.assertEqual(gui.check_stdin_secret("correct horse battery", "P"),
                         "correct horse battery")


class RunBitcoinCliTests(unittest.TestCase):
    def setUp(self):
        self.captured = {}

        def fake_run(cmd, capture_output=False, text=False, timeout=None, input=None):
            self.captured["cmd"] = list(cmd)
            self.captured["input"] = input

            class Result:
                returncode = 0
                stdout = "result"
                stderr = ""
            return Result()

        self._real_run = gui.subprocess.run
        gui.subprocess.run = fake_run

    def tearDown(self):
        gui.subprocess.run = self._real_run

    def test_flags_precede_the_method(self):
        # bitcoin-cli skips leading switches, so a flag placed after the method
        # would be sent to the node as an RPC argument instead.
        gui.run_bitcoin_cli(["walletpassphrase", "600"], datadir="/dd", network="mainnet",
                            wallet_name="w", flags=["-stdinwalletpassphrase"],
                            stdin_lines=["hunter2"])
        cmd = self.captured["cmd"]
        self.assertLess(cmd.index("-stdinwalletpassphrase"), cmd.index("walletpassphrase"))
        self.assertEqual(cmd[-2:], ["walletpassphrase", "600"])

    def test_stdin_lines_go_to_stdin_not_argv(self):
        gui.run_bitcoin_cli(["encryptwallet"], flags=["-stdin"], stdin_lines=["hunter2"])
        self.assertEqual(self.captured["input"], "hunter2\n")
        self.assertNotIn("hunter2", self.captured["cmd"])

    def test_no_stdin_when_not_requested(self):
        gui.run_bitcoin_cli(["getblockchaininfo"])
        self.assertIsNone(self.captured["input"])


class WalletSecretRoutingTests(unittest.TestCase):
    """The passphrase endpoints must keep secrets out of the process arguments."""

    def setUp(self):
        self.cli = RecordingCli()
        self._real_cli = gui.run_bitcoin_cli
        self._real_ctx = gui.get_node_context
        gui.run_bitcoin_cli = self.cli
        gui.get_node_context = lambda: (True, "/datadir", "mainnet")

    def tearDown(self):
        gui.run_bitcoin_cli = self._real_cli
        gui.get_node_context = self._real_ctx

    def assert_secret_not_in_argv(self, secret):
        for call in self.cli.calls:
            self.assertNotIn(secret, call["args_list"])
            self.assertNotIn(secret, call["flags"])
            self.assertIn(secret, call["stdin_lines"])

    def test_unlock_sends_passphrase_over_stdin(self):
        bind_json_request({"name": "w", "passphrase": "hunter2", "timeout": 600})
        self.assertEqual(gui.api_wallet_unlock(), {"success": True})
        call = self.cli.calls[0]
        self.assertEqual(call["args_list"], ["walletpassphrase", "600"])
        self.assertEqual(call["flags"], ["-stdinwalletpassphrase"])
        self.assert_secret_not_in_argv("hunter2")

    def test_encrypt_sends_passphrase_over_stdin(self):
        bind_json_request({"name": "w", "passphrase": "hunter2secret"})
        result = gui.api_wallet_encrypt()
        self.assertTrue(result["success"], result)
        call = self.cli.calls[0]
        self.assertEqual(call["args_list"], ["encryptwallet"])
        self.assertEqual(call["flags"], ["-stdin"])
        self.assert_secret_not_in_argv("hunter2secret")

    def test_change_passphrase_sends_both_over_stdin(self):
        bind_json_request({"name": "w", "old_passphrase": "oldsecret1",
                           "new_passphrase": "newsecret1"})
        self.assertEqual(gui.api_wallet_change_passphrase(), {"success": True})
        call = self.cli.calls[0]
        self.assertEqual(call["args_list"], ["walletpassphrasechange"])
        # -stdinwalletpassphrase takes the first line as the current passphrase,
        # -stdin appends the second as the new one.
        self.assertEqual(call["flags"], ["-stdinwalletpassphrase", "-stdin"])
        self.assertEqual(call["stdin_lines"], ["oldsecret1", "newsecret1"])

    def test_import_descriptors_keeps_key_material_off_argv(self):
        xprv = "wpkh(xprvSECRETKEYMATERIAL/84h/0h/0h/0/*)"
        bind_json_request({"name": "w", "descriptor": xprv})
        self.cli.result = (True, "[]")
        result = gui.api_wallet_import_descriptors()
        self.assertTrue(result["success"], result)
        call = self.cli.calls[0]
        self.assertEqual(call["args_list"], ["importdescriptors"])
        self.assertEqual(call["flags"], ["-stdin"])
        self.assertNotIn(xprv, " ".join(call["args_list"]))
        self.assertIn(xprv, call["stdin_lines"][0])

    def test_multiline_passphrase_is_refused(self):
        bind_json_request({"name": "w", "passphrase": "two\nlines", "timeout": 60})
        result = gui.api_wallet_unlock()
        self.assertFalse(result["success"])
        self.assertEqual(self.cli.calls, [])


if __name__ == "__main__":
    unittest.main()
