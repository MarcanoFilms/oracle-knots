# Oracle Knots User Guide

**Version**: 1.0  
**Last Updated**: June 28, 2026  
**For**: Non-technical Bitcoin users who want to run a sovereign node

---

## Table of Contents

1. [Introduction](#introduction)
2. [System Requirements](#system-requirements)
3. [Installation](#installation)
4. [Getting Started](#getting-started)
5. [Dashboard Overview](#dashboard-overview)
6. [Wallet Operations](#wallet-operations)
7. [Configuration](#configuration)
8. [Policy Engine](#policy-engine)
9. [Monitoring & Troubleshooting](#monitoring--troubleshooting)
10. [Security Best Practices](#security-best-practices)
11. [FAQ](#faq)

---

## Introduction

### What is Oracle Knots?

Oracle Knots is a modern, user-friendly Bitcoin node client built on Bitcoin Knots. It brings the power and sovereignty of running your own full node to non-technical users through an intuitive graphical interface.

**Why Run a Node?**
- **Sovereignty**: You verify the blockchain yourself, not trusting third parties
- **Privacy**: Your transactions aren't exposed to node providers
- **Security**: You control your own Bitcoin keys and addresses
- **Support Bitcoin**: Help strengthen the network by validating transactions
- **Advanced Features**: Access to mining, policy filtering, and advanced settings

### Key Features

✅ **User-Friendly Interface** - No command line required  
✅ **Modern Dashboard** - Real-time blockchain status  
✅ **Wallet Management** - Create, load, and manage wallets  
✅ **Policy Engine** - Filter mempool according to custom rules (BIP-110)  
✅ **Sovereign Mining** - Run your own mining operation  
✅ **Responsive Design** - Works on desktop, tablet, and mobile  
✅ **Secure** - Military-grade encryption and validation  

---

## System Requirements

### Minimum Requirements
- **CPU**: Dual-core processor (2 GHz+)
- **RAM**: 4 GB (8 GB recommended)
- **Storage**: 600 GB SSD (1 TB+ recommended for future growth)
- **Internet**: 2 Mbps connection (10 Mbps+ for better sync)
- **OS**: Linux, macOS, or Windows

### Recommended Specifications
- **CPU**: Quad-core processor (3 GHz+)
- **RAM**: 8 GB or more
- **Storage**: 1 TB+ NVMe SSD
- **Internet**: 10 Mbps+ with unlimited data
- **OS**: Linux (Ubuntu 20.04+, Debian 11+, or Arch Linux)

### Network Ports
- **8333**: P2P network communication (default)
- **8332**: RPC (local only, localhost)
- **8080**: GUI web interface (localhost)

---

## Installation

### For Linux (Ubuntu/Debian)

1. **Download Oracle Knots**
```bash
git clone https://github.com/MarcanoFilms/oracle-knots.git
cd oracle-knots
```

2. **Build from Source**
```bash
./autogen.sh
./configure
make -j$(nproc)
```

3. **Start the Application**
```bash
python3 gui.py
```

4. **Access the GUI**
Open your browser and navigate to `http://127.0.0.1:8080`

### For macOS

1. **Install Homebrew** (if not already installed)
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

2. **Clone and Build**
```bash
git clone https://github.com/MarcanoFilms/oracle-knots.git
cd oracle-knots
brew install autoconf automake libtool
./autogen.sh
./configure
make -j$(sysctl -n hw.ncpu)
```

3. **Start Oracle Knots**
```bash
python3 gui.py
```

### For Windows

1. Download the Windows binary from GitHub releases
2. Extract to a folder
3. Run `oracle-knots.exe`
4. The GUI will open automatically in your browser

### Verification

After starting, you should see:
- ✓ GUI server running on port 8080
- ✓ bitcoind starting in the background
- ✓ Browser opens to `http://127.0.0.1:8080`
- ✓ Dashboard shows "Syncing..." (this is normal)

---

## Getting Started

### First Time Setup

1. **Start the Node**
   - When you first run Oracle Knots, it will start the Bitcoin network node
   - This may take 5-10 minutes on first launch
   - The node will begin downloading and verifying the blockchain

2. **Choose Your Network**
   - **Mainnet** (default): Real Bitcoin network - use this for production
   - **Testnet**: Practice network with fake Bitcoin
   - **Signet**: Another test network run by developers
   - **Regtest**: Local testing, generates blocks instantly

3. **Configure Storage**
   - Decide on pruning mode:
     - **Full Node** (~600 GB): Stores entire blockchain history
     - **Pruned Node** (~550 MB): Stores only recent blocks
   - Choose a location with sufficient free space

4. **Wait for Sync**
   - Initial sync can take 2-24 hours depending on your internet
   - CPU, RAM, and storage speed affect sync time
   - You can use your node while syncing

### Understanding the Dashboard

The dashboard shows real-time information about your node:

**Status Box**
- Node status (running/syncing/error)
- Blockchain height (total blocks downloaded)
- Peer count (connected nodes)
- Sync progress percentage

**Network Stats**
- Current difficulty
- Network hashrate
- Memory usage

**Mining Info** (if enabled)
- Mining status
- Template info
- Hash rate (if mining)

---

## Wallet Operations

### Creating a Wallet

1. Click **Wallet Manager** tab
2. Click **Create Wallet**
3. Enter a wallet name (e.g., "My Bitcoin Wallet")
4. Click **Create**
5. **IMPORTANT**: Write down your recovery phrase in a safe location

### Receiving Bitcoin

1. Go to **Wallet Manager** → **Receive**
2. Click **Generate Address** to create a new receiving address
3. Copy the address or scan the QR code
4. Share this address with whoever is sending you Bitcoin
5. You can optionally add a label (e.g., "Payment from Alice")

### Sending Bitcoin

**Simple Mode** (recommended for most users)
1. Go to **Wallet Manager** → **Send**
2. Enter recipient address
3. Enter amount (in BTC or satoshis)
4. Fee rate is automatically calculated
5. Review transaction details
6. Click **Send**

**Coin Control Mode** (for advanced users)
1. Select which UTXOs (coins) to spend
2. Manually choose change address
3. Set custom fee rate
4. More control but requires Bitcoin knowledge

### Understanding Fees

Fees are paid to Bitcoin miners to include your transaction in a block.

**Fee Rate**: Measured in satoshis per virtual byte (sat/vB)
- **Low** (1-5 sat/vB): Slower, cheaper - 10+ blocks
- **Standard** (5-25 sat/vB): Normal - 2-10 blocks
- **Fast** (25-50 sat/vB): Quick - 1-2 blocks
- **Very Fast** (50+ sat/vB): Instant - next block

Oracle Knots automatically calculates appropriate fees based on network conditions.

### Transaction History

1. Go to **Wallet Manager** → **Transactions**
2. View all received and sent transactions
3. Sort by date or amount
4. Filter by status (confirmed/pending)
5. Click transaction for details

### Wallet Security

**Backup Your Wallet**
1. Write down your recovery phrase in a safe location
2. Store backups in multiple locations (safe, safe deposit box, etc.)
3. Never share your recovery phrase with anyone

**Encrypt Your Wallet**
1. Go to **Wallet Manager** → **Settings**
2. Click **Encrypt Wallet**
3. Enter a strong password (≥8 characters)
4. Confirm password
5. Your wallet is now encrypted

**Lock/Unlock**
- After encryption, your wallet is locked by default
- You must unlock it with your password to send transactions
- Locking helps protect your funds if someone gains access to your computer

---

## Configuration

### Storage Settings

**Network Selection**
- Choose which Bitcoin network your node connects to
- Changing networks requires resyncing the blockchain

**Pruning Mode**
- **Off** (Full Node): Stores complete blockchain history
- **Auto**: Automatically keep last 350 MB of blocks
- **Custom**: Specify exact storage size in GB

**Indexing**
- **txindex**: Index all transactions (needed for wallet lookups)
- **addressindex**: Index by address (needed for address history)
- **blockfilterindex**: Create compact filters for fast scanning

### Network Settings

**P2P Settings**
- Port: Which port to listen for peer connections (default 8333)
- Connections: Maximum number of peers to connect to

**Privacy Options**
- **Tor**: Connect through Tor network for privacy
- **I2P**: Connect through I2P network for privacy
- **IPv6**: Support IPv6 addresses

### Policy Engine

The policy engine allows you to filter which transactions appear in your mempool.

**Policy Profiles**
1. **Standard**: Bitcoin Core's default rules
2. **Conservative**: Stricter filtering, fewer transactions
3. **Aggressive**: Lenient filtering, more transactions
4. **Custom**: Your own rules

**Custom Rules**
- **datacarrier_size**: Maximum OP_RETURN data size (0-80 bytes)
- **dust_relay_fee**: Minimum value for outputs (in sat/vB)
- **permit_bare_multisig**: Allow old-style multisig transactions

### Backup & Recovery

**Backing Up**
1. Go to **Configuration** → **Backup**
2. Click **Download Backup**
3. Save the file to multiple secure locations
4. Verify backup file is readable

**Recovering**
1. If you lose data, run Oracle Knots on new hardware
2. Go to **Configuration** → **Restore**
3. Select backup file
4. Click **Restore**
5. Node will resync with your saved settings

---

## Policy Engine

The policy engine (BIP-110) lets you customize transaction filtering.

### What is a Policy?

A **policy** is a set of rules that determines which transactions your node accepts into its mempool (memory pool of unconfirmed transactions).

### Built-In Policies

**Standard** (Bitcoin Core default)
- Accepts most legitimate transactions
- Filters obvious spam
- Good for most users

**Conservative** (Strict)
- Rejects transactions with unusual patterns
- Filters more aggressively
- Good for privacy-conscious users

**Aggressive** (Permissive)
- Accepts almost all transactions
- Minimal filtering
- Good if you want to analyze all activity

### Creating a Custom Policy

1. Go to **Policy Engine** → **Custom**
2. Set your rules:
   - Data carrier size limit
   - Dust relay fee
   - Multisig rules
3. Click **Save Policy**
4. Your node now uses your custom rules

---

## Monitoring & Troubleshooting

### Dashboard Monitoring

**Green Status** = All good ✓
- Node fully synced
- Peers connected
- No errors

**Yellow Status** = Syncing
- Node downloading blocks
- This is normal during initial setup
- May take hours or days

**Red Status** = Problem
- Check error messages
- See troubleshooting section below

### Common Issues

**"Syncing is very slow"**
- Check internet connection speed (run speed test)
- Restart the node
- Check available disk space
- Increase cache size in configuration

**"No peers connected"**
- Restart node
- Check firewall isn't blocking port 8333
- Enable UPnP for automatic port opening
- Try adding manual seed nodes

**"Wallet won't load"**
- Try restarting Oracle Knots
- Check wallet file exists in data directory
- Try recovery from backup

**"Out of disk space"**
- Enable pruning to reduce storage
- Delete non-essential files
- Upgrade to larger storage device

### Viewing Logs

1. Go to **Logs** tab
2. Filter by log level (Info, Warning, Error)
3. Search for specific keywords
4. Recent errors are shown at the top

---

## Security Best Practices

### General Security

✅ **Do**
- Keep your recovery phrase written down and stored securely
- Enable wallet encryption
- Keep software updated
- Use a strong wallet password (≥12 characters)
- Keep your computer updated with security patches

❌ **Don't**
- Share your recovery phrase with anyone
- Store recovery phrase digitally (screenshot, email, cloud)
- Run Oracle Knots on untrusted computers
- Use weak passwords
- Ignore software updates

### Wallet Security

**Private Keys**
- Never share your recovery phrase
- Never type it into websites or applications
- Only enter it if recovering a lost wallet

**Address Privacy**
- Use different addresses for each transaction
- Don't reuse addresses publicly
- Label addresses to track where they came from

**Backups**
- Create backups of your wallet
- Store in multiple locations
- Test restoring from backup (to verify it works)
- Update backups after significant changes

### Network Security

- Use Tor or I2P if concerned about privacy
- Keep firewall enabled
- Only open necessary ports (8333 for P2P)
- Restrict RPC access to localhost only

---

## FAQ

**Q: How long does initial sync take?**
A: 2-24 hours depending on internet speed, CPU, and storage. SSD significantly speeds this up.

**Q: Can I use my node while it's syncing?**
A: Yes, you can use your wallet while the node syncs. Transactions may take longer to confirm.

**Q: What's the difference between Mainnet and Testnet?**
A: Mainnet uses real Bitcoin and real value. Testnet uses worthless test Bitcoin for practice.

**Q: Is my wallet safe if my computer is hacked?**
A: If encrypted, only with the correct password. Without encryption, your funds could be at risk.

**Q: Can I run multiple wallets?**
A: Yes, create multiple wallets in the wallet manager.

**Q: What happens if I turn off my node?**
A: Your wallet data is saved. Turning it back on will sync from where it left off.

**Q: Can I run a node on a Raspberry Pi?**
A: Yes, with pruning enabled. Full nodes need more resources, but pruned nodes work well.

**Q: How do I keep my node secure?**
A: Keep software updated, use firewall, encrypt wallet, backup recovery phrase, use strong passwords.

**Q: What's a PSBT?**
A: Partially Signed Bitcoin Transaction. Useful for multisig or offline signing scenarios.

**Q: Where is my wallet data stored?**
A: Default: `~/.bitcoin/wallets/` on Linux/macOS, `%APPDATA%\Bitcoin\wallets\` on Windows

**Q: Can I move my wallet to another computer?**
A: Yes, use backup/restore, or copy wallet files to `wallets/` directory on the new computer.

---

## Getting Help

- **GitHub Issues**: Report bugs at https://github.com/MarcanoFilms/oracle-knots/issues
- **Community**: Join our community for questions and discussion
- **Documentation**: Full docs available in the Help tab within Oracle Knots

---

## Version History

- **v1.0** (June 2026): Initial release with core features
- **v0.9** (Beta): Testing phase with community feedback

---

**Last Updated**: June 28, 2026  
**For More Help**: Use the Help tab in Oracle Knots for contextual assistance
