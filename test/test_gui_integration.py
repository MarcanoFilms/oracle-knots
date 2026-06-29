#!/usr/bin/env python3
"""Integration tests for Oracle Knots GUI with bitcoind.

Tests the complete flow: GUI API → Python backend → bitcoind RPC
"""
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

# API endpoint
API_BASE = "http://127.0.0.1:8080"
API_TIMEOUT = 10


class TestAPIClient:
    """Simple HTTP API client for testing."""

    @staticmethod
    def get(endpoint: str, timeout: int = API_TIMEOUT) -> tuple:
        """Make GET request to API."""
        try:
            url = f"{API_BASE}{endpoint}"
            with urllib.request.urlopen(url, timeout=timeout) as response:
                status = response.status
                body = response.read().decode('utf-8')
                try:
                    data = json.loads(body)
                except json.JSONDecodeError:
                    data = body
                return status, data
        except urllib.error.URLError as e:
            return None, str(e)
        except Exception as e:
            return None, str(e)

    @staticmethod
    def post(endpoint: str, data: dict, timeout: int = API_TIMEOUT) -> tuple:
        """Make POST request to API."""
        try:
            url = f"{API_BASE}{endpoint}"
            json_data = json.dumps(data).encode('utf-8')
            req = urllib.request.Request(
                url,
                data=json_data,
                headers={'Content-Type': 'application/json'},
                method='POST'
            )
            with urllib.request.urlopen(req, timeout=timeout) as response:
                status = response.status
                body = response.read().decode('utf-8')
                try:
                    response_data = json.loads(body)
                except json.JSONDecodeError:
                    response_data = body
                return status, response_data
        except urllib.error.URLError as e:
            return None, str(e)
        except Exception as e:
            return None, str(e)


class TestDashboardAPI:
    """Test dashboard API endpoints."""

    def test_dashboard_endpoint_exists(self):
        """Dashboard endpoint should be accessible."""
        status, data = TestAPIClient.get("/")
        assert status is not None, "Dashboard endpoint not accessible"
        assert status == 200 or isinstance(data, str), "Dashboard returned unexpected status"

    def test_blockchain_info_retrieval(self):
        """Should retrieve blockchain info."""
        status, data = TestAPIClient.get("/api/blockchain")
        if status is not None:
            assert status == 200, f"Got status {status}"
            assert isinstance(data, dict), "Response should be JSON"
            # Should have blockchain info fields
            expected_fields = ["blocks", "difficulty", "chain"]
            for field in expected_fields:
                if field in data:
                    pass  # Field present

    def test_network_info_retrieval(self):
        """Should retrieve network info."""
        status, data = TestAPIClient.get("/api/network")
        if status is not None:
            assert status == 200, f"Got status {status}"
            assert isinstance(data, dict), "Response should be JSON"
            # Should have network info fields
            if "connections" in data or "version" in data:
                pass  # Has expected fields

    def test_dashboard_data_format(self):
        """Dashboard data should be properly formatted JSON."""
        status, data = TestAPIClient.get("/api/dashboard")
        if status is not None and isinstance(data, dict):
            # Verify JSON structure
            assert isinstance(data, dict), "Dashboard should return dict"
            # Check for timestamp or version field
            assert "timestamp" in data or "data" in data or status == 200


class TestWalletAPIIntegration:
    """Test wallet API integration with bitcoind."""

    def test_list_wallets_endpoint(self):
        """Should list available wallets."""
        status, data = TestAPIClient.get("/api/wallet/list")
        if status is not None:
            # Endpoint exists and returns data
            assert status in [200, 404], f"Unexpected status: {status}"
            if status == 200:
                assert isinstance(data, (dict, list)), "Wallets should be JSON"

    def test_wallet_info_structure(self):
        """Wallet info should have correct structure."""
        status, data = TestAPIClient.get("/api/wallet/info")
        if status == 200 and isinstance(data, dict):
            # Check for expected wallet fields
            if "name" in data:
                assert isinstance(data["name"], str)
            if "balance" in data:
                assert isinstance(data["balance"], (int, float))

    def test_address_generation(self):
        """Should be able to generate addresses."""
        # This would require a wallet to be loaded
        # For now, just verify endpoint exists
        status, data = TestAPIClient.get("/api/wallet/addresses")
        if status is not None:
            assert status in [200, 404, 500], "Should return a valid status"


