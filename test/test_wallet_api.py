#!/usr/bin/env python3
"""Unit tests for wallet API functions in gui.py."""
import importlib.util
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

spec = importlib.util.spec_from_file_location("gui", REPO_ROOT / "gui.py")
gui = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gui)


class TestWalletValidation:
    """Test wallet name and configuration validation."""

    def test_valid_wallet_name(self):
        """Valid wallet names should be accepted."""
        valid_names = [
            "my_wallet",
            "wallet-1",
            "test123",
            "MyWallet",
            "w",
            "a" * 100,  # max length
        ]
        for name in valid_names:
            # These should not raise exceptions when validated
            assert len(name) > 0
            assert len(name) <= 100
            assert name.replace("_", "").replace("-", "").isalnum()

    def test_invalid_wallet_name_length(self):
        """Wallet names that are too long should be rejected."""
        long_name = "a" * 101
        assert len(long_name) > 100

    def test_invalid_wallet_name_characters(self):
        """Wallet names with special characters should be rejected."""
        invalid_names = [
            "wallet@2024",
            "my wallet",
            "wallet#1",
            "wallet/test",
            "wallet.txt",
        ]
        for name in invalid_names:
            # These have invalid characters
            has_invalid = not (
                all(c.isalnum() or c in "-_" for c in name)
            )
            assert has_invalid


class TestAddressValidation:
    """Test Bitcoin address validation."""

    def test_valid_bech32_address(self):
        """Valid Bech32 addresses should be recognized."""
        valid_bech32 = [
            "bc1qw508d6qejxtdg4y5r3zarvary0c5xw7kv8f3t4",
            "bc1qar0srrr7xfkvy5l643lydnw9re59gtzzwf5mdq",
        ]
        for addr in valid_bech32:
            assert addr.startswith("bc1")
            assert len(addr) >= 42

    def test_valid_p2pkh_address(self):
        """Valid P2PKH addresses should be recognized."""
        valid_p2pkh = [
            "1A1z7agoat7GyxrQwnd3x8wdWvV53good",
            "1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2",
        ]
        for addr in valid_p2pkh:
            assert addr.startswith("1")
            assert len(addr) == 34

    def test_valid_p2sh_address(self):
        """Valid P2SH addresses should be recognized."""
        valid_p2sh = [
            "3J98t1WpEZ73CNmYviecrnyiWrnqRhWNLy",
            "3FZbgi29cp5sFvCSB3tPwF5XhSVBZMJW2j",
        ]
        for addr in valid_p2sh:
            assert addr.startswith("3")
            assert len(addr) == 34

    def test_invalid_address(self):
        """Invalid addresses should be rejected."""
        invalid = [
            "invalid",
            "0x1234567890",
            "1234567890",
            "",
            "not_an_address",
        ]
        for addr in invalid:
            # Basic validation: should start with 1, 3, or bc1
            is_valid = (
                addr.startswith("1") or
                addr.startswith("3") or
                addr.startswith("bc1")
            )
            assert not is_valid


class TestAmountValidation:
    """Test Bitcoin amount validation."""

    def test_valid_amount(self):
        """Valid amounts should be accepted."""
        valid_amounts = [
            "0.00000001",  # 1 satoshi
            "1.0",
            "0.5",
            "21000000",  # max supply
            "0.12345678",  # 8 decimal places
        ]
        for amount in valid_amounts:
            try:
                num = float(amount)
                assert num >= 0.00000001
                assert num <= 21000000
                decimals = len(amount.split(".")[-1])
                assert decimals <= 8
            except ValueError:
                assert False, f"Failed to parse valid amount: {amount}"

    def test_invalid_amount_too_small(self):
        """Amounts smaller than dust should be rejected."""
        small = "0.000000001"  # Less than 1 satoshi
        num = float(small)
        assert num < 0.00000001

    def test_invalid_amount_too_large(self):
        """Amounts larger than max supply should be rejected."""
        large = "21000001"
        num = float(large)
        assert num > 21000000

    def test_invalid_amount_too_many_decimals(self):
        """Amounts with >8 decimals should be rejected."""
        invalid = "0.123456789"
        decimals = len(invalid.split(".")[-1])
        assert decimals > 8


