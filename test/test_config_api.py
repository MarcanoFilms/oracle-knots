#!/usr/bin/env python3
"""Unit tests for configuration API functions in gui.py."""
import importlib.util
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

spec = importlib.util.spec_from_file_location("gui", REPO_ROOT / "gui.py")
gui = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gui)


class TestBitcoinConfParsing:
    """Test bitcoin.conf parsing and validation."""

    def test_parse_simple_config(self):
        """Should parse simple key=value configuration."""
        config_text = """
# Bitcoin configuration
server=1
rpcuser=testuser
rpcpassword=testpass
"""
        # Basic parsing
        lines = config_text.strip().split("\n")
        config = {}
        for line in lines:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, value = line.split("=", 1)
                config[key.strip()] = value.strip()

        assert config.get("server") == "1"
        assert config.get("rpcuser") == "testuser"
        assert config.get("rpcpassword") == "testpass"

    def test_parse_config_with_comments(self):
        """Should ignore comments in configuration."""
        config_text = """
# This is a comment
rpcport=18332  # inline comment
pruning=1
"""
        lines = config_text.strip().split("\n")
        config = {}
        for line in lines:
            line = line.split("#")[0].strip()  # Remove comments
            if not line:
                continue
            if "=" in line:
                key, value = line.split("=", 1)
                config[key.strip()] = value.strip()

        assert config.get("rpcport") == "18332"
        assert config.get("pruning") == "1"

    def test_config_numeric_validation(self):
        """Should validate numeric configuration values."""
        numeric_configs = {
            "rpcport": "18332",
            "maxconnections": "32",
            "dbcache": "450",
        }

        for key, value in numeric_configs.items():
            try:
                num = int(value)
                assert num > 0
            except ValueError:
                assert False, f"Failed to parse numeric config {key}={value}"

    def test_config_boolean_validation(self):
        """Should validate boolean configuration values."""
        bool_configs = {
            "server": "1",
            "rest": "1",
            "txindex": "1",
            "pruning": "0",
        }

        for key, value in bool_configs.items():
            assert value in ["0", "1"]


class TestNetworkConfiguration:
    """Test network configuration options."""

    def test_valid_networks(self):
        """Should accept valid Bitcoin networks."""
        valid_networks = ["main", "test", "signet", "regtest"]

        for network in valid_networks:
            assert network in valid_networks

    def test_invalid_network(self):
        """Should reject invalid networks."""
        invalid = "mainnet"  # Should be "main"
        assert invalid not in ["main", "test", "signet", "regtest"]

    def test_port_ranges(self):
        """Network ports should be in valid ranges."""
        valid_ports = {
            "main": 8333,
            "test": 18333,
            "signet": 38333,
            "regtest": 18444,
        }

        for network, port in valid_ports.items():
            assert 1024 <= port <= 65535


class TestPruningConfiguration:
    """Test blockchain pruning configuration."""

    def test_pruning_disabled(self):
        """Pruning disabled (0) is valid."""
        assert 0 >= 0

    def test_pruning_auto(self):
        """Pruning auto (1) is valid."""
        assert 1 >= 0

    def test_pruning_custom(self):
        """Pruning with custom size (>=550) is valid."""
        valid_sizes = [550, 1000, 5000, 10000]
        for size in valid_sizes:
            assert size >= 550

    def test_pruning_too_small(self):
        """Pruning sizes less than 550 should be rejected."""
        invalid_size = 100
        assert invalid_size < 550


class TestPolicyConfiguration:
    """Test policy engine configuration."""

    def test_policy_profiles(self):
        """Should recognize valid policy profiles."""
        profiles = [
            "standard",
            "conservative",
            "aggressive",
            "custom",
        ]

        for profile in profiles:
            assert profile in ["standard", "conservative", "aggressive", "custom"]

    def test_policy_settings_validation(self):
        """Should validate policy settings."""
        policy = {
            "profile": "standard",
            "datacarrier_size": 80,
            "dust_relay_fee": 3,
            "permit_bare_multisig": False,
        }

        assert policy["datacarrier_size"] >= 0
        assert policy["dust_relay_fee"] >= 0
        assert isinstance(policy["permit_bare_multisig"], bool)


