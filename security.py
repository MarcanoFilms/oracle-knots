#!/usr/bin/env python3
"""
Security & Input Validation Module for Oracle Knots GUI

Provides:
- Input validation (client-side + server-side)
- XSS prevention
- CSRF token management
- Rate limiting
- Secrets management
"""

import re
import json
import secrets
import time
from typing import Tuple, Optional, Dict, List, Any
from collections import defaultdict


class InputValidator:
    """Validate and sanitize user inputs."""

    # Patterns for validation
    WALLET_NAME_PATTERN = r'^[a-zA-Z0-9_-]+$'
    BITCOIN_ADDRESS_PATTERNS = [
        r'^bc1[a-z0-9]{39,59}$',  # Bech32
        r'^1[a-zA-Z0-9]{25,34}$',  # P2PKH
        r'^3[a-zA-Z0-9]{25,34}$',  # P2SH
    ]
    AMOUNT_PATTERN = r'^\d+(\.\d{1,8})?$'

    @staticmethod
    def validate_wallet_name(name: str) -> Tuple[bool, str]:
        """Validate wallet name (1-100 alphanumeric + -_)."""
        if not isinstance(name, str):
            return False, "Wallet name must be a string"

        if len(name) < 1 or len(name) > 100:
            return False, "Wallet name must be 1-100 characters"

        if not re.match(InputValidator.WALLET_NAME_PATTERN, name):
            return False, "Wallet name contains invalid characters"

        return True, ""

    @staticmethod
    def validate_bitcoin_address(address: str) -> Tuple[bool, str]:
        """Validate Bitcoin address format."""
        if not isinstance(address, str):
            return False, "Address must be a string"

        if len(address) > 62:
            return False, "Invalid address length"

        for pattern in InputValidator.BITCOIN_ADDRESS_PATTERNS:
            if re.match(pattern, address, re.IGNORECASE):
                return True, ""

        return False, "Invalid Bitcoin address format"

    @staticmethod
    def validate_amount(amount: str, max_amount: float = 21000000) -> Tuple[bool, str]:
        """Validate BTC amount."""
        if not isinstance(amount, str):
            return False, "Amount must be a string"

        try:
            num = float(amount)
        except ValueError:
            return False, "Invalid amount format"

        if num < 0.00000001:
            return False, "Amount too small (minimum 1 satoshi)"

        if num > max_amount:
            return False, f"Amount exceeds maximum ({max_amount} BTC)"

        # Check decimal places
        if '.' in amount:
            decimals = len(amount.split('.')[1])
            if decimals > 8:
                return False, "Maximum 8 decimal places allowed"

        return True, ""

    @staticmethod
    def validate_label(label: str) -> Tuple[bool, str]:
        """Validate address label."""
        if not isinstance(label, str):
            return False, "Label must be a string"

        if len(label) < 1 or len(label) > 100:
            return False, "Label must be 1-100 characters"

        # Check for control characters
        if any(ord(c) < 32 for c in label):
            return False, "Label contains invalid characters"

        return True, ""

    @staticmethod
    def validate_fee_rate(rate: str) -> Tuple[bool, str]:
        """Validate fee rate (sat/vB)."""
        if not isinstance(rate, str):
            return False, "Fee rate must be a string"

        try:
            num = int(rate)
        except ValueError:
            return False, "Fee rate must be an integer"

        if num < 1 or num > 100000:
            return False, "Fee rate must be between 1 and 100,000 sat/vB"

        return True, ""

    @staticmethod
    def validate_rpc_command(command: str) -> Tuple[bool, str]:
        """Validate RPC command against whitelist."""
        # Whitelist of safe commands
        SAFE_COMMANDS = {
            "getblockchaininfo",
            "getnetworkinfo",
            "getmempoolinfo",
            "getpeerinfo",
            "getwalletinfo",
            "listwallets",
            "getaddressinfo",
            "gettransaction",
            "getblock",
            "getblockhash",
            "createwallet",
            "loadwallet",
            "unloadwallet",
            "listreceivedbyaddress",
            "listunspent",
            "sendtoaddress",
            "signrawtransactionwithwallet",
            "walletpassphrase",
            "encryptwallet",
            "dumpwallet",
            "importwallet",
            "backupwallet",
        }

        if not isinstance(command, str):
            return False, "Command must be a string"

        cmd_name = command.split()[0].lower()

        if cmd_name not in SAFE_COMMANDS:
            return False, f"Command '{cmd_name}' not in whitelist"

        return True, ""

    @staticmethod
    def validate_json(data: str) -> Tuple[bool, str]:
        """Validate JSON format."""
        if not isinstance(data, str):
            return False, "Data must be a string"

        try:
            json.loads(data)
            return True, ""
        except json.JSONDecodeError as e:
            return False, f"Invalid JSON: {str(e)}"


