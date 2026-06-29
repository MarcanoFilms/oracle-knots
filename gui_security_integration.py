#!/usr/bin/env python3
"""
Security Integration Instructions for gui.py

This file shows exactly how to integrate the security modules into gui.py.
Apply these changes step-by-step to gui.py
"""

# ============================================================================
# STEP 1: Add imports at the top of gui.py (after existing imports)
# ============================================================================

"""
Add these lines after line 13 (after "from bottle import ..."):

# Security modules
try:
    from security import (
        InputValidator,
        XSSPrevention,
        csrf_protection,
        rate_limiter,
        sensitive_rate_limiter,
    )
    from security_middleware import (
        SecurityMiddleware,
        SecurityDecorators,
        ResponseBuilder,
        LogManager,
    )
    SECURITY_ENABLED = True
except ImportError:
    print("WARNING: Security modules not found. Running without security.")
    SECURITY_ENABLED = False
"""


# ============================================================================
# STEP 2: Setup middleware after bottle app is created
# ============================================================================

"""
Add this after the bottle app is initialized (around line 850-860):

# Setup security middleware
if SECURITY_ENABLED:
    SecurityMiddleware.apply_security_headers(app)
    SecurityMiddleware.validate_json_content_type(app)
    SecurityMiddleware.setup_csrf_protection(app)
    SecurityMiddleware.setup_rate_limiting(app)
    print("[SECURITY] Middleware configured")
"""


# ============================================================================
# STEP 3: Protect sensitive routes
# ============================================================================

"""
Apply decorators to routes that need protection. Examples:

BEFORE:
@app.route('/api/wallet/send', method='POST')
def send_bitcoin():
    try:
        data = request.json
        ...

AFTER:
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
    try:
        data = request.sanitized_json  # Use sanitized data
        ...
"""


# ============================================================================
# STEP 4: Routes to protect (list of sensitive endpoints)
# ============================================================================

SENSITIVE_ROUTES = [
    # Wallet operations
    '/api/wallet/create',
    '/api/wallet/load',
    '/api/wallet/send',
    '/api/wallet/send-advanced',
    '/api/wallet/lock-utxo',
    '/api/wallet/address',

    # Configuration
    '/api/config',  # POST method
    '/api/config/parsed',  # POST method

    # Policy
    '/api/policy/apply',
    '/api/rpc/set-policy',
    '/api/rpc/reload-policy',

    # Node control
    '/api/start',
    '/api/stop',
]


# ============================================================================
# STEP 5: Example integrations for common routes
# ============================================================================

"""
EXAMPLE 1: Wallet Send Route
=====================================

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
    try:
        # Data is now validated and sanitized
        data = request.sanitized_json

        address = data.get('address')
        amount = data.get('amount')
        fee_rate = data.get('fee_rate', '10')
        wallet_name = data.get('wallet_name', '')

        # Proceed with existing logic...
        # Use validated data safely

        return ResponseBuilder.success(
            data={'txid': 'abc123'},
            message='Transaction sent successfully'
        )
    except Exception as e:
        LogManager.log_security_event('Transaction send failed', str(e))
        return ResponseBuilder.error(
            'Failed to send transaction',
            code=500
        )


EXAMPLE 2: Wallet Create Route
=====================================

@app.route('/api/wallet/create', method='POST')
@SecurityDecorators.require_valid_json
@SecurityDecorators.require_csrf_token
@SecurityDecorators.validate_input({
    'wallet_name': InputValidator.validate_wallet_name,
})
@SecurityDecorators.detect_xss
@SecurityDecorators.sanitize_input
def create_wallet():
    try:
        data = request.sanitized_json
        wallet_name = data.get('wallet_name')

        # Create wallet using validated name
        # Existing logic...

        return ResponseBuilder.success(
            data={'wallet': wallet_name},
            message='Wallet created successfully'
        )
    except Exception as e:
        LogManager.log_security_event('Wallet creation failed', str(e))
        return ResponseBuilder.error(
            'Failed to create wallet',
            code=400
        )


EXAMPLE 3: Configuration Update Route
=====================================

@app.route('/api/config', method='POST')
@SecurityDecorators.require_valid_json
@SecurityDecorators.require_csrf_token
@SecurityDecorators.validate_input({
    'network': lambda v: (v in ['main', 'test', 'signet', 'regtest'],
                          'Invalid network') if isinstance(v, str) else (False, 'Must be string'),
})
@SecurityDecorators.detect_xss
@SecurityDecorators.sanitize_input
def update_config():
    try:
        data = request.sanitized_json

        # Update configuration with validated data
        # Existing logic...

        return ResponseBuilder.success(
            message='Configuration updated successfully'
        )
    except Exception as e:
        LogManager.log_security_event('Config update failed', str(e))
        return ResponseBuilder.error(
            'Failed to update configuration',
            code=400
        )


EXAMPLE 4: Read-Only Route (Dashboard - no CSRF needed)
=====================================

@app.route('/api/dashboard')
@SecurityDecorators.sanitize_input  # Still sanitize outputs
def get_dashboard():
    try:
        # No input validation needed for GET request
        # Return dashboard data

        return ResponseBuilder.success(
            data={
                'blocks': 800000,
                'peers': 8,
                'sync_progress': 100,
            }
        )
    except Exception as e:
        return ResponseBuilder.error(
            'Failed to fetch dashboard data',
            code=500
        )
"""


