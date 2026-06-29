#!/usr/bin/env python3
"""
Security Middleware for Oracle Knots GUI API

Integrates security.py with Bottle framework to:
- Apply security headers
- Validate inputs
- Enforce rate limiting
- Manage CSRF tokens
"""

from bottle import request, response
from security import (
    InputValidator,
    XSSPrevention,
    CSRFProtection,
    RateLimiter,
    SecretsManager,
    SecurityHeaders,
    InputSanitizer,
    csrf_protection,
    rate_limiter,
    sensitive_rate_limiter,
)
import json
import functools
from typing import Callable, Any


class SecurityMiddleware:
    """Security middleware for Bottle."""

    @staticmethod
    def apply_security_headers(app) -> None:
        """Apply security headers to all responses."""
        @app.hook('after_request')
        def apply_headers():
            SecurityHeaders.apply_to_response(response)

    @staticmethod
    def validate_json_content_type(app) -> None:
        """Ensure POST requests have proper Content-Type."""
        @app.hook('before_request')
        def check_content_type():
            if request.method in ['POST', 'PUT', 'PATCH']:
                if request.content_type and 'application/json' not in request.content_type:
                    if request.content_length and request.content_length > 0:
                        return {
                            'error': 'Invalid Content-Type. Use application/json',
                            'code': 400
                        }

    @staticmethod
    def setup_csrf_protection(app) -> None:
        """Setup CSRF token management."""
        @app.route('/api/csrf-token', method='GET')
        def get_csrf_token():
            """Get CSRF token for session."""
            client_id = request.remote_addr
            token = csrf_protection.generate_token(client_id)
            SecurityHeaders.apply_to_response(response)
            return {
                'csrf_token': token,
                'status': 'success'
            }

    @staticmethod
    def setup_rate_limiting(app) -> None:
        """Setup rate limiting on sensitive endpoints."""
        sensitive_endpoints = [
            '/api/wallet/send',
            '/api/wallet/create',
            '/api/config/save',
            '/api/policy/update',
        ]

        @app.hook('before_request')
        def check_rate_limit():
            client_id = request.remote_addr

            # Check if endpoint is sensitive
            if any(request.path.startswith(ep) for ep in sensitive_endpoints):
                if not sensitive_rate_limiter.is_allowed(client_id):
                    response.status = 429
                    SecurityHeaders.apply_to_response(response)
                    return {
                        'error': 'Rate limit exceeded',
                        'code': 429,
                        'message': 'Please wait before making another request'
                    }
            else:
                if not rate_limiter.is_allowed(client_id):
                    response.status = 429
                    SecurityHeaders.apply_to_response(response)
                    return {
                        'error': 'Rate limit exceeded',
                        'code': 429
                    }


class SecurityDecorators:
    """Decorators for securing routes."""

    @staticmethod
    def require_valid_json(func: Callable) -> Callable:
        """Decorator: Require valid JSON body."""
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                if request.method in ['POST', 'PUT', 'PATCH']:
                    if request.content_length and request.content_length > 0:
                        data = request.json
                        if not data:
                            return {'error': 'Invalid JSON body'}, 400
            except Exception as e:
                return {'error': 'Failed to parse JSON', 'detail': str(e)}, 400

            return func(*args, **kwargs)

        return wrapper

    @staticmethod
    def require_csrf_token(func: Callable) -> Callable:
        """Decorator: Require valid CSRF token for state-changing requests."""
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if request.method in ['POST', 'PUT', 'DELETE', 'PATCH']:
                token = request.headers.get('X-CSRF-Token')
                client_id = request.remote_addr

                if not token or not csrf_protection.validate_token(client_id, token):
                    response.status = 403
                    return {'error': 'Invalid CSRF token'}, 403

            return func(*args, **kwargs)

        return wrapper

    @staticmethod
    def validate_input(validation_rules: dict) -> Callable:
        """Decorator: Validate input parameters.

        Example:
            @validate_input({
                'wallet_name': InputValidator.validate_wallet_name,
                'address': InputValidator.validate_bitcoin_address,
            })
            def my_route():
                ...
        """
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                try:
                    data = request.json if request.json else {}
                except:
                    data = {}

                # Validate each field
                for field, validator in validation_rules.items():
                    if field in data:
                        value = data[field]
                        valid, error_msg = validator(value)

                        if not valid:
                            response.status = 400
                            return {
                                'error': f'Invalid {field}',
                                'message': error_msg,
                                'code': 400
                            }, 400

                return func(*args, **kwargs)

            return wrapper

        return decorator

    @staticmethod
    def sanitize_input(func: Callable) -> Callable:
        """Decorator: Sanitize all string inputs."""
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                data = request.json if request.json else {}
                if isinstance(data, dict):
                    sanitized = InputSanitizer.sanitize_dict(data)
                    # Store sanitized data in request context
                    request.sanitized_json = sanitized
            except:
                request.sanitized_json = {}

            return func(*args, **kwargs)

        return wrapper

    @staticmethod
    def detect_xss(func: Callable) -> Callable:
        """Decorator: Detect XSS payloads in input."""
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                data = request.json if request.json else {}
            except:
                data = {}

            # Check all string values for XSS
            for key, value in data.items():
                if isinstance(value, str):
                    if XSSPrevention.detect_xss_payload(value):
                        response.status = 400
                        return {
                            'error': 'Invalid input detected',
                            'message': f'Field {key} contains invalid characters',
                            'code': 400
                        }, 400

            return func(*args, **kwargs)

        return wrapper


