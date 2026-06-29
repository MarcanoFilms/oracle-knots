# Oracle Knots Security Hardening Plan

**Phase 3.2: Security Hardening & Input Validation**  
**Target**: Zero critical vulnerabilities before public release  
**Approach**: Defense in depth with client + server validation

---

## 1. Input Validation Strategy

### 1.1 Client-Side Validation (JavaScript)

**Validation Framework**
```javascript
// gui/validation.js - New validation library
const validators = {
  walletName: (value) => {
    if (!value || value.length < 1 || value.length > 100) return false
    if (!/^[a-zA-Z0-9_-]+$/.test(value)) return false
    return true
  },
  
  bitcoinAddress: (value) => {
    // Validate P2PKH, P2SH, Bech32, Bech32m
    const patterns = {
      p2pkh: /^1[a-zA-Z0-9]{25,34}$/,
      p2sh: /^3[a-zA-Z0-9]{25,34}$/,
      bech32: /^bc1[a-z0-9]{39,59}$/i,
      bech32m: /^bc1[a-z0-9]{39,59}$/i,
    }
    return Object.values(patterns).some(p => p.test(value))
  },
  
  amount: (value) => {
    const num = parseFloat(value)
    if (isNaN(num) || num < 0.00000001 || num > 21000000) return false
    // Check for max 8 decimal places
    if (!/^\d+(\.\d{1,8})?$/.test(value)) return false
    return true
  },
  
  label: (value) => {
    if (!value || value.length > 100) return false
    // No control characters
    if (/[\x00-\x1f\x7f]/.test(value)) return false
    return true
  },
  
  feeRate: (value) => {
    const num = parseInt(value)
    if (isNaN(num) || num < 1 || num > 100000) return false
    return true
  }
}
```

**Form Field Validation**
```html
<!-- Example: Wallet name input -->
<div class="form-group">
  <label for="wallet-name">Wallet Name</label>
  <input 
    id="wallet-name" 
    type="text" 
    maxlength="100"
    pattern="^[a-zA-Z0-9_-]+$"
    required
    aria-describedby="wallet-name-error"
  >
  <div id="wallet-name-error" class="form-error hidden">
    Wallet name must be 1-100 characters, alphanumeric with _ and -
  </div>
</div>

<script>
document.getElementById('wallet-name').addEventListener('blur', (e) => {
  if (!validators.walletName(e.target.value)) {
    e.target.classList.add('error')
    document.getElementById('wallet-name-error').classList.remove('hidden')
  } else {
    e.target.classList.remove('error')
    document.getElementById('wallet-name-error').classList.add('hidden')
  }
})
</script>
```

**Validation Rules by Field**

| Field | Validation |  Max Length | Pattern |
|-------|-----------|------------|---------|
| Wallet Name | alphanumeric + underscore/dash | 100 | `^[a-zA-Z0-9_-]+$` |
| Bitcoin Address | Valid Bitcoin address | 62 | Bech32/P2PKH/P2SH |
| Amount (BTC) | Positive number, max 8 decimals | 20 | `^\d+(\.\d{1,8})?$` |
| Label | UTF-8, no control chars | 100 | `^[\x20-\x7e]*$` |
| Fee Rate (sat/vB) | Positive integer 1-100000 | 6 | `^\d{1,6}$` |
| PSBT Data | Base64/Hex string | 100KB | Hex or base64 |
| RPC Command | Command name + args | 10KB | Whitelist commands |

### 1.2 Server-Side Validation (Python/gui.py)

