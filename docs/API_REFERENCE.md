# Oracle Knots API Reference

**Version**: 1.0  
**Base URL**: `http://127.0.0.1:8080`  
**Authentication**: CSRF tokens required for state-changing requests

---

## Overview

The Oracle Knots API is a JSON-RPC style interface for interacting with the node. All endpoints are local-only (localhost) for security.

### Authentication

- **CSRF Tokens**: Required for POST/PUT/DELETE requests
- **Session-based**: Token tied to client IP
- **Rate Limiting**: 10 req/sec general, 1 req/sec for sensitive operations

### Error Responses

All errors return JSON with this format:
```json
{
  "status": "error",
  "message": "Human-readable error message",
  "code": 400,
  "details": {...}
}
```

---

## Dashboard & Status

### GET /api/blockchain

Get blockchain information.

**Response**:
```json
{
  "blocks": 800000,
  "difficulty": 84895105882.79,
  "chain": "main",
  "verify_progress": 0.9999,
  "size_on_disk": 590000000000
}
```

### GET /api/network

Get network status.

**Response**:
```json
{
  "connections": 8,
  "subversion": "/Bitcoin Knots:29.3.0/",
  "version": 230000,
  "timeoffset": 0,
  "relay_fee": 0.00001000
}
```

### GET /api/dashboard

Get complete dashboard data (combines blockchain + network + peers).

**Response**:
```json
{
  "blockchain": {...},
  "network": {...},
  "peers": {...},
  "timestamp": 1719590400
}
```

### POST /api/start

Start the node (if not running).

**Request**:
```json
{
  "datadir": "~/.bitcoin"
}
```

**Response**:
```json
{
  "status": "success",
  "message": "Node started"
}
```

### POST /api/stop

Stop the node gracefully.

**Response**:
```json
{
  "status": "success",
  "message": "Node stopping"
}
```

---

## Wallet Operations

### GET /api/wallet/status

Get wallet status (loaded/unloaded).

**Response**:
```json
{
  "loaded": true,
  "name": "my_wallet"
}
```

### POST /api/wallet/create

Create a new wallet.

**Request**:
```json
{
  "wallet_name": "my_wallet",
  "passphrase": "optional_password"
}
```

**Response**:
```json
{
  "status": "success",
  "wallet": "my_wallet",
  "mnemonic": "word1 word2 ... word12"
}
```

### POST /api/wallet/load

Load an existing wallet.

**Request**:
```json
{
  "wallet_name": "my_wallet"
}
```

**Response**:
```json
{
  "status": "success",
  "message": "Wallet loaded"
}
```

### GET /api/wallet/info

Get loaded wallet information.

**Response**:
```json
{
  "name": "my_wallet",
  "balance": 0.5,
  "unconfirmed": 0.1,
  "transactions": 25,
  "addresses": 5
}
```

### POST /api/wallet/address

Generate a new address.

**Request**:
```json
{
  "label": "My Address"
}
```

**Response**:
```json
{
  "address": "bc1qw508d6qejxtdg4y5r3zarvaRy0c5xw7kv8f3t4",
  "label": "My Address"
}
```

### POST /api/wallet/send

Send Bitcoin.

**Request**:
```json
{
  "address": "bc1qw508d6qejxtdg4y5r3zarvary0c5xw7kv8f3t4",
  "amount": "0.5",
  "fee_rate": "25"
}
```

**Response**:
```json
{
  "status": "success",
  "txid": "abc123...",
  "fee": 0.00001
}
```

### POST /api/wallet/send-advanced

Send Bitcoin with coin control.

**Request**:
```json
{
  "address": "bc1q...",
  "amount": "0.5",
  "fee_rate": "25",
  "utxos": ["txid:vout", "txid:vout"],
  "change_address": "bc1q..."
}
```

**Response**:
```json
{
  "status": "success",
  "txid": "abc123...",
  "fee": 0.00001
}
```

### GET /api/wallet/utxos

Get unspent transaction outputs (UTXOs).

**Response**:
```json
{
  "utxos": [
    {
      "txid": "abc123...",
      "vout": 0,
      "amount": 0.5,
      "status": "spendable",
      "confirmations": 100
    }
  ]
}
```

### POST /api/wallet/lock-utxo

Lock a UTXO to prevent spending.

**Request**:
```json
{
  "txid": "abc123...",
  "vout": 0
}
```

**Response**:
```json
{
  "status": "success",
  "message": "UTXO locked"
}
```

### GET /api/wallet/transactions

Get transaction history.

**Response**:
```json
{
  "transactions": [
    {
      "txid": "abc123...",
      "amount": 0.5,
      "status": "confirmed",
      "date": "2026-06-28T12:00:00Z",
      "confirmations": 100
    }
  ]
}
```

---

## Configuration

### GET /api/config

Get current configuration.

**Response**:
```json
{
  "chain": "main",
  "prune_mode": "auto",
  "txindex": true,
  "addressindex": false,
  "tor_proxy": null,
  "policy_profile": "standard"
}
```

### POST /api/config

Update configuration.

