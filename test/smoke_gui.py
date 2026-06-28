#!/usr/bin/env python3
"""Smoke test for Oracle Knots GUI API (no bitcoind required for static routes)."""
import importlib.util
import json
import sys
import threading
import time
import urllib.error
import urllib.request

REPO_ROOT = __import__("pathlib").Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

spec = importlib.util.spec_from_file_location("gui", REPO_ROOT / "gui.py")
gui = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gui)

PORT = 18765


def _start_server():
    from bottle import run
    run(host="127.0.0.1", port=PORT, quiet=True)


def get(path, as_json=True):
    with urllib.request.urlopen(f"http://127.0.0.1:{PORT}{path}", timeout=5) as r:
        body = r.read()
        if as_json:
            return r.status, json.loads(body)
        return r.status, body


def post(path, body):
    req = urllib.request.Request(
        f"http://127.0.0.1:{PORT}{path}",
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=5) as r:
        return r.status, json.loads(r.read())


def main():
    t = threading.Thread(target=_start_server, daemon=True)
    t.start()
    time.sleep(0.6)

    status, body = get("/", as_json=False)
    assert status == 200 and b"Oracle Knots" in body, "index.html failed"

    status, data = get("/api/status")
    assert status == 200 and "running" in data

    status, data = post("/api/cli", {"command": "stop"})
    assert status == 200 and not data.get("success"), "stop should be blocked"

    status, dash = get("/api/dashboard")
    assert status == 200
    assert "online" in dash
    assert "rejections" in dash
    assert "policy" in dash
    if not dash.get("online"):
        assert dash["rejections"]["deltas"]["today"] == 0

    status, pre = get("/api/preflight")
    assert status == 200 and "checks" in pre

    print("GUI smoke tests passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())