**Input Sanitization Framework**
```python
# gui.py - Add validation functions
import re
from typing import Any, Tuple

class InputValidator:
    """Validate and sanitize user inputs"""
    
    @staticmethod
    def validate_wallet_name(name: str) -> Tuple[bool, str]:
        """Validate wallet name (1-100 alphanumeric + -_)"""
        if not isinstance(name, str) or len(name) < 1 or len(name) > 100:
            return False, "Wallet name must be 1-100 characters"
        if not re.match(r'^[a-zA-Z0-9_-]+$', name):
            return False, "Wallet name contains invalid characters"
        return True, ""
    
    @staticmethod
    def validate_bitcoin_address(address: str) -> Tuple[bool, str]:
        """Validate Bitcoin address format"""
        if not isinstance(address, str) or len(address) > 62:
            return False, "Invalid address length"
        # Pattern for Bech32, P2PKH, P2SH
        patterns = [
            r'^bc1[a-z0-9]{39,59}$',  # Bech32
            r'^1[a-zA-Z0-9]{25,34}$',  # P2PKH
            r'^3[a-zA-Z0-9]{25,34}$',  # P2SH
        ]
        if not any(re.match(p, address, re.IGNORECASE) for p in patterns):
            return False, "Invalid Bitcoin address format"
        return True, ""
    
    @staticmethod
    def validate_amount(amount: str, max_amount: float = 21000000) -> Tuple[bool, str]:
        """Validate BTC amount"""
        try:
            num = float(amount)
            if num < 0.00000001 or num > max_amount:
                return False, f"Amount must be between 0.00000001 and {max_amount}"
            # Check decimal places
            if len(amount.split('.')[-1]) > 8:
                return False, "Maximum 8 decimal places allowed"
            return True, ""
        except (ValueError, AttributeError):
            return False, "Invalid amount format"
    
    @staticmethod
    def sanitize_label(label: str) -> Tuple[bool, str]:
        """Sanitize and validate label"""
        if not isinstance(label, str) or len(label) > 100:
            return False, "Label must be 1-100 characters"
        # Remove control characters
        if re.search(r'[\x00-\x1f\x7f]', label):
            return False, "Label contains invalid characters"
        return True, ""

# Usage in routes
@app.route('/api/wallet/create', method='POST')
def create_wallet():
    name = request.json.get('name', '')
    valid, error = InputValidator.validate_wallet_name(name)
    if not valid:
        return {'error': error}, 400
    # Proceed with wallet creation
```

---

## 2. XSS Prevention

### 2.1 Frontend XSS Prevention

**Current State**: Using `.textContent` for user data ✓ (mostly good)  
**Improvements Needed**: Complete audit and enforcement

```javascript
// DO: Use textContent for user-supplied data
const address = data.address  // User data
document.getElementById('address-display').textContent = address

// DON'T: Use innerHTML with user data
// document.getElementById('bad').innerHTML = `Address: ${address}`  // DANGEROUS!

// DO: Escape if HTML needed
const escaped = document.createElement('div')
escaped.textContent = userProvidedHTML
const safeHTML = escaped.innerHTML
```

**HTML Template Safety Checklist**
```html
<!-- ✓ SAFE: Using textContent -->
<span id="wallet-name-display"></span>
<script>
  document.getElementById('wallet-name-display').textContent = walletName
</script>

<!-- ✓ SAFE: Using text nodes -->
<p>Address: <code></code></p>
<script>
  document.querySelector('code').textContent = bitcoinAddress
</script>

<!-- ✗ UNSAFE: Using innerHTML with user data -->
<!-- <div innerHTML={userInput}></div> -->

<!-- ✓ SAFE: Using data attributes -->
<div data-txid="abc123"></div>
<script>
  const txid = element.dataset.txid  // Safe access
</script>
```

### 2.2 Backend XSS Prevention

**JSON Response Safety**
```python
import json

@app.route('/api/wallet/addresses')
def get_addresses():
    addresses = get_wallet_addresses()
    # Ensure JSON encoding handles special characters
    return json.dumps({
        'addresses': addresses
    }, ensure_ascii=True)  # Escape non-ASCII characters
```

**Response Headers**
```python
@app.route('/')
def index():
    response = make_response(render_template('index.html'))
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    return response
```

---

## 3. CSRF & CORS Protection

### 3.1 CSRF Protection

**Strategy**: Add CSRF tokens to state-changing requests

