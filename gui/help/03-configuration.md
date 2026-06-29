# Configuration Guide

Customize Oracle Knots to your needs.

## Storage & Sync

### Network Selection
Choose which Bitcoin blockchain to connect to:
- **Mainnet**: Production Bitcoin (real money)
- **Testnet**: Testing network (free Bitcoin for testing)
- **Signet**: Signature testnet (modern testing)
- **Regtest**: Local testing only

### Pruning
Save disk space by enabling pruning:
- **Disabled**: Keep all blocks (~600GB+)
- **Automatic**: Let Oracle Knots decide size limit
- **Custom**: Set your own storage limit

⚠️ Warning: Pruning is incompatible with transaction indexing.

### Indexing
- **txindex**: Enable to search all historical transactions (requires ~200GB extra)
- **blockfilterindex**: Create compact filters for wallet rescanning

## P2P Network Settings

### Connections
- **Max Connections**: Limit peer connections (default: 125)
- **Max Inbound**: Limit incoming connections
- **Listen**: Allow other nodes to connect to you

### Privacy Networks
Choose which networks to use:
- **Clearnet**: Direct IPv4/IPv6 connections
- **Tor**: Route traffic through Tor for privacy
- **I2P**: Route through I2P network

### Recommended Setup
For maximum privacy:
1. Enable Tor
2. Set inbound connections
3. Use a VPN or Tor Browser

## Spam Filters (Policy)

Oracle Knots lets you filter what transactions your node accepts:

### Policy Profiles
- **Maximalist**: Zero tolerance for data spam
- **BIP-110 Strict**: Follow Bitcoin standard rules strictly
- **Monetary-Only**: Accept only money transactions
- **Custom**: Create your own rules

### What Gets Filtered
- Large data carriers (Ordinals, Runes)
- Non-monetary tokens
- Bloated outputs
- Uneconomical transactions

### Changing Policy
1. Go to **Configuration** → **Spam Filters**
2. Select a profile
3. Click **Apply Policy** on the Dashboard
4. Changes take effect immediately

## RPC & API

### Port Settings
- **RPC Port**: Default 8332 (mainnet), 18332 (testnet)
- **User/Password**: Set credentials for API access

### Accessing RPC
Use `bitcoin-cli` or other tools to interact with your node:
```
bitcoin-cli -rpcuser=YOUR_USER -rpcpass=YOUR_PASS getblockchaininfo
```

## System Optimization

### Memory (dbcache)
- Set based on your available RAM
- More cache = faster blockchain processing
- Default: 300MB

### Network
- **maxmempool**: Max unconfirmed transaction pool
- **dbcache**: Memory to use for database

## Backup & Recovery

Always backup your Bitcoin data:
1. Go to **Configuration** → **Storage**
2. Find your datadir path
3. Back up the entire directory to external storage
4. Store backup securely

## Common Settings

### Light Node (Low Resources)
```
prune=550          # Minimal disk
maxmempool=25      # Low memory
maxconnections=8   # Few peers
```

### Full Archival Node
```
txindex=1          # Index all transactions
blockfilterindex=1 # Enable filters
dbcache=2000       # High memory
```

### Private Node (Tor Only)
```
onlynet=tor        # Tor only
listen=1           # Accept connections
proxy=127.0.0.1:9050  # Tor proxy