# ============================================================================
# STEP 6: CSRF Token for Frontend
# ============================================================================

"""
The frontend needs CSRF tokens. Add to index.html:

<script>
// On page load, get CSRF token
fetch('/api/csrf-token')
    .then(r => r.json())
    .then(data => {
        window.csrfToken = data.csrf_token;
        // Store in hidden input
        document.getElementById('csrf-token').value = data.csrf_token;
    });

// When sending POST/PUT/DELETE requests:
fetch('/api/wallet/send', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'X-CSRF-Token': window.csrfToken  // Add this header
    },
    body: JSON.stringify({
        address: '1A1z...',
        amount: '0.5',
        fee_rate: '50'
    })
})
.then(r => r.json())
.then(data => {
    if (data.status === 'success') {
        // Show success message
    } else {
        // Show error message
    }
});
</script>
"""


# ============================================================================
# STEP 7: Error Handling
# ============================================================================

"""
Security decorators will return errors for invalid input:

400 - Invalid JSON or validation failed
403 - CSRF token missing or invalid
429 - Rate limit exceeded
500 - Internal server error

Example error responses:

{
    "status": "error",
    "message": "Invalid amount",
    "code": 400,
    "details": {
        "field": "amount",
        "error": "Must be between 0.00000001 and 21000000"
    }
}

{
    "status": "error",
    "message": "Invalid CSRF token",
    "code": 403
}

{
    "status": "error",
    "message": "Rate limit exceeded",
    "code": 429,
    "message": "Please wait before making another request"
}
"""


# ============================================================================
# STEP 8: Logging
# ============================================================================

"""
Use LogManager for secure logging:

LogManager.log_safe("User action: send_bitcoin")
# Output: "[TIMESTAMP] [INFO] User action: send_bitcoin"

LogManager.log_request("POST", "/api/wallet/send", "127.0.0.1")
# Output: "[TIMESTAMP] [DEBUG] API Request: POST /api/wallet/send from 127.0.0.1"

LogManager.log_validation_error("address", "Invalid format")
# Output: "[TIMESTAMP] [WARNING] Validation failed for address: Invalid format"

LogManager.log_security_event("Rate limit exceeded", "client_ip=127.0.0.1")
# Output: "[TIMESTAMP] [WARNING] Security Event: Rate limit exceeded - client_ip=127.0.0.1"

# Note: Sensitive data is automatically redacted:
LogManager.log_safe("User login with password=secret123")
# Output: "[TIMESTAMP] [INFO] User login with [REDACTED]"
"""


# ============================================================================
# STEP 9: Testing Security
# ============================================================================

"""
Test invalid inputs:

# Test 1: Invalid address
curl -X POST http://127.0.0.1:8080/api/wallet/send \\
  -H "Content-Type: application/json" \\
  -H "X-CSRF-Token: valid_token" \\
  -d '{"address": "invalid", "amount": "1.0"}'
# Response: 400 - Invalid Bitcoin address format


# Test 2: Missing CSRF token
curl -X POST http://127.0.0.1:8080/api/wallet/send \\
  -H "Content-Type: application/json" \\
  -d '{"address": "1A1z...", "amount": "1.0"}'
# Response: 403 - Invalid CSRF token


# Test 3: Rate limit (make 11 requests in 1 second)
for i in {1..11}; do
  curl -X POST http://127.0.0.1:8080/api/wallet/send \\
    -H "Content-Type: application/json" \\
    -H "X-CSRF-Token: token" \\
    -d '{"address": "1A1z...", "amount": "1.0"}' &
done
# Response after 10: 429 - Rate limit exceeded


# Test 4: XSS payload detection
curl -X POST http://127.0.0.1:8080/api/wallet/create \\
  -H "Content-Type: application/json" \\
  -H "X-CSRF-Token: token" \\
  -d '{"wallet_name": "<script>alert(1)</script>"}'
# Response: 400 - Invalid input detected
"""


if __name__ == "__main__":
    print("Security Integration Guide")
    print("=" * 70)
    print("\nThis file provides step-by-step instructions for integrating")
    print("security modules (security.py, security_middleware.py) into gui.py.")
    print("\nSteps:")
    print("  1. Add imports to gui.py")
    print("  2. Setup middleware")
    print("  3. Apply decorators to sensitive routes")
    print("  4. Update frontend to send CSRF tokens")
    print("  5. Handle error responses")
    print("  6. Use LogManager for logging")
    print("  7. Test security with curl examples")
    print("\nSensitive routes to protect:")
    for route in SENSITIVE_ROUTES:
        print(f"  - {route}")
    print("\n" + "=" * 70)