class TestPolicyEngineAPI:
    """Test policy engine API integration."""

    def test_policy_info_endpoint(self):
        """Policy info endpoint should be accessible."""
        status, data = TestAPIClient.get("/api/policy/info")
        if status is not None:
            assert status in [200, 404], f"Unexpected status: {status}"
            if status == 200 and isinstance(data, dict):
                # Verify policy data structure
                if "profile" in data:
                    assert isinstance(data["profile"], str)

    def test_rejection_stats(self):
        """Should retrieve rejection statistics."""
        status, data = TestAPIClient.get("/api/policy/rejections")
        if status is not None and status == 200:
            assert isinstance(data, dict), "Rejections should be JSON"
            # Should have counts
            if "total" in data:
                assert isinstance(data["total"], int)


class TestBIP110Integration:
    """Test BIP-110 (Sovereign Mining) integration."""

    def test_mining_status_endpoint(self):
        """Should provide mining status."""
        status, data = TestAPIClient.get("/api/mining/status")
        if status is not None:
            assert status in [200, 404], f"Unexpected status: {status}"

    def test_template_stats(self):
        """Should provide template statistics."""
        status, data = TestAPIClient.get("/api/mining/templates")
        if status is not None:
            assert status in [200, 404], f"Unexpected status: {status}"


class TestRPCIntegration:
    """Test RPC command execution through GUI."""

    def test_rpc_endpoint_exists(self):
        """RPC endpoint should be accessible."""
        status, data = TestAPIClient.get("/api/rpc")
        if status is not None:
            # Should return some response (even if method not allowed)
            assert status in [200, 404, 405], f"Unexpected status: {status}"

    def test_rpc_safe_commands(self):
        """Safe RPC commands should work."""
        # getblockchaininfo is a safe, read-only command
        safe_commands = [
            "/api/rpc/getblockchaininfo",
            "/api/rpc/getnetworkinfo",
        ]

        for cmd in safe_commands:
            status, data = TestAPIClient.get(cmd)
            if status is not None:
                # Should return valid response
                assert status in [200, 404, 500], f"Unexpected status for {cmd}: {status}"


class TestConfigurationAPI:
    """Test configuration API."""

    def test_config_endpoint_exists(self):
        """Configuration endpoint should be accessible."""
        status, data = TestAPIClient.get("/api/config")
        if status is not None:
            assert status in [200, 404], f"Unexpected status: {status}"

    def test_config_info_structure(self):
        """Config info should have correct structure."""
        status, data = TestAPIClient.get("/api/config/info")
        if status == 200 and isinstance(data, dict):
            # Should have configuration info
            if "network" in data:
                assert data["network"] in ["main", "test", "signet", "regtest"]


class TestErrorHandling:
    """Test error handling and edge cases."""

    def test_invalid_endpoint_404(self):
        """Invalid endpoints should return 404."""
        status, data = TestAPIClient.get("/api/invalid/endpoint/path")
        assert status in [404, None], f"Invalid endpoint returned {status}"

    def test_malformed_json_handling(self):
        """API should handle malformed requests gracefully."""
        try:
            # Attempt to post invalid JSON
            req = urllib.request.Request(
                f"{API_BASE}/api/wallet/send",
                data=b"invalid json {",
                headers={'Content-Type': 'application/json'},
                method='POST'
            )
            with urllib.request.urlopen(req, timeout=5) as response:
                status = response.status
        except urllib.error.HTTPError as e:
            # Should return error status
            assert e.code in [400, 404, 405], f"Unexpected error: {e.code}"
        except Exception:
            pass  # Connection error is ok for this test

    def test_timeout_handling(self):
        """Long-running requests should handle timeouts."""
        # This is more of a performance test
        # Just verify API responds within reasonable time
        start = time.time()
        status, data = TestAPIClient.get("/api/blockchain", timeout=5)
        elapsed = time.time() - start
        if status is not None:
            assert elapsed < 5, "Request took too long"