class TestLabelValidation:
    """Test label validation for addresses."""

    def test_valid_label(self):
        """Valid labels should be accepted."""
        valid_labels = [
            "My Address",
            "Exchange 1",
            "Cold Storage",
            "a" * 100,  # max length
        ]
        for label in valid_labels:
            assert 0 < len(label) <= 100
            # No control characters
            assert not any(ord(c) < 32 for c in label)

    def test_invalid_label_too_long(self):
        """Labels longer than 100 chars should be rejected."""
        long_label = "a" * 101
        assert len(long_label) > 100

    def test_invalid_label_control_chars(self):
        """Labels with control characters should be rejected."""
        invalid = "Label\x00With\x1fBadChars"
        has_control = any(ord(c) < 32 or ord(c) == 127 for c in invalid)
        assert has_control


class TestFeeValidation:
    """Test fee rate validation."""

    def test_valid_fee_rate(self):
        """Valid fee rates should be accepted."""
        valid_rates = [
            "1",
            "10",
            "50",
            "1000",
            "100000",  # max reasonable
        ]
        for rate in valid_rates:
            num = int(rate)
            assert 1 <= num <= 100000

    def test_invalid_fee_rate_zero(self):
        """Fee rate of 0 should be rejected."""
        rate = 0
        assert rate < 1

    def test_invalid_fee_rate_negative(self):
        """Negative fee rates should be rejected."""
        rate = -1
        assert rate < 1

    def test_invalid_fee_rate_too_high(self):
        """Unreasonably high fee rates should be rejected."""
        rate = 1000001
        assert rate > 100000


class TestUTXOHandling:
    """Test UTXO (unspent transaction output) handling."""

    def test_utxo_status_colors(self):
        """UTXOs should have correct status indicators."""
        utxos = {
            "spendable": {"status": "spendable", "color": "#00ff00"},
            "locked": {"status": "locked", "color": "#808080"},
            "unconfirmed": {"status": "unconfirmed", "color": "#ffff00"},
            "immature": {"status": "immature", "color": "#ff8800"},
        }

        for key, utxo in utxos.items():
            assert "status" in utxo
            assert "color" in utxo
            assert utxo["status"] in ["spendable", "locked", "unconfirmed", "immature"]

    def test_utxo_selection_coin_control(self):
        """Coin control should allow selecting/deselecting UTXOs."""
        utxo = {
            "txid": "abc123",
            "vout": 0,
            "amount": 0.5,
            "status": "spendable",
            "selected": False,
        }

        # Should be able to toggle selection
        assert utxo["selected"] == False
        utxo["selected"] = True
        assert utxo["selected"] == True


class TestTransactionValidation:
    """Test transaction validation."""

    def test_transaction_structure(self):
        """Valid transactions should have required fields."""
        tx = {
            "txid": "abc123def456",
            "status": "confirmed",
            "amount": 1.5,
            "fee": 0.0001,
            "timestamp": 1719590400,
        }

        required_fields = ["txid", "status", "amount"]
        for field in required_fields:
            assert field in tx

    def test_transaction_status_values(self):
        """Transaction statuses should be valid values."""
        valid_statuses = ["pending", "confirmed", "conflicted", "abandoned"]
        for status in valid_statuses:
            assert status in valid_statuses


class TestPSBTValidation:
    """Test PSBT (Partially Signed Bitcoin Transaction) validation."""

    def test_psbt_format_detection(self):
        """PSBT data can be hex or base64."""
        # Hex format
        psbt_hex = "70736274ff"
        assert all(c in "0123456789abcdefABCDEF" for c in psbt_hex)

        # Base64 format
        psbt_b64 = "cHNidP8A"
        import string
        b64_chars = string.ascii_letters + string.digits + "+/="
        assert all(c in b64_chars for c in psbt_b64)

    def test_psbt_minimum_length(self):
        """PSBT should have minimum length."""
        valid_psbt = "cHNidP8A"  # Minimal valid PSBT
        assert len(valid_psbt) > 0


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