class XSSPrevention:
    """XSS (Cross-Site Scripting) prevention utilities."""

    # Characters that need escaping
    ESCAPE_MAP = {
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#x27;',
        '&': '&amp;',
    }

    @staticmethod
    def escape_html(text: str) -> str:
        """Escape HTML special characters."""
        if not isinstance(text, str):
            return str(text)

        result = text
        for char, escaped in XSSPrevention.ESCAPE_MAP.items():
            result = result.replace(char, escaped)

        return result

    @staticmethod
    def detect_xss_payload(text: str) -> bool:
        """Detect common XSS payloads."""
        if not isinstance(text, str):
            return False

        dangerous_patterns = [
            r'<script',
            r'on\w+\s*=',  # event handlers (onclick, onerror, etc)
            r'javascript:',
            r'<iframe',
            r'<embed',
            r'<object',
        ]

        text_lower = text.lower()
        for pattern in dangerous_patterns:
            if re.search(pattern, text_lower):
                return True

        return False

    @staticmethod
    def sanitize_json_response(data: Any) -> str:
        """Safely encode JSON response."""
        return json.dumps(data, ensure_ascii=True)


class CSRFProtection:
    """CSRF (Cross-Site Request Forgery) token management."""

    def __init__(self):
        """Initialize CSRF token storage."""
        self.tokens = {}  # {session_id: token}

    def generate_token(self, session_id: str) -> str:
        """Generate a new CSRF token."""
        token = secrets.token_urlsafe(32)
        self.tokens[session_id] = token
        return token

    def validate_token(self, session_id: str, token: str) -> bool:
        """Validate CSRF token."""
        stored_token = self.tokens.get(session_id)
        if not stored_token:
            return False

        # Use constant-time comparison to prevent timing attacks
        return self._constant_time_compare(stored_token, token)

    @staticmethod
    def _constant_time_compare(a: str, b: str) -> bool:
        """Constant-time string comparison."""
        if len(a) != len(b):
            return False

        result = 0
        for x, y in zip(a, b):
            result |= ord(x) ^ ord(y)

        return result == 0


class RateLimiter:
    """Rate limiting for API endpoints."""

    def __init__(self, requests_per_second: int = 10):
        """Initialize rate limiter."""
        self.requests_per_second = requests_per_second
        self.request_times = defaultdict(list)

    def is_allowed(self, client_id: str, max_requests: Optional[int] = None) -> bool:
        """Check if request is allowed."""
        if max_requests is None:
            max_requests = self.requests_per_second

        now = time.time()
        window_start = now - 1  # 1 second window

        # Remove old requests outside window
        self.request_times[client_id] = [
            t for t in self.request_times[client_id]
            if t > window_start
        ]

        # Check limit
        if len(self.request_times[client_id]) >= max_requests:
            return False

        # Record request
        self.request_times[client_id].append(now)
        return True

    def get_remaining(self, client_id: str, max_requests: Optional[int] = None) -> int:
        """Get remaining requests in current window."""
        if max_requests is None:
            max_requests = self.requests_per_second

        now = time.time()
        window_start = now - 1

        count = len([t for t in self.request_times[client_id] if t > window_start])
        return max(0, max_requests - count)


class SecretsManager:
    """Manage sensitive data securely."""

    # Patterns to prevent logging
    SENSITIVE_PATTERNS = [
        r'password\s*[=:]\s*["\']?[^"\'\s]+',
        r'passphrase\s*[=:]\s*["\']?[^"\'\s]+',
        r'secret\s*[=:]\s*["\']?[^"\'\s]+',
        r'api[_-]?key\s*[=:]\s*["\']?[^"\'\s]+',
        r'token\s*[=:]\s*["\']?[^"\'\s]+',
    ]

    @staticmethod
    def sanitize_log_message(message: str) -> str:
        """Remove sensitive data from log messages."""
        if not isinstance(message, str):
            return str(message)

        result = message
        for pattern in SecretsManager.SENSITIVE_PATTERNS:
            result = re.sub(pattern, '[REDACTED]', result, flags=re.IGNORECASE)

        return result

    @staticmethod
    def check_password_strength(password: str) -> Tuple[bool, str]:
        """Check password meets minimum requirements."""
        if not isinstance(password, str):
            return False, "Password must be a string"

        if len(password) < 8:
            return False, "Password must be at least 8 characters"

        # Could add more requirements: uppercase, numbers, special chars
        # For now, just minimum length

        return True, ""