```python
import secrets

# Session CSRF token
csrf_tokens = {}

@app.route('/api/session/init')
def init_session():
    """Initialize session with CSRF token"""
    token = secrets.token_urlsafe(32)
    session_id = request.remote_addr  # Simple session key
    csrf_tokens[session_id] = token
    return {'csrf_token': token}

# Middleware: Validate CSRF on POST/PUT/DELETE
@app.before_request
def validate_csrf():
    if request.method in ['POST', 'PUT', 'DELETE']:
        token = request.headers.get('X-CSRF-Token')
        session_id = request.remote_addr
        if not token or token != csrf_tokens.get(session_id):
            return {'error': 'CSRF token invalid'}, 403

# Frontend: Include CSRF token in requests
const csrfToken = document.querySelector('[data-csrf-token]').content
fetch('/api/wallet/create', {
  method: 'POST',
  headers: {
    'X-CSRF-Token': csrfToken,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({name: 'my_wallet'})
})
```

### 3.2 CORS Policy

**Current**: GUI is localhost only (no CORS issues)  
**Documentation**: Add clear CORS policy

```python
# gui.py - Document CORS policy
"""
CORS Policy for Oracle Knots GUI:
- GUI runs locally via pywebview (localhost only)
- No remote API access allowed
- All requests originate from same origin
- CORS headers not needed (same-origin policy applies)

Security Implication:
- GUI cannot be accessed from remote machines
- No network exposure beyond local RPC
- HTTPS not needed (localhost traffic)
"""
```

---

## 4. Rate Limiting

### 4.1 Implementation

```python
import time
from collections import defaultdict

class RateLimiter:
    """Simple rate limiter for API endpoints"""
    
    def __init__(self, requests_per_second=10):
        self.requests_per_second = requests_per_second
        self.request_times = defaultdict(list)
    
    def is_allowed(self, client_id, max_requests=None):
        """Check if request is allowed"""
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

# Initialize limiters
general_limiter = RateLimiter(10)  # 10 req/sec general
sensitive_limiter = RateLimiter(1)  # 1 req/sec for sensitive ops

# Use in routes
@app.route('/api/wallet/send', method='POST')
def send_transaction():
    client = request.remote_addr
    if not sensitive_limiter.is_allowed(client):
        return {'error': 'Rate limit exceeded'}, 429
    # Process transaction
```

**Rate Limit Tiers**
```
General API (status, info):           10 req/sec
Wallet operations (create, load):      1 req/sec
Transaction operations (send):         1 req/sec
Configuration changes:                 1 req/sec
Policy changes:                        0.5 req/sec (1 per 2 seconds)
```

---

## 5. Secrets Management

### 5.1 Password/Passphrase Handling

