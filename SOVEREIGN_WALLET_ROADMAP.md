# Oracle Knots - Sovereign Wallet Development Roadmap

**Version**: 1.0.0 → 2.0.0+  
**Focus**: Complete Bitcoin Wallet for Sovereign Nodes  
**Hardware Integration**: Keystone Wallet (Rust-based, Bitcoin-only)  
**Date Updated**: June 28, 2026  

---

## Strategic Direction Change

### What Changed
- ❌ **Removed**: Mobile apps (Bitcoin nodes cannot run on mobile)
- ✅ **Focused**: Complete wallet implementation for sovereign node operators
- ✅ **Added**: Hardware wallet integration (Keystone as primary reference)
- ✅ **Prioritized**: Wallet becomes THE killer feature

### Why This Approach
1. **Sovereign Node Reality**: Full nodes need real machines, not phones
2. **Hardware Wallet Integration**: Most secure way to manage funds
3. **Keystone Reference**: Modern, open-source, Rust-based, Bitcoin-only
4. **Market Gap**: No desktop wallet is complete for sovereign node operators
5. **Long-term Value**: Best wallet for Bitcoin maximalists running their own nodes

---

## Vision: The Most Complete Sovereign Wallet

Oracle Knots Wallet should become the **definitive desktop wallet** for:
- ✅ Bitcoin maximalists running full nodes
- ✅ Privacy-conscious users (Tor/I2P integration)
- ✅ Advanced traders (fee optimization, CPFP, RBF)
- ✅ Cold storage managers (hardware wallet integration)
- ✅ Self-sovereign operators (no KYC, no cloud)

---

# Phase 4: v1.1.0 - SOVEREIGN WALLET FOUNDATION

**Timeline**: 12-16 weeks  
**Effort**: 200-280 hours  
**Target**: Q3-Q4 2026  
**Priority**: CRITICAL

## 4.1 Bitcoin Price Widget (Foundation Layer)

**Status**: Ready to implement  
**Effort**: 30 hours

See DEVELOPMENT_ROADMAP.md for complete implementation.

---

## 4.2 Portfolio Management & Tracking

**Effort**: 50 hours

### Features
- **Multi-wallet management** with balance tracking
- **Portfolio value** in multiple currencies (real-time via CoinGecko)
- **Transaction history** with USD/EUR amounts
- **Balance evolution** over time (7d, 30d, all-time charts)
- **P&L tracking** with daily snapshots
- **Export** to CSV (for tax purposes)
- **Watch-only** wallet support (for xpub tracking)

### Architecture

```python
# oracle_knots/wallet/portfolio.py

class SovereignWallet:
    """Complete sovereign wallet management"""
    
    def __init__(self, node):
        self.node = node
        self.keystore = KeystoreManager()
        self.utxo_manager = UTXOManager()
        self.fee_estimator = FeeEstimator()
    
    def get_portfolio_status(self):
        """Get complete portfolio snapshot"""
        return {
            'wallets': self.list_wallets(),
            'total_btc': self.get_total_balance(),
            'total_value': self.calculate_portfolio_value(),
            'utxos': self.get_utxo_analysis(),
            'pending_txs': self.get_pending_transactions(),
            'last_updated': time.time()
        }
    
    def analyze_utxos(self):
        """Analyze UTXO set for privacy and efficiency"""
        return {
            'total_utxos': self.count_utxos(),
            'by_value': self.group_by_value(),
            'by_age': self.group_by_age(),
            'privacy_score': self.calculate_privacy(),
            'consolidation_opportunities': self.find_consolidation_targets()
        }
```

---

## 4.3 Advanced Transaction Management

**Effort**: 60 hours

### Transaction Types & Features

#### Standard Transactions
- Single input, multiple outputs
- Fee estimation (mempool-based)
- RBF (Replace-By-Fee) support
- RBPCP (Replace-By-Parent) creation
- Preview before signing

#### Advanced Transactions
- **Batch send** (1 input → N outputs)
- **Coin control** with UTXO selection UI
- **CPFP** (Child-Pays-For-Parent) assistant
- **Dust consolidation** (merge small UTXOs)
- **Cold storage** consolidation from hardware wallet
- **Privacy mixing** wallet creation

#### PSBT Workflows
- **Full PSBT lifecycle**: Create → Sign → Finalize → Broadcast
- **Hardware wallet signing**: Keystone integration
- **Multi-sig support**: 2-of-3, 3-of-5, etc.
- **Offline signing**: Air-gapped cold storage

### Architecture