class ResponseBuilder:
    """Build secure JSON responses."""

    @staticmethod
    def success(data: Any = None, message: str = "Success") -> str:
        """Build success response."""
        SecurityHeaders.apply_to_response(response)
        response.content_type = 'application/json'

        result = {
            'status': 'success',
            'message': message,
        }

        if data is not None:
            result['data'] = data

        return json.dumps(result, ensure_ascii=True)

    @staticmethod
    def error(message: str, code: int = 400, details: Any = None) -> str:
        """Build error response."""
        SecurityHeaders.apply_to_response(response)
        response.content_type = 'application/json'
        response.status = code

        result = {
            'status': 'error',
            'message': message,
            'code': code,
        }

        if details:
            result['details'] = details

        return json.dumps(result, ensure_ascii=True)

    @staticmethod
    def validation_error(field: str, message: str) -> str:
        """Build validation error response."""
        return ResponseBuilder.error(
            f"Validation error in {field}",
            code=400,
            details={'field': field, 'error': message}
        )


class LogManager:
    """Secure logging without sensitive data."""

    @staticmethod
    def log_safe(message: str, level: str = "INFO") -> None:
        """Log message with sensitive data redacted."""
        safe_message = SecretsManager.sanitize_log_message(message)
        timestamp = __import__('datetime').datetime.now().isoformat()
        print(f"[{timestamp}] [{level}] {safe_message}")

    @staticmethod
    def log_request(method: str, path: str, remote_addr: str) -> None:
        """Log API request safely."""
        LogManager.log_safe(
            f"API Request: {method} {path} from {remote_addr}",
            level="DEBUG"
        )

    @staticmethod
    def log_validation_error(field: str, reason: str) -> None:
        """Log validation errors."""
        LogManager.log_safe(
            f"Validation failed for {field}: {reason}",
            level="WARNING"
        )

    @staticmethod
    def log_security_event(event: str, details: str = "") -> None:
        """Log security events."""
        LogManager.log_safe(
            f"Security Event: {event} - {details}",
            level="WARNING"
        )


# Example usage in routes:
def example_secure_route(app):
    """Example of how to use security decorators."""

    @app.route('/api/wallet/send', method='POST')
    @SecurityDecorators.require_valid_json
    @SecurityDecorators.require_csrf_token
    @SecurityDecorators.validate_input({
        'address': InputValidator.validate_bitcoin_address,
        'amount': InputValidator.validate_amount,
        'fee_rate': InputValidator.validate_fee_rate,
    })
    @SecurityDecorators.detect_xss
    @SecurityDecorators.sanitize_input
    def send_bitcoin():
        """Send Bitcoin with full security validation."""
        data = request.sanitized_json

        # Now we can safely use the validated and sanitized data
        address = data.get('address')
        amount = data.get('amount')
        fee_rate = data.get('fee_rate')

        # Proceed with transaction
        return ResponseBuilder.success(
            data={'txid': 'abc123'},
            message='Transaction sent'
        )

    return app


if __name__ == "__main__":
    print("Security Middleware Tests")
    print("=" * 60)

    # Test response building
    print("\n1. Response Building:")
    success_resp = ResponseBuilder.success(
        data={'wallet': 'test'},
        message='Wallet created'
    )
    print(f"Success response: {success_resp[:50]}...")

    error_resp = ResponseBuilder.error(
        'Invalid input',
        code=400,
        details={'field': 'amount'}
    )
    print(f"Error response: {error_resp[:50]}...")

    # Test logging
    print("\n2. Secure Logging:")
    LogManager.log_safe("User login: password=secret123")
    LogManager.log_security_event("Rate limit exceeded", "client_ip=127.0.0.1")

    print("\n" + "=" * 60)
    print("Security middleware tests completed!")