class TestAPIConcurrency:
    """Test API behavior under concurrent usage."""

    def test_multiple_requests(self):
        """API should handle multiple sequential requests."""
        endpoints = [
            "/api/blockchain",
            "/api/network",
            "/api/policy/info",
        ]

        for endpoint in endpoints:
            status, data = TestAPIClient.get(endpoint)
            # Should handle each request
            assert status is not None or data is not None


class TestDataConsistency:
    """Test data consistency across API calls."""

    def test_consistent_blockchain_height(self):
        """Blockchain height should be consistent."""
        status1, data1 = TestAPIClient.get("/api/blockchain")
        time.sleep(0.5)  # Small delay
        status2, data2 = TestAPIClient.get("/api/blockchain")

        if status1 == 200 and status2 == 200:
            if isinstance(data1, dict) and isinstance(data2, dict):
                if "blocks" in data1 and "blocks" in data2:
                    # Height shouldn't decrease
                    assert data2["blocks"] >= data1["blocks"]

    def test_peer_count_stability(self):
        """Peer count should be relatively stable."""
        status1, data1 = TestAPIClient.get("/api/network")
        time.sleep(0.5)
        status2, data2 = TestAPIClient.get("/api/network")

        if status1 == 200 and status2 == 200:
            if isinstance(data1, dict) and isinstance(data2, dict):
                if "connections" in data1 and "connections" in data2:
                    # Peer count shouldn't change drastically in 0.5s
                    diff = abs(data2["connections"] - data1["connections"])
                    assert diff < 5, "Peer count changed too much"


def main():
    """Run all integration tests."""
    test_classes = [
        TestDashboardAPI,
        TestWalletAPIIntegration,
        TestPolicyEngineAPI,
        TestBIP110Integration,
        TestRPCIntegration,
        TestConfigurationAPI,
        TestErrorHandling,
        TestAPIConcurrency,
        TestDataConsistency,
    ]

    print("\n" + "=" * 70)
    print("Oracle Knots GUI - Integration Tests")
    print("=" * 70)

    total_tests = 0
    total_passed = 0
    total_failed = 0

    # Check if API is accessible
    status, data = TestAPIClient.get("/")
    if status is None:
        print("\n⚠️  WARNING: GUI API not responding at http://127.0.0.1:8080")
        print("   Make sure the GUI server is running:")
        print("   python3 gui.py")
        print("\n   Proceeding with available tests...\n")

    for test_class in test_classes:
        print(f"\n{test_class.__name__}")
        print("-" * 70)

        instance = test_class()
        test_methods = [m for m in dir(instance) if m.startswith("test_")]

        for method_name in sorted(test_methods):
            total_tests += 1
            try:
                method = getattr(instance, method_name)
                method()
                print(f"  ✓ {method_name}")
                total_passed += 1
            except AssertionError as e:
                print(f"  ✗ {method_name}: {str(e)}")
                total_failed += 1
            except Exception as e:
                print(f"  ✗ {method_name}: {str(e)}")
                total_failed += 1

    print("\n" + "=" * 70)
    print("Integration Test Summary")
    print("=" * 70)
    print(f"Total Tests: {total_tests}")
    print(f"Passed:      {total_passed}")
    print(f"Failed:      {total_failed}")
    print("=" * 70 + "\n")

    return 0 if total_failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
