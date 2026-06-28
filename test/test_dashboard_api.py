#!/usr/bin/env python3
"""Unit tests for dashboard aggregation helpers in gui.py."""
import importlib.util
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

spec = importlib.util.spec_from_file_location("gui", REPO_ROOT / "gui.py")
gui = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gui)


def test_summarize_peers():
    peers = [
        {"addr": "abc.onion:8333", "inbound": True, "network": "onion"},
        {"addr": "1.2.3.4:8333", "inbound": False, "network": "ipv4"},
        {"addr": "peer.b32.i2p", "inbound": False, "network": "i2p"},
    ]
    s = gui._summarize_peers(peers)
    assert s["total"] == 3
    assert s["tor"] == 1
    assert s["i2p"] == 1
    assert s["clearnet"] == 1
    assert s["inbound"] == 1
    assert s["outbound"] == 2


def test_top_rejections():
    rejections = {
        "total": 15,
        "inscription": 10,
        "tokens-runes": 3,
        "dust-nonanchor": 2,
    }
    top, total = gui._top_rejections(rejections, 5)
    assert len(top) == 3
    assert top[0]["reason"] == "inscription"
    assert top[0]["count"] == 10
    assert total == 15


def test_rejection_stats():
    stats = gui._rejection_stats({"total": 25}, 75)
    assert stats["total"] == 25
    assert stats["evaluated"] == 100
    assert stats["rate_pct"] == 25.0
    assert stats["pass_rate_pct"] == 75.0


def test_parse_rdts_deployment():
    info = {
        "softforks": {
            "reduced_data": {
                "active": False,
                "bip9": {
                    "status": "started",
                    "statistics": {"period": 2016, "count": 1008, "threshold": 1109},
                },
            }
        }
    }
    rdts = gui._parse_rdts_deployment(info)
    assert rdts["status"] == "started"
    assert rdts["blocks_signaling"] == 1008
    assert rdts["signaling_pct"] == 50.0


def test_policy_preset_detection():
    parsed = {"profile": "maximalist", **gui.POLICY_PRESETS["maximalist"]}
    assert gui._policy_settings_from_parsed(parsed)["profile"] == "maximalist"
    parsed["custom_rules.datacarrier_size"] = 83
    assert gui._policy_settings_from_parsed(parsed)["profile"] == "custom"


def test_build_setsovereignpolicy_args_preset():
    args = gui._build_setsovereignpolicy_args({"profile": "maximalist"})
    assert args == ["setsovereignpolicy", "maximalist"]


if __name__ == "__main__":
    test_summarize_peers()
    test_top_rejections()
    test_rejection_stats()
    test_parse_rdts_deployment()
    test_policy_preset_detection()
    test_build_setsovereignpolicy_args_preset()
    print("Dashboard API unit tests passed")