```python
# oracle_knots/wallet/transactions.py

class TransactionBuilder:
    """Advanced transaction building for sovereign operators"""
    
    def __init__(self, wallet, fee_estimator):
        self.wallet = wallet
        self.fee_estimator = fee_estimator
    
    def create_transaction(self, recipients, fee_rate=None, coin_control=None):
        """Create optimized transaction"""
        if fee_rate is None:
            fee_rate = self.fee_estimator.get_recommended_rate()
        
        utxos = self.select_utxos(recipients, coin_control)
        inputs = self.build_inputs(utxos)
        outputs = self.build_outputs(recipients)
        change = self.calculate_change(inputs, outputs, fee_rate)
        
        return {
            'inputs': inputs,
            'outputs': outputs,
            'fee': self.calculate_fee(fee_rate, inputs, outputs),
            'size': self.estimate_size(inputs, outputs),
            'priority': self.estimate_priority(fee_rate),
            'rbf_enabled': True,
            'preview': self.create_preview(inputs, outputs)
        }
    
    def create_batch_transaction(self, recipients, coin_control=None):
        """Create batch send (many outputs)"""
        return self.create_transaction(recipients, coin_control=coin_control)
    
    def create_consolidation_tx(self, target_utxos=None):
        """Create UTXO consolidation transaction"""
        utxos = target_utxos or self.wallet.get_small_utxos()
        return self.create_transaction(
            recipients=[{'address': self.wallet.get_change_address()}],
            coin_control={'utxos': [u['outpoint'] for u in utxos]}
        )
    
    def create_psbt(self, tx_dict):
        """Create PSBT for hardware wallet signing"""
        return PSBTBuilder(tx_dict).build()

class FeeEstimator:
    """Smart fee estimation based on mempool"""
    
    def get_recommended_rate(self, target_blocks=6):
        """Get recommended fee rate"""
        mempool = self.get_mempool_analysis()
        return mempool['fee_rates'][target_blocks]
    
    def get_all_rates(self):
        """Get fee rates for different targets"""
        return {
            'next_block': self.get_recommended_rate(1),
            'fast': self.get_recommended_rate(3),
            'standard': self.get_recommended_rate(6),
            'slow': self.get_recommended_rate(12),
            'minimum': self.get_minimum_rate()
        }
```

---

## 4.4 Keystone Hardware Wallet Integration

**Effort**: 80 hours

### Keystone Wallet Reference
- **Repository**: https://github.com/keystonehq/keystone
- **Language**: Rust (Bitcoin-only firmware)
- **Protocol**: UR (Unified Resources) with QR codes
- **Features**: PSBT signing, multi-sig, air-gapped

### Integration Strategy

#### Phase 1: Basic PSBT Signing
```python
# oracle_knots/wallet/keystone_integration.py

from ur_codec import URCodec
from psbt import PSBT

class KeystoneWalletIntegration:
    """Integration with Keystone hardware wallet"""
    
    def __init__(self):
        self.ur_codec = URCodec()
    
    def create_psbt_qr(self, psbt: PSBT) -> str:
        """Create animated QR code for PSBT signing"""
        ur_bytes = self.ur_codec.encode_psbt(psbt)
        qr_data = self.generate_qr_animation(ur_bytes)
        return qr_data
    
    def scan_signed_qr(self, qr_data: str) -> PSBT:
        """Scan QR code with signed PSBT from Keystone"""
        ur_bytes = self.parse_qr_animation(qr_data)
        signed_psbt = self.ur_codec.decode_psbt(ur_bytes)
        return signed_psbt
    
    def verify_keystone_connection(self):
        """Check if Keystone firmware is compatible"""
        return {
            'connected': True,
            'firmware_version': self.get_firmware_version(),
            'supports_psbt': True,
            'supports_multisig': True
        }

class KeystoneQRScanner:
    """Handle animated QR code scanning"""
    
    def __init__(self):
        self.frame_buffer = []
    
    def start_scanning(self):
        """Begin scanning QR frames"""
        self.frame_buffer = []
    
    def add_frame(self, qr_frame):
        """Add scanned QR frame"""
        self.frame_buffer.append(qr_frame)
    
    def is_complete(self):
        """Check if all frames received"""
        return self.validate_frames()
    
    def get_result(self):
        """Get complete QR data"""
        return self.reassemble_frames(self.frame_buffer)
```

#### Phase 2: Multi-Sig Support
- Support for 2-of-3, 3-of-5 setups
- Extended public key (xpub) management
- Multisig wallet creation and recovery

#### Phase 3: Advanced Features
- Batch transaction signing
- Cold storage management
- Transaction verification on device

### Architecture Diagram

```
┌─────────────────────────────────────────┐
│   Oracle Knots Wallet (Desktop)         │
│  (Python + JavaScript Frontend)         │
└─────────────────────────────────────────┘
                    │
                    │ PSBT via UR/QR
                    ▼
┌─────────────────────────────────────────┐
│   Keystone Hardware Wallet (Rust)       │
│  - Sign transactions                    │
│  - Multi-sig support                    │
│  - Air-gapped (no network)              │
└─────────────────────────────────────────┘
                    │
                    │ Signed PSBT via QR
                    ▼
┌─────────────────────────────────────────┐
│   Bitcoin Knots Node                    │
│  - Broadcast transactions               │
│  - Verify balances                      │
│  - RPC Interface                        │
└─────────────────────────────────────────┘
```

---

## 4.5 Complete UTXO Management

**Effort**: 40 hours

### Features
- **Visual UTXO display** (amount, age, address, status)
- **Privacy analysis** (heuristics detection)
- **Coin selection algorithm** (privacy-first vs efficiency)
- **Consolidation suggestions** (when and how to merge)
- **Dust identification** (UTXOs not worth spending)
- **Cold storage** tracking (xpub-based monitoring)

### Implementation

```python
# oracle_knots/wallet/utxo_manager.py

class UTXOManager:
    """Advanced UTXO management for sovereign operators"""
    
    def get_utxo_analysis(self):
        """Complete UTXO analysis"""
        return {
            'total_count': len(self.get_all_utxos()),
            'total_value': self.sum_all_utxos(),
            'by_age': self.group_by_age(),
            'by_address': self.group_by_address(),
            'privacy_metrics': self.calculate_privacy(),
            'consolidation_opportunities': self.find_consolidation(),
            'dust_utxos': self.identify_dust()
        }
    
    def get_privacy_score(self, wallet=None):
        """Calculate privacy score (0-100)"""
        factors = {
            'address_reuse': self.check_address_reuse(wallet),
            'change_detection': self.detect_change_patterns(wallet),
            'coin_age': self.analyze_coin_age(wallet),
            'amount_patterns': self.analyze_amounts(wallet)
        }
        return self.calculate_score(factors)
    
    def recommend_consolidation(self):
        """Recommend UTXO consolidation"""
        utxos = self.get_all_utxos()
        recommendations = []
        
        for group in self.find_consolidation_groups(utxos):
            if self.should_consolidate(group):
                recommendations.append({
                    'utxos': group,
                    'current_value': self.sum_group(group),
                    'consolidation_cost': self.estimate_consolidation_fee(group),
                    'savings_per_spend': self.estimate_future_savings(group),
                    'privacy_impact': self.calculate_privacy_impact(group)
                })
        
        return recommendations

class PrivacyAnalyzer:
    """Analyze wallet privacy"""
    
    def detect_change_patterns(self, wallet):
        """Detect if change detection is possible"""
        transactions = wallet.get_transactions()
        return {
            'suspicious_patterns': self.find_patterns(transactions),
            'risk_level': self.calculate_risk(transactions),
            'recommendations': self.suggest_improvements(transactions)
        }
    
    def analyze_mixing_potential(self):
        """Suggest mixing strategies"""
        return {
            'coinjoin_pools': self.find_coinjoin_pools(),
            'mixing_recommendations': self.suggest_mixing(),
            'privacy_gain': self.estimate_privacy_gain()
        }
```

---

## 4.6 Professional UI/UX for Wallet

**Effort**: 50 hours

### Wallet Dashboard
- **Account overview** (balance, price, P&L)
- **Quick actions** (send, receive, request)
- **Recent transactions** (with USD amounts)
- **UTXO status** (visual representation)
- **Fee recommendations** (mempool-based)

### Send Transaction Flow
```
Step 1: Select Recipient
├─ Address or BIP47 PayCode
├─ Contact book
└─ Recent addresses

Step 2: Amount & Fees
├─ Amount in BTC/USD
├─ Fee estimation (fast/standard/slow)
├─ Coin control (optional)
└─ Fee preview

Step 3: Review
├─ Transaction details
├─ Address verification
├─ Fee breakdown
└─ Confirm or edit

Step 4: Sign
├─ Hardware wallet (Keystone QR)
├─ Software signing (with password)
└─ Or offline PSBT

Step 5: Broadcast
├─ Send to network
├─ Track confirmation
└─ Show txid
```

### Receive Flow
```
Step 1: Select Wallet
└─ Choose receiving address

Step 2: Request Details
├─ Amount (optional)
├─ Description
├─ Invoice expiry
└─ Generate payment request

Step 3: Share
├─ Bitcoin URI
├─ QR code
├─ BIP70 payment request
└─ Copy address
```

---

# Phase 5: v1.2.0 - ADVANCED WALLET FEATURES

**Timeline**: 16-20 weeks  
**Effort**: 240-320 hours  
**Target**: Q4 2026 - Q1 2027  

## 5.1 BIP47 Reusable Payment Codes (80h)

- Generate and share payment codes
- Receive payments without address reuse
- Complete privacy for recipient
- Contact management with payment codes

## 5.2 Multi-Signature Wallets (100h)

- Create 2-of-2, 2-of-3, 3-of-5 setups
- Hardware wallet key storage
- Keystone multi-sig signing
- Recovery phrase backup
- Timelocks and relative locks

## 5.3 Advanced Fee Management (60h)

- Mempool fee analysis
- RBF transaction replacement
- CPFP transaction creation
- Fee prediction models
- Historical fee tracking

---

# Phase 6: v1.3.0 - SOVEREIGN FEATURES

**Timeline**: 12-16 weeks  
**Effort**: 180-240 hours  
**Target**: Q1-Q2 2027  

## 6.1 Privacy Enhancement (80h)

- Tor integration status
- CoinJoin integration preparation
- Privacy score tracking
- Mixing recommendations
- Address clustering detection

## 6.2 Tax & Accounting (60h)

- Gain/loss calculation
- Tax report generation
- Cost basis tracking
- Multi-year reporting
- Export to tax software (TurboTax, etc.)

## 6.3 On-Chain Analytics (100h)

- Transaction analysis
- Fee pattern analysis
- UTXO set visualization
- Network insights
- Mempool monitoring

---

# Phase 7: v2.0.0 - ECOSYSTEM INTEGRATION

**Timeline**: 16-20 weeks  
**Effort**: 240-320 hours  
**Target**: Q2-Q3 2027  

## 7.1 Extended Hardware Wallet Support (80h)

- Trezor integration
- Ledger integration
- ColdCard compatibility
- Custom device support via standard protocols

## 7.2 Lightning Network (120h)

- Channel opening from wallet
- Payment routing
- Invoice generation
- Balance management

## 7.3 Advanced Protocols (160h)

- BIP78 Payjoin
- Stonewall/Stonewall2 transactions
- Ricochet transactions
- Mixing protocols

---

# Implementation Priority (Updated)

## 🔴 CRITICAL Phase 4 (v1.1.0)

**Timeline**: 12-16 weeks | **Effort**: 200-280h | **Budget**: $10-14k

1. ✅ Price Widget (30h) - START IMMEDIATELY
2. ✅ Portfolio Management (50h)
3. ✅ Transaction Management (60h)
4. ✅ Keystone Integration (80h)
5. ✅ UTXO Management (40h)
6. ✅ Professional UI/UX (50h)

**Result**: Complete sovereign wallet with hardware signing

## 🟠 HIGH Priority Phase 5 (v1.2.0)

**Timeline**: 16-20 weeks | **Effort**: 240-320h | **Budget**: $12-16k

1. BIP47 Payment Codes (80h)
2. Multi-Sig Wallets (100h)
3. Advanced Fees (60h)

**Result**: Advanced features for traders & privacy users

## 🟡 MEDIUM Priority Phase 6 (v1.3.0)

**Timeline**: 12-16 weeks | **Effort**: 180-240h | **Budget**: $9-12k

1. Privacy Enhancement (80h)
2. Tax & Accounting (60h)
3. On-Chain Analytics (100h)

**Result**: Professional-grade features

## 🔵 FUTURE Phase 7 (v2.0.0)

**Timeline**: 16-20 weeks | **Effort**: 240-320h | **Budget**: $12-16k

1. Extended Hardware Support (80h)
2. Lightning Network (120h)
3. Advanced Protocols (160h)

**Result**: Complete ecosystem integration

---

# Total Effort & Budget (No Mobile Apps)

| Phase | Version | Duration | Effort | Budget |
|-------|---------|----------|--------|--------|
| 4 | v1.1.0 | 12-16 wks | 200-280h | $10-14k |
| 5 | v1.2.0 | 16-20 wks | 240-320h | $12-16k |
| 6 | v1.3.0 | 12-16 wks | 180-240h | $9-12k |
| 7 | v2.0.0 | 16-20 wks | 240-320h | $12-16k |
| **TOTAL** | | **56-72 wks** | **860-1160h** | **$43-58k** |