**Requirements**
- ✅ Never log passwords or passphrases
- ✅ Never store in localStorage
- ✅ Never send in plain HTTP
- ✅ Require minimum 8 characters
- ✅ Hash on server side (use bitcoind's built-in)

```python
# gui.py - Password handling
@app.route('/api/wallet/encrypt', method='POST')
def encrypt_wallet():
    wallet_name = request.json.get('wallet_name')
    passphrase = request.json.get('passphrase')
    
    # Validate passphrase
    if not passphrase or len(passphrase) < 8:
        return {'error': 'Passphrase must be at least 8 characters'}, 400
    
    # IMPORTANT: Never log the passphrase
    log(f"Encrypting wallet {wallet_name}")  # OK
    # log(f"Passphrase: {passphrase}")  # NEVER DO THIS
    
    try:
        # Let bitcoind handle the encryption
        result = rpc_call('encryptwallet', [passphrase])
        return {'success': True}
    except Exception as e:
        return {'error': str(e)}, 500
    finally:
        # Clear passphrase from memory
        del passphrase
```

### 5.2 File Permissions

**Bitcoin Config/Wallet Permissions**
```bash
# bitcoin.conf should be readable only by user
chmod 600 ~/.bitcoin/bitcoin.conf

# Wallet files should be readable only by user
chmod 600 ~/.bitcoin/wallets/*.dat

# Verify in gui.py
import os
import stat

def check_file_permissions(filepath):
    """Verify file is readable only by owner"""
    st = os.stat(filepath)
    mode = st.st_mode
    
    # Check if group/others have read access
    if mode & (stat.S_IRGRP | stat.S_IROTH):
        return False, "File is readable by group or others!"
    
    return True, "Permissions OK"
```

---

## 6. Security Audit Checklist

### Pre-Release Security Audit

```
Input Validation:
[ ] All user inputs validated client-side
[ ] All user inputs validated server-side
[ ] Validation rules documented
[ ] Error messages don't leak sensitive info

XSS Prevention:
[ ] No innerHTML with user data
[ ] All user data rendered via textContent
[ ] JSON properly escaped
[ ] Response headers set (X-Content-Type-Options, etc)

CSRF Protection:
[ ] CSRF tokens implemented and validated
[ ] State-changing requests require tokens
[ ] Token rotation implemented

Rate Limiting:
[ ] Implemented for sensitive operations
[ ] Limits documented
[ ] Error handling for rate limit exceeded

Secrets Management:
[ ] No passwords logged
[ ] No passphrases stored in localStorage
[ ] File permissions checked (mode 600)
[ ] Passwords never sent in logs

Code Review:
[ ] All routes reviewed for security
[ ] All user inputs reviewed
[ ] All file operations reviewed
[ ] All RPC calls reviewed

Dependency Audit:
[ ] No known vulnerabilities in Bottle
[ ] No known vulnerabilities in pywebview
[ ] No known vulnerabilities in dependencies
[ ] Dependencies up-to-date
```

---

## 7. Security Testing

### 7.1 Security Test Cases

```python
# test/test_security.py
import pytest

class TestInputValidation:
    def test_wallet_name_too_long(self):
        """Reject wallet names > 100 characters"""
        long_name = 'a' * 101
        valid, error = InputValidator.validate_wallet_name(long_name)
        assert not valid
    
    def test_wallet_name_invalid_chars(self):
        """Reject wallet names with invalid characters"""
        invalid_names = ['wallet@name', 'wallet name', 'wallet#123']
        for name in invalid_names:
            valid, error = InputValidator.validate_wallet_name(name)
            assert not valid
    
    def test_address_validation_invalid(self):
        """Reject invalid Bitcoin addresses"""
        invalid = ['invalid', '1'*30, 'bc1invalid']
        for addr in invalid:
            valid, error = InputValidator.validate_bitcoin_address(addr)
            assert not valid

class TestXSSPrevention:
    def test_xss_not_reflected(self):
        """XSS payloads should not be reflected"""
        xss_payload = '<img src=x onerror=alert("XSS")>'
        # Test that payload is escaped, not executed
        assert '<img' not in render_template('test.html', user_input=xss_payload)
    
    def test_json_escaping(self):
        """JSON should properly escape special characters"""
        data = {'input': '<script>alert("xss")</script>'}
        json_output = json.dumps(data)
        assert '<script>' not in json_output

class TestRateLimiting:
    def test_rate_limit_enforced(self):
        """Rate limiting should block excessive requests"""
        limiter = RateLimiter(1)  # 1 req/sec
        # First request OK
        assert limiter.is_allowed('client1')
        # Second request blocked
        assert not limiter.is_allowed('client1')
```

### 7.2 Security Testing Tools

```bash
# Static code analysis (optional)
pylint gui.py --disable=all --enable=security

# Dependency scanning
pip audit

# OWASP ZAP (optional, for web app scanning)
# zaproxy -cmd -quickurl http://localhost:8080
```

---

## 8. Security Incident Response

### Vulnerability Reporting
```
SECURITY.md should include:
- How to report vulnerabilities (email)
- Response time expectations (48 hours)
- Process for fixing (private fix → release)
- Credit policy
```

### Fix Process
1. Receive vulnerability report
2. Assess severity
3. Develop fix in private branch
4. Create test case
5. Release security patch with detailed notes
6. Credit reporter (if requested)

---

## 9. Ongoing Security Maintenance

### Regular Checks
- **Weekly**: Review error logs for suspicious activity
- **Monthly**: Update dependencies and check for vulnerabilities
- **Quarterly**: Full security audit of changes
- **Annually**: Third-party security review (recommended)

---

## 10. Documentation

### Security Documentation
- Create `SECURITY.md` with vulnerability reporting
- Document all validation rules
- Document CSRF token implementation
- Document rate limiting strategy
- Create security incident response guide

---

**Timeline**: Weeks 10-11  
**Target Completion**: Zero critical vulnerabilities  
**Verification**: Pass all security test cases before release