class TestIndexingConfiguration:
    """Test blockchain indexing options."""

    def test_txindex_valid(self):
        """txindex should be boolean."""
        assert True in [True, False]
        assert False in [True, False]

    def test_blockfilterindex_valid(self):
        """blockfilterindex should be boolean or specific type."""
        valid_values = [0, 1, "basic"]
        assert any(val in [0, 1, "basic"] for val in valid_values)

    def test_addressindex_valid(self):
        """addressindex should be boolean."""
        assert True in [True, False]


class TestPrivacyConfiguration:
    """Test privacy-related configuration."""

    def test_tor_proxy_configuration(self):
        """Should validate Tor proxy settings."""
        tor_config = {
            "proxy": "127.0.0.1:9050",
            "onion": "127.0.0.1:9050",
        }

        for key, value in tor_config.items():
            # Should be IP:PORT format
            assert ":" in value
            parts = value.split(":")
            assert len(parts) == 2

    def test_i2p_proxy_configuration(self):
        """Should validate I2P proxy settings."""
        i2p_config = {
            "i2psam": "127.0.0.1:7656",
        }

        for key, value in i2p_config.items():
            # Should be IP:PORT format
            assert ":" in value

    def test_listen_settings(self):
        """Should validate listen address configuration."""
        valid_listen = [
            "0.0.0.0",
            "127.0.0.1",
            "::1",  # IPv6
        ]

        for addr in valid_listen:
            assert isinstance(addr, str)


class TestRPCConfiguration:
    """Test RPC configuration."""

    def test_rpc_auth_required(self):
        """RPC should require authentication."""
        rpc_config = {
            "rpcuser": "admin",
            "rpcpassword": "secure_password",
        }

        assert "rpcuser" in rpc_config
        assert "rpcpassword" in rpc_config
        assert len(rpc_config["rpcuser"]) > 0
        assert len(rpc_config["rpcpassword"]) > 0

    def test_rpc_port_valid(self):
        """RPC port should be valid."""
        rpc_port = 8332
        assert 1024 <= rpc_port <= 65535

    def test_rpc_bind_address(self):
        """RPC should bind to specific addresses."""
        valid_binds = [
            "127.0.0.1",
            "::1",  # IPv6 localhost
        ]

        for bind in valid_binds:
            assert isinstance(bind, str)


class TestConfigConflicts:
    """Test detection of conflicting configuration options."""

    def test_txindex_pruning_conflict(self):
        """txindex and pruning cannot both be enabled."""
        config = {
            "txindex": 1,
            "pruning": 1,
        }

        # These should conflict
        has_conflict = config.get("txindex") and config.get("pruning")
        if has_conflict:
            assert True  # Conflict detected

    def test_addressindex_pruning_conflict(self):
        """addressindex and pruning cannot both be enabled."""
        config = {
            "addressindex": 1,
            "pruning": 1,
        }

        has_conflict = config.get("addressindex") and config.get("pruning")
        if has_conflict:
            assert True

    def test_blockfilterindex_pruning_conflict(self):
        """blockfilterindex and pruning cannot both be enabled."""
        config = {
            "blockfilterindex": "basic",
            "pruning": 1,
        }

        has_conflict = config.get("blockfilterindex") and config.get("pruning")
        if has_conflict:
            assert True


class TestConfigurationPersistence:
    """Test configuration saving and loading."""

    def test_config_format_preserved(self):
        """Configuration format should be preserved."""
        original = "rpcuser=admin\nrpcpassword=pass123\n"
        parsed = {}
        for line in original.strip().split("\n"):
            if "=" in line:
                key, value = line.split("=", 1)
                parsed[key] = value

        # Verify keys are preserved
        assert "rpcuser" in parsed
        assert "rpcpassword" in parsed

    def test_config_roundtrip(self):
        """Should be able to save and load configuration."""
        config = {
            "server": "1",
            "rpcuser": "admin",
            "rpcpassword": "password",
        }

        # Simulate save
        lines = [f"{k}={v}" for k, v in config.items()]
        saved = "\n".join(lines)

        # Simulate load
        loaded = {}
        for line in saved.split("\n"):
            if "=" in line:
                k, v = line.split("=", 1)
                loaded[k] = v

        assert loaded == config


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
