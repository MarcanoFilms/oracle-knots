# Oracle Knots Documentation Plan

**Phase 3.3: Documentation**  
**Target**: Comprehensive docs for users, developers, and operators  
**Timeline**: Weeks 11-12

---

## 1. User Guide (2000-3000 words)

### File: `docs/USER_GUIDE.md`

**Structure**:
1. **Introduction**
   - What is Oracle Knots?
   - Why run your own node?
   - System requirements

2. **Installation**
   - Build from source
   - Download binaries
   - System dependencies
   - Verifying builds

3. **Getting Started**
   - First time setup
   - Understanding the interface
   - Dashboard overview
   - Key features

4. **Wallet Operations**
   - Creating a wallet
   - Generating addresses
   - Receiving Bitcoin
   - Sending transactions
   - Coin control
   - PSBT workflows
   - Wallet security

5. **Configuration**
   - Storage settings
   - Network settings
   - Privacy (Tor/I2P)
   - Policy filters
   - Mining setup

6. **Monitoring**
   - Understanding sync status
   - Monitoring peers
   - Tracking transactions
   - Understanding rejections

7. **Security**
   - Best practices
   - Wallet backup
   - Recovery
   - Updates

8. **Troubleshooting**
   - Common issues
   - Debug logs
   - Performance optimization
   - Getting help

9. **FAQ**
   - General questions
   - Technical questions
   - Security questions
   - Community resources

### Content Outline

**Introduction Section**
```
What is Oracle Knots? (200 words)
- Bitcoin Knots-based fork
- Modern GUI focus
- Sovereign node control
- User-friendly interface

Why Run Your Own Node? (200 words)
- Privacy benefits
- Security independence
- Network participation
- Supporting Bitcoin

System Requirements (200 words)
- Minimum: 4GB RAM, 600GB SSD, 2 Mbps internet
- Recommended: 8GB RAM, 1TB SSD, 10 Mbps
- Network ports
- Operating systems supported
```

**Getting Started**
```
First Time Setup (400 words)
- Download and build
- Initial configuration
- Starting the node
- First sync

Understanding the Interface (300 words)
- Dashboard layout
- Navigation
- Key information
- Quick actions

Dashboard Overview (300 words)
- Sync status
- Peer count
- Memory usage
- Recent blocks
- Policy status
- Mining info (if mining)
```

**Wallet Operations** (800 words)
```
Creating a Wallet
- Step-by-step guide
- Wallet naming
- Backup immediately

Receiving Bitcoin
- Generate address
- Share address/QR code
- Monitor balance

Sending Bitcoin
- Simple send
- Coin control send
- Fee selection
- Transaction confirmation

PSBT Workflows
- What is PSBT?
- Multisig scenarios
- Hardware wallet use
- Air-gapped signing

Wallet Security
- Encryption
- Backups
- Recovery
- Updating Bitcoin
```

**Troubleshooting** (400 words)
```
"My node won't start"
- Check ports
- Review logs
- Common issues

"My sync is stuck"
- Network connectivity
- Peer count
- Disk space

"Balance shows but no transactions"
- Rescan wallet
- Check labels
- Review filters

"I forgot my passphrase"
- Recovery options
- Prevention tips

"How to get help"
- Forums
- GitHub issues
- Community
```