**Request**:
```json
{
  "chain": "main",
  "prune_mode": "auto",
  "txindex": true,
  "policy_profile": "conservative"
}
```

**Response**:
```json
{
  "status": "success",
  "message": "Configuration updated"
}
```

### GET /api/config/parsed

Get parsed bitcoin.conf file.

**Response**:
```json
{
  "config": {
    "server": "1",
    "rest": "1",
    "rpcuser": "oracle",
    "txindex": "1"
  }
}
```

### POST /api/config/parsed

Update config via parsed format.

**Request**:
```json
{
  "config": {
    "txindex": "1",
    "addressindex": "0"
  }
}
```

**Response**:
```json
{
  "status": "success",
  "message": "Configuration saved"
}
```

---

## Policy Engine

### GET /api/policy/info

Get policy engine status and current profile.

**Response**:
```json
{
  "profile": "standard",
  "rules": {
    "datacarrier_size": 80,
    "dust_relay_fee": 3,
    "permit_bare_multisig": false
  }
}
```

### POST /api/policy/apply

Apply a policy profile.

**Request**:
```json
{
  "profile": "conservative"
}
```

**Response**:
```json
{
  "status": "success",
  "message": "Policy applied"
}
```

### GET /api/policy/rejections

Get transaction rejection statistics.

**Response**:
```json
{
  "total": 1500,
  "by_reason": {
    "policy_filter": 800,
    "size": 500,
    "fee": 200
  }
}
```

---

## Mining (BIP-110)

### GET /api/mining/status

Get sovereign mining status.

**Response**:
```json
{
  "mining_enabled": true,
  "current_template": "template_001",
  "lock_in_progress": 75,
  "shares_submitted": 1250
}
```

### GET /api/mining/templates

Get mining templates.

**Response**:
```json
{
  "templates": [
    {
      "id": "template_001",
      "size": 4096,
      "txs": 2500,
      "value": 6.5
    }
  ]
}
```

---

## RPC Passthrough

### GET /api/rpc/<method>

Execute read-only RPC command.

**Example**: `/api/rpc/getblockchaininfo`

**Response**: JSON from bitcoind

### POST /api/rpc/<method>

Execute read-write RPC command (requires CSRF token).

**Request**:
```json
{
  "params": ["param1", "param2"]
}
```

**Response**: JSON from bitcoind

### Whitelisted Commands

Safe commands that can be executed:
- `getblockchaininfo`
- `getnetworkinfo`
- `getmempoolinfo`
- `getpeerinfo`
- `getwalletinfo`
- `listwallets`
- `createwallet`
- `loadwallet`
- `unloadwallet`
- `listreceivedbyaddress`
- `listunspent`
- `sendtoaddress`

---

## Peers & Networking

### GET /api/peers

Get connected peers.

**Response**:
```json
{
  "peers": [
    {
      "id": 123,
      "address": "192.168.1.1:8333",
      "user_agent": "/Bitcoin Core:23.0/",
      "direction": "inbound",
      "height": 800000,
      "ping": 0.025
    }
  ]
}
```

### GET /api/mempool

Get mempool statistics.

**Response**:
```json
{
  "size": 1500,
  "bytes": 456000,
  "usage": 456000,
  "total_fee": 0.005
}
```

---

## CSRF Protection

### GET /api/csrf-token

Get CSRF token for session.

**Response**:
```json
{
  "csrf_token": "abc123xyz..."
}
```

**Usage**:
1. Call `/api/csrf-token` to get token
2. Include token in `X-CSRF-Token` header for state-changing requests

---

## Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 400 | Bad request (validation failed) |
| 403 | CSRF token missing or invalid |
| 404 | Resource not found |
| 429 | Rate limit exceeded |
| 500 | Internal server error |

---

## Rate Limiting

- **General endpoints**: 10 requests/second per client IP
- **Sensitive endpoints**: 1 request/second per client IP
  - `/api/wallet/send`
  - `/api/wallet/create`
  - `/api/config` (POST)
  - `/api/policy/apply`

Exceeding limits returns 429 status.

---

## Security Headers

All responses include:
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: SAMEORIGIN`
- `X-XSS-Protection: 1; mode=block`

---

## Example: Complete Workflow

```bash
# 1. Get CSRF token
curl http://127.0.0.1:8080/api/csrf-token
# Response: { "csrf_token": "..." }

# 2. Create wallet (POST requires CSRF token)
curl -X POST http://127.0.0.1:8080/api/wallet/create \
  -H "Content-Type: application/json" \
  -H "X-CSRF-Token: <token>" \
  -d '{"wallet_name": "my_wallet"}'

# 3. Get wallet info
curl http://127.0.0.1:8080/api/wallet/info

# 4. Send Bitcoin
curl -X POST http://127.0.0.1:8080/api/wallet/send \
  -H "Content-Type: application/json" \
  -H "X-CSRF-Token: <token>" \
  -d '{
    "address": "bc1q...",
    "amount": "0.5",
    "fee_rate": "25"
  }'
```

---

**Last Updated**: June 28, 2026