class SecurityHeaders:
    """Generate security headers for HTTP responses."""

    HEADERS = {
        'X-Content-Type-Options': 'nosniff',  # Prevent MIME sniffing
        'X-Frame-Options': 'SAMEORIGIN',      # Clickjacking protection
        'X-XSS-Protection': '1; mode=block',  # XSS protection
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',  # HSTS
        'Content-Security-Policy': "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'",
    }

    @staticmethod
    def apply_to_response(response_obj) -> None:
        """Apply security headers to Bottle response."""
        for header, value in SecurityHeaders.HEADERS.items():
            response_obj.add_header(header, value)


class InputSanitizer:
    """Sanitize user inputs comprehensively."""

    @staticmethod
    def sanitize_string(value: str, max_length: int = 1000) -> str:
        """Sanitize string input."""
        if not isinstance(value, str):
            return ""

        # Trim to max length
        value = value[:max_length]

        # Remove null bytes
        value = value.replace('\x00', '')

        # Normalize whitespace
        value = ' '.join(value.split())

        return value

    @staticmethod
    def sanitize_dict(data: dict, max_depth: int = 10) -> dict:
        """Recursively sanitize dictionary."""
        if not isinstance(data, dict):
            return {}

        if max_depth <= 0:
            return {}

        result = {}
        for key, value in data.items():
            # Sanitize key
            if not isinstance(key, str):
                continue

            key = InputSanitizer.sanitize_string(key, 100)

            # Sanitize value
            if isinstance(value, str):
                result[key] = InputSanitizer.sanitize_string(value)
            elif isinstance(value, dict):
                result[key] = InputSanitizer.sanitize_dict(value, max_depth - 1)
            elif isinstance(value, (int, float, bool)):
                result[key] = value
            elif isinstance(value, list):
                result[key] = [
                    v for v in value
                    if isinstance(v, (str, int, float, bool))
                ]

        return result


# Global instances
csrf_protection = CSRFProtection()
rate_limiter = RateLimiter()
general_rate_limiter = RateLimiter(10)      # 10 req/sec
sensitive_rate_limiter = RateLimiter(1)     # 1 req/sec


if __name__ == "__main__":
    # Test the security module
    print("Security Module Tests")
    print("=" * 60)

    # Test input validation
    print("\n1. Input Validation:")
    valid, msg = InputValidator.validate_wallet_name("my_wallet")
    print(f"   Valid wallet name: {valid} - {msg}")

    valid, msg = InputValidator.validate_bitcoin_address("1A1z7agoat7GyxrQwnd3x8wdWvV53good")
    print(f"   Valid address: {valid} - {msg}")

    valid, msg = InputValidator.validate_amount("1.5")
    print(f"   Valid amount: {valid} - {msg}")

    # Test XSS detection
    print("\n2. XSS Prevention:")
    has_xss = XSSPrevention.detect_xss_payload('<script>alert("xss")</script>')
    print(f"   Detected XSS: {has_xss}")

    escaped = XSSPrevention.escape_html('<div>')
    print(f"   Escaped HTML: {escaped}")

    # Test CSRF tokens
    print("\n3. CSRF Protection:")
    token = csrf_protection.generate_token("session123")
    print(f"   Generated token: {token[:20]}...")
    valid = csrf_protection.validate_token("session123", token)
    print(f"   Token valid: {valid}")

    # Test rate limiting
    print("\n4. Rate Limiting:")
    allowed = rate_limiter.is_allowed("client1")
    print(f"   Request allowed: {allowed}")

    # Test secrets sanitization
    print("\n5. Secrets Management:")
    log_msg = "User authenticated with password=secret123"
    sanitized = SecretsManager.sanitize_log_message(log_msg)
    print(f"   Original: {log_msg}")
    print(f"   Sanitized: {sanitized}")

    print("\n" + "=" * 60)
    print("All security module tests completed!")