**Time Frame**: ~18 months to v2.0.0  
**Team Size**: 1-2 developers (solo for v1.1-1.2, team for v1.3+)  

---

# Keystone Integration Details

## Why Keystone?
1. ✅ **Bitcoin-only** (no altcoin bloat)
2. ✅ **Open source** (Rust firmware)
3. ✅ **Modern protocols** (UR/QR codes, not USB)
4. ✅ **Air-gapped** (complete security)
5. ✅ **Hardware wallet standard** (widely compatible)
6. ✅ **Active development** (GitHub: keystonehq/keystone)

## Implementation Stack
- **Backend**: Python interface to Keystone via UR protocol
- **Frontend**: QR code display for PSBTs
- **QR Scanning**: Built-in camera or external scanner
- **Signing**: Fully air-gapped (no USB or network)

## Reference Implementation
```
Oracle Knots (Desktop GUI)
    ↓ PSBT as UR/QR
Keystone (Hardware Wallet)
    ↓ Signed PSBT as UR/QR
Oracle Knots (Broadcast)
    ↓ Transaction
Bitcoin Network
```

---

# Competitive Positioning

Oracle Knots Wallet will be **the best** for sovereign node operators because:

| Feature | Sparrow | Electrum | BlueWallet | Oracle Knots |
|---------|---------|----------|-----------|--------------|
| Full Node Integration | ❌ No | ❌ No | ❌ No | ✅ **Native** |
| Keystone Support | ✅ Yes | ❌ No | ❌ No | ✅ **Yes** |
| Multi-Sig | ✅ Yes | ✅ Yes | ✅ Yes | ✅ **Yes** |
| PSBT | ✅ Yes | ✅ Yes | ✅ Yes | ✅ **Yes** |
| Privacy Score | ❌ No | ❌ No | ❌ No | ✅ **Yes** |
| UTXO Analysis | ✅ Limited | ✅ Limited | ❌ No | ✅ **Advanced** |
| Tax Reporting | ❌ No | ❌ No | ❌ No | ✅ **Yes** |
| Fee Analysis | ✅ Basic | ✅ Basic | ❌ No | ✅ **Advanced** |
| BIP47 PayCodes | ✅ Yes | ❌ No | ❌ No | ✅ **Yes** |
| Lightning | ❌ No | ✅ Yes | ✅ Yes | ✅ **Planned** |

**Oracle Knots Unique Value**: Complete wallet for sovereign node operators

---

# Next Steps: START NOW

## Week 1-2: Design & Setup
- [ ] UI mockups for wallet screens
- [ ] Database schema for wallet data
- [ ] API design for wallet endpoints
- [ ] Keystone integration research

## Week 2-4: Price Widget (30h)
- [ ] Backend: CoinGecko API integration
- [ ] Frontend: PriceWidget component
- [ ] CSS styling (responsive)
- [ ] Testing & refinement

## Week 4-9: Portfolio & Transactions (110h)
- [ ] Portfolio management (50h)
- [ ] Transaction builder (60h)

## Week 9-13: Keystone Integration (80h)
- [ ] PSBT generation
- [ ] QR code handling
- [ ] Keystone protocol implementation

## Week 13-16: UTXO Management & UI (90h)
- [ ] UTXO analyzer (40h)
- [ ] Professional UI (50h)

## Week 16: Testing & Release (20h)
- [ ] Unit tests
- [ ] Integration tests
- [ ] v1.1.0 release

---

# Success Metrics for v1.1.0

✅ **Functional**
- Complete wallet operations (send, receive, view balance)
- Hardware wallet signing (Keystone)
- Transaction preview before sending
- UTXO management and analysis

✅ **Quality**
- 75%+ test coverage
- <500ms transaction preview time
- All major platforms (Linux, macOS, Windows)
- No security vulnerabilities

✅ **User Experience**
- 5+ users successfully complete send/receive flows
- Hardware wallet signing works seamlessly
- Clear, professional UI
- Intuitive fee selection

---

# The Vision

Oracle Knots Wallet will be **THE** wallet for:
- Bitcoin maximalists running full nodes
- Privacy-focused users (Tor integration)
- Advanced traders (professional fee management)
- Cold storage operators (hardware wallet integration)
- Sovereign individuals (complete self-custody)

By v2.0.0, it will rival or exceed Sparrow, Electrum, and BlueWallet in features while being **the only one** designed specifically for full node operators.

**Ready to build the future of sovereign Bitcoin wallets?** 🚀

