# Oracle Knots - Post-Launch Development Roadmap

**Version**: 1.0.0 → 2.0.0+  
**Date Created**: June 28, 2026  
**Status**: Planning Phase  

---

## Executive Summary

Oracle Knots v1.0.0 is production-ready with core Bitcoin node GUI functionality. The roadmap below defines the evolution toward v1.1, v2.0, and beyond, focusing on:

1. **User Experience** - Live price feeds, better dashboards, notifications
2. **Transaction Management** - Smart fees, RBF/CPFP, batch operations
3. **Security & Privacy** - 2FA, privacy scoring, hardware wallet support
4. **Analytics** - Tax reporting, on-chain analytics, portfolio tracking
5. **Platform Expansion** - Mobile apps, ecosystem integrations, plugins

---

## Version Roadmap at a Glance

| Version | Focus | Timeline | Status |
|---------|-------|----------|--------|
| **v1.0.0** | Core GUI, Wallets, Policy Engine | ✅ Released | ✅ COMPLETE |
| **v1.1.0** | Price Widget, Fee Management, UX Polish | Q3 2026 | 📋 Planning |
| **v1.2.0** | Privacy Features, Hardware Wallets | Q4 2026 | 📋 Planning |
| **v1.3.0** | Advanced Analytics, Notifications | Q1 2027 | 📋 Planning |
| **v2.0.0** | Mobile Apps, Ecosystem Integration | Q2-Q3 2027 | 🔮 Vision |

---

# PHASE 4: v1.1.0 - Price Widget & UX Enhancement

**Timeline**: 8-12 weeks  
**Effort**: 120-160 hours  
**Target Date**: Q3 2026  
**Priority**: HIGH

## 4.1 Live Bitcoin Price Widget

### Requirements
- Real-time BTC price in multiple currencies (USD, EUR, GBP, JPY, etc.)
- 24h price change with color coding (green/red)
- Mini 7-day sparkline chart
- Market cap, 24h volume, circulating supply
- Price updates every 60 seconds
- Caching to avoid excessive API calls

### Technical Implementation

**Backend (Python/Bottle)**

```python
# api/bitcoin_price.py
import requests
import time
from functools import wraps

class PriceCache:
    def __init__(self, ttl=60):
        self.cache = {}
        self.ttl = ttl
    
    def cached(self, func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            key = f"{func.__name__}"
            
            if key in self.cache:
                value, timestamp = self.cache[key]
                if time.time() - timestamp < self.ttl:
                    return value
            
            result = func(*args, **kwargs)
            self.cache[key] = (result, time.time())
            return result
        
        return wrapper

class BitcoinPriceService:
    """Fetch Bitcoin prices from CoinGecko API (free, no key required)"""
    
    COINGECKO_URL = "https://api.coingecko.com/api/v3/simple/price"
    HISTORY_URL = "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart"
    
    def __init__(self):
        self.cache = PriceCache(ttl=60)
    
    @property
    @cache.cached
    def current_price(self):
        """Get current BTC price in multiple currencies"""
        try:
            params = {
                'ids': 'bitcoin',
                'vs_currencies': 'usd,eur,gbp,jpy,cad,aud',
                'include_market_cap': 'true',
                'include_24hr_vol': 'true',
                'include_24hr_change': 'true'
            }
            response = requests.get(self.COINGECKO_URL, params=params, timeout=5)
            response.raise_for_status()
            return response.json()['bitcoin']
        except Exception as e:
            return {'error': str(e)}
    
    def get_price_history(self, days=7):
        """Get historical prices for sparkline (last 7 days)"""
        try:
            params = {
                'id': 'bitcoin',
                'vs_currency': 'usd',
                'days': days,
                'interval': 'daily'
            }
            response = requests.get(self.HISTORY_URL, params=params, timeout=5)
            response.raise_for_status()
            prices = response.json()['prices']
            return [{'date': p[0], 'price': p[1]} for p in prices]
        except Exception as e:
            return []

# gui.py routes
price_service = BitcoinPriceService()

@app.route('/api/bitcoin/price', method='GET')
def get_bitcoin_price():
    """Get current BTC price and 24h change"""
    try:
        current = price_service.current_price
        history = price_service.get_price_history(7)
        
        return {
            'success': True,
            'price': current,
            'history': history,
            'updated_at': time.time()
        }
    except Exception as e:
        return {'success': False, 'error': str(e)}, 500

@app.route('/api/bitcoin/portfolio-value', method='GET')
def get_portfolio_value():
    """Calculate total portfolio value in selected currency"""
    try:
        currency = request.query.get('currency', 'usd')
        
        # Get all wallets balance
        total_btc = 0
        for wallet in get_all_wallets():
            balance = run_bitcoin_cli(['getbalance', wallet])
            total_btc += balance
        
        # Get current price
        price_data = price_service.current_price
        btc_price = price_data.get(currency, price_data.get('usd'))
        
        portfolio_value = total_btc * btc_price
        
        return {
            'success': True,
            'total_btc': total_btc,
            'price_per_btc': btc_price,
            'portfolio_value': portfolio_value,
            'currency': currency
        }
    except Exception as e:
        return {'success': False, 'error': str(e)}, 500
```

**Frontend (JavaScript)**

```javascript
// gui/components/PriceWidget.js

class PriceWidget {
    constructor() {
        this.priceData = null;
        this.refreshInterval = 60000; // 60 seconds
        this.currencies = ['usd', 'eur', 'gbp', 'jpy'];
        this.selectedCurrency = localStorage.getItem('preferred_currency') || 'usd';
    }
    
    async init() {
        this.render();
        this.startAutoRefresh();
    }
    
    async fetchPriceData() {
        try {
            const response = await fetch('/api/bitcoin/price');
            if (!response.ok) throw new Error('Price fetch failed');
            
            const data = await response.json();
            this.priceData = data;
            this.updateUI();
        } catch (error) {
            console.error('Price widget error:', error);
            this.showError();
        }
    }
    
    updateUI() {
        if (!this.priceData) return;
        
        const price = this.priceData.price;
        const selectedPrice = price[this.selectedCurrency];
        const change24h = price[`${this.selectedCurrency}_24h_change`];
        
        // Update price display
        const priceEl = document.getElementById('btc-price');
        priceEl.textContent = this.formatCurrency(selectedPrice);
        
        // Update 24h change
        const changeEl = document.getElementById('btc-change');
        changeEl.textContent = `${change24h.toFixed(2)}%`;
        changeEl.classList.toggle('positive', change24h >= 0);
        changeEl.classList.toggle('negative', change24h < 0);
        
        // Update sparkline chart
        this.updateSparkline(this.priceData.history);
        
        // Update market data
        this.updateMarketData(price);
    }
    
    updateSparkline(history) {
        const prices = history.map(h => h.price);
        const min = Math.min(...prices);
        const max = Math.max(...prices);
        const range = max - min;
        
        // Simple SVG sparkline
        const points = prices.map((p, i) => {
            const x = (i / (prices.length - 1)) * 100;
            const y = 100 - ((p - min) / range) * 100;
            return `${x},${y}`;
        }).join(' ');
        
        const svg = `<svg class="price-sparkline" viewBox="0 0 100 40">
            <polyline points="${points}" fill="none" stroke="currentColor" stroke-width="2"/>
        </svg>`;
        
        document.getElementById('price-sparkline').innerHTML = svg;
    }
    
    updateMarketData(price) {
        const marketCapEl = document.getElementById('market-cap');
        const volumeEl = document.getElementById('volume-24h');
        const supplyEl = document.getElementById('circulating-supply');
        
        marketCapEl.textContent = this.formatLargeNumber(price.usd_market_cap);
        volumeEl.textContent = this.formatLargeNumber(price.usd_24h_vol);
        supplyEl.textContent = price.circulating_supply.toFixed(0) + ' BTC';
    }
    
    formatCurrency(amount) {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: this.selectedCurrency.toUpperCase(),
            minimumFractionDigits: 2
        }).format(amount);
    }
    
    formatLargeNumber(num) {
        if (num >= 1e12) return (num / 1e12).toFixed(1) + 'T';
        if (num >= 1e9) return (num / 1e9).toFixed(1) + 'B';
        if (num >= 1e6) return (num / 1e6).toFixed(1) + 'M';
        return num.toFixed(0);
    }
    
    startAutoRefresh() {
        this.fetchPriceData();
        setInterval(() => this.fetchPriceData(), this.refreshInterval);
    }
    
    render() {
        const html = `
            <div class="price-widget card">
                <div class="price-header">
                    <h2>Bitcoin Price</h2>
                    <select id="currency-selector" class="currency-dropdown">
                        ${this.currencies.map(c => 
                            `<option value="${c}" ${c === this.selectedCurrency ? 'selected' : ''}>
                                ${c.toUpperCase()}
                            </option>`
                        ).join('')}
                    </select>
                </div>
                
                <div class="price-display">
                    <div class="current-price">
                        <span id="btc-price" class="price-amount">--</span>
                    </div>
                    <div class="price-change">
                        <span id="btc-change" class="change-percent">--</span>
                        <span class="change-label">24h change</span>
                    </div>
                </div>
                
                <div id="price-sparkline" class="sparkline-container"></div>
                
                <div class="market-data">
                    <div class="market-item">
                        <label>Market Cap</label>
                        <span id="market-cap">--</span>
                    </div>
                    <div class="market-item">
                        <label>24h Volume</label>
                        <span id="volume-24h">--</span>
                    </div>
                    <div class="market-item">
                        <label>Supply</label>
                        <span id="circulating-supply">--</span>
                    </div>
                </div>
            </div>
        `;
        
        document.getElementById('price-widget-container').innerHTML = html;
        
        // Event listeners
        document.getElementById('currency-selector').addEventListener('change', (e) => {
            this.selectedCurrency = e.target.value;
            localStorage.setItem('preferred_currency', this.selectedCurrency);
            this.updateUI();
        });
    }
    
    showError() {
        const container = document.getElementById('price-widget-container');
        container.innerHTML = '<div class="alert alert-error">Unable to fetch price data</div>';
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    const widget = new PriceWidget();
    widget.init();
});
```

**CSS Styling**

```css
/* gui/price-widget.css */

.price-widget {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 1.5rem;
    border-radius: 12px;
    margin-bottom: 1.5rem;
}

.price-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
}

.price-header h2 {
    font-size: 1.25rem;
    font-weight: 600;
    margin: 0;
}

.currency-dropdown {
    background: rgba(255, 255, 255, 0.2);
    color: white;
    border: 1px solid rgba(255, 255, 255, 0.3);
    padding: 0.5rem 0.75rem;
    border-radius: 6px;
    font-size: 0.9rem;
}

.currency-dropdown option {
    background: #333;
    color: white;
}

.price-display {
    display: flex;
    align-items: baseline;
    gap: 1.5rem;
    margin-bottom: 1rem;
}

.current-price {
    flex: 1;
}

.price-amount {
    font-size: 2rem;
    font-weight: 700;
    display: block;
}

.price-change {
    text-align: right;
}

.change-percent {
    font-size: 1.5rem;
    font-weight: 600;
    display: block;
}

.change-percent.positive {
    color: #4ade80;
}

.change-percent.negative {
    color: #f87171;
}

.change-label {
    font-size: 0.85rem;
    opacity: 0.8;
}

.sparkline-container {
    margin-bottom: 1rem;
    height: 40px;
}

.price-sparkline {
    width: 100%;
    height: 100%;
    color: rgba(255, 255, 255, 0.6);
}

.market-data {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 1rem;
    padding-top: 1rem;
    border-top: 1px solid rgba(255, 255, 255, 0.2);
}

.market-item {
    text-align: center;
}

.market-item label {
    display: block;
    font-size: 0.75rem;
    opacity: 0.8;
    margin-bottom: 0.25rem;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.market-item span {
    display: block;
    font-size: 0.95rem;
    font-weight: 500;
}

/* Responsive */
@media (max-width: 768px) {
    .price-display {
        flex-direction: column;
        gap: 1rem;
    }
    
    .price-change {
        text-align: left;
    }
    
    .market-data {
        grid-template-columns: 1fr;
    }
}
```

### Estimated Effort
- Backend API: 8 hours
- Frontend component: 10 hours
- CSS styling: 6 hours
- Testing & refinement: 6 hours
- **Subtotal: 30 hours**

---

## 4.2 Portfolio Value Dashboard

### Features
- Total BTC balance across all wallets
- Portfolio value in selected currency (with real-time price)
- 7-day, 30-day, all-time charts
- Daily P&L tracking
- Export to CSV

### Technical Implementation

**Backend**

```python
# api/portfolio.py

class PortfolioManager:
    """Manage portfolio metrics and P&L tracking"""
    
    def __init__(self):
        self.db = get_database()
    
    def get_portfolio_snapshot(self, currency='usd'):
        """Get current portfolio snapshot"""
        total_btc = 0
        wallets_detail = []
        
        for wallet_name in list_wallets():
            balance = run_bitcoin_cli(['getbalance', wallet_name])
            wallet_info = {
                'name': wallet_name,
                'btc': balance,
                'usd': balance * get_btc_price(currency)
            }
            wallets_detail.append(wallet_info)
            total_btc += balance
        
        return {
            'total_btc': total_btc,
            'total_value': total_btc * get_btc_price(currency),
            'currency': currency,
            'wallets': wallets_detail,
            'timestamp': time.time()
        }
    
    def record_daily_snapshot(self):
        """Record daily portfolio snapshot for P&L tracking"""
        snapshot = self.get_portfolio_snapshot()
        
        self.db.execute("""
            INSERT INTO portfolio_history 
            (date, total_btc, total_value, price_usd, currency)
            VALUES (?, ?, ?, ?, ?)
        """, (
            datetime.date.today(),
            snapshot['total_btc'],
            snapshot['total_value'],
            get_btc_price('usd'),
            'usd'
        ))
    
    def get_portfolio_history(self, days=30):
        """Get portfolio history for charting"""
        query = """
            SELECT date, total_btc, total_value, price_usd
            FROM portfolio_history
            WHERE date >= date('now', ?)
            ORDER BY date
        """
        
        rows = self.db.execute(query, (f'-{days} days',)).fetchall()
        return [
            {
                'date': row[0],
                'btc': row[1],
                'value': row[2],
                'price': row[3]
            }
            for row in rows
        ]
    
    def calculate_pl(self):
        """Calculate P&L vs previous day"""
        today = self.get_portfolio_snapshot()
        
        yesterday = self.db.execute("""
            SELECT total_value FROM portfolio_history
            WHERE date = date('now', '-1 day')
        """).fetchone()
        
        if not yesterday:
            return {'change': 0, 'change_percent': 0}
        
        change = today['total_value'] - yesterday[0]
        change_percent = (change / yesterday[0]) * 100
        
        return {
            'change': change,
            'change_percent': change_percent,
            'previous_value': yesterday[0],
            'current_value': today['total_value']
        }

# API routes
portfolio = PortfolioManager()

@app.route('/api/portfolio/snapshot', method='GET')
def get_portfolio_snapshot():
    currency = request.query.get('currency', 'usd')
    return portfolio.get_portfolio_snapshot(currency)

@app.route('/api/portfolio/history', method='GET')
def get_portfolio_history():
    days = int(request.query.get('days', '30'))
    return portfolio.get_portfolio_history(days)

@app.route('/api/portfolio/pl', method='GET')
def get_pl():
    return portfolio.calculate_pl()
```

### Estimated Effort
- Backend implementation: 12 hours
- Frontend dashboard: 14 hours
- Charts integration: 8 hours
- **Subtotal: 34 hours**

---

## 4.3 Transaction Summary & Filtering

### Features
- Last 10 transactions with USD amounts
- Filters (sent, received, pending)
- Search by address/amount/date
- Transaction details modal

### Estimated Effort: 20 hours

---

## 4.4 Enhanced Address Management

### Features
- Address labeling with tags
- QR code generation
- Copy address with tooltip
- Address re-use warnings
- Receive address tracking

### Estimated Effort: 24 hours

---

## 4.5 UI/UX Polish

### Tasks
- Dark mode support
- Improved responsive layout
- Better form validation
- Loading states and skeletons
- Accessibility improvements

### Estimated Effort: 40 hours

---

# PHASE 5: v1.2.0 - Privacy & Security Enhancement

**Timeline**: 12-16 weeks  
**Effort**: 180-240 hours  
**Target Date**: Q4 2026  

## 5.1 Hardware Wallet Integration (Ledger, Trezor)

### Features
- PSBT workflow with hardware wallet signing
- Address verification on device
- Firmware update checks
- Multi-sig support

### Estimated Effort: 60 hours

---

## 5.2 Advanced Privacy Features

### Features
- Privacy score per wallet
- UTXO age visualization
- Coin mixing suggestions
- Tor integration indicator
- CoinJoin workflow

### Estimated Effort: 50 hours

---

## 5.3 Enhanced Security

### Features
- 2FA (TOTP) authentication
- Security audit log
- Backup encryption
- Password strength meter
- Session timeout

### Estimated Effort: 40 hours

---

# PHASE 6: v1.3.0 - Advanced Analytics & Notifications

**Timeline**: 8-12 weeks  
**Effort**: 150-200 hours  
**Target Date**: Q1 2027

## 6.1 Transaction Analytics

### Features
- Fee analysis (historical & patterns)
- On-chain transaction visualization
- Address clustering analysis
- Privacy heuristics detection

### Estimated Effort: 50 hours

---

## 6.2 Notification System

### Features
- Transaction alerts (in/out)
- Price alerts
- Mempool alerts (high fees, backlog)
- Network alerts (sync issues)

### Estimated Effort: 40 hours

---

## 6.3 Tax Reporting

### Features
- Gain/loss calculation
- Tax report generation (PDF/CSV)
- Cost basis tracking
- Multi-year reporting

### Estimated Effort: 40 hours

---

# PHASE 7: v2.0.0 - Mobile & Platform Expansion

**Timeline**: 16-24 weeks  
**Effort**: 400-600 hours  
**Target Date**: Q2-Q3 2027

## 7.1 Mobile Applications

### iOS & Android (React Native)
- Watch-only mode (no private keys)
- Transaction sending
- Price tracking
- Notifications

### Estimated Effort: 200-300 hours

---

## 7.2 Ecosystem Integration

### Features
- Lightning Network support
- DeFi position tracking
- Bridge monitoring
- Cross-chain swaps

### Estimated Effort: 100-150 hours

---

## 7.3 Plugin System & APIs

### Features
- Plugin architecture
- GraphQL API
- WebSocket support
- Webhook system

### Estimated Effort: 100-150 hours

---

# Implementation Priority Matrix

## High Priority (Implement ASAP)

| Phase | Feature | Impact | Effort | Timeline |
|-------|---------|--------|--------|----------|
| 4.1 | Bitcoin Price Widget | High | 30h | 2-3 weeks |
| 4.2 | Portfolio Dashboard | High | 34h | 3-4 weeks |
| 4.3 | Transaction Filters | High | 20h | 1-2 weeks |
| 5.1 | Hardware Wallets | Medium | 60h | 6-8 weeks |
| 5.3 | 2FA Security | High | 40h | 4-5 weeks |

## Medium Priority (Q3-Q4 2026)

| Phase | Feature | Impact | Effort | Timeline |
|-------|---------|--------|--------|----------|
| 4.5 | Dark Mode | Medium | 40h | 4-5 weeks |
| 5.2 | Privacy Features | Medium | 50h | 5-6 weeks |
| 6.1 | Fee Analytics | Medium | 50h | 5-6 weeks |
| 6.2 | Notifications | Medium | 40h | 4-5 weeks |

## Lower Priority (2027+)

| Phase | Feature | Impact | Effort | Timeline |
|-------|---------|--------|--------|----------|
| 6.3 | Tax Reporting | Medium | 40h | 4-5 weeks |
| 7.1 | Mobile Apps | High | 250h | 12-16 weeks |
| 7.2 | Ecosystem | Low | 150h | 8-12 weeks |
| 7.3 | Plugins/APIs | Medium | 150h | 8-12 weeks |

---

# Technical Architecture Notes

## API Design

All new features follow RESTful principles:

```
GET    /api/bitcoin/price              - Current price data
GET    /api/portfolio/snapshot         - Current portfolio
GET    /api/portfolio/history          - Historical data
GET    /api/portfolio/pl               - P&L tracking
GET    /api/transactions               - Transaction list
POST   /api/transactions/filter        - Advanced filtering
GET    /api/addresses                  - All addresses
POST   /api/addresses/label            - Add labels
GET    /api/security/audit-log         - Audit trail
POST   /api/notifications/subscribe    - Subscribe to alerts
```

## Database Schema

Additions for new features:

```sql
-- Portfolio history
CREATE TABLE portfolio_history (
    id INTEGER PRIMARY KEY,
    date DATE,
    total_btc REAL,
    total_value REAL,
    price_usd REAL,
    currency TEXT
);

-- Address labels
CREATE TABLE address_labels (
    address TEXT PRIMARY KEY,
    label TEXT,
    category TEXT,
    created_at TIMESTAMP
);

-- Price cache
CREATE TABLE price_cache (
    id INTEGER PRIMARY KEY,
    currency TEXT,
    price REAL,
    updated_at TIMESTAMP
);

-- Audit log
CREATE TABLE audit_log (
    id INTEGER PRIMARY KEY,
    action TEXT,
    details TEXT,
    user TEXT,
    timestamp TIMESTAMP
);
```

## Security Considerations

1. **Price API Caching**: Cache API responses to reduce external calls
2. **No API Keys Stored**: Use only free/public APIs
3. **Rate Limiting**: Maintain existing rate limits
4. **User Data**: Never send portfolio data to external services
5. **Local Processing**: All sensitive calculations happen locally

---

# Team Recommendations

## Solo Developer Path (Recommended for v1.1-1.2)

**Timeline**: 20-24 weeks
- v1.1: 12 weeks (Phase 4)
- v1.2: 12-16 weeks (Phase 5)
- Can deliver features steadily with community testing

## Small Team Path (3 people, Recommended for v1.3+)

**Timeline**: 12-16 weeks
- Frontend Dev: UI/UX for all features
- Backend Dev: APIs, data processing, integrations
- QA/Testing: Test coverage, security audits

**Roles**:
1. Frontend/UX: Phase 4-6 UI work
2. Backend/API: Price integrations, analytics
3. Devops/QA: Testing, deployment, security

---

# Success Metrics

## v1.1.0 Success Criteria
- ✅ Live price widget updates every 60s
- ✅ Portfolio dashboard shows accurate values
- ✅ <50ms response time for price requests
- ✅ Price data cached effectively
- ✅ 50+ concurrent users supported

## v1.2.0 Success Criteria
- ✅ Hardware wallet signing works on Linux/macOS/Windows
- ✅ Privacy score accurately reflects wallet mixing
- ✅ 2FA reduces unauthorized access to near-zero
- ✅ No data breaches or security incidents

## v2.0.0 Success Criteria
- ✅ Mobile app reaches 10k+ downloads
- ✅ Plugin ecosystem has 5+ quality plugins
- ✅ GraphQL API used by 3rd-party apps
- ✅ 100k+ active users across platforms

---

# Budget Estimation

| Phase | Effort | Solo Dev | Small Team | Cost |
|-------|--------|----------|-----------|------|
| 4.1-4.5 (v1.1) | 120-160h | $6-8k | $12-16k | Salary-based |
| 5.1-5.3 (v1.2) | 180-240h | $9-12k | $18-24k | Salary-based |
| 6.1-6.3 (v1.3) | 150-200h | $7.5-10k | $15-20k | Salary-based |
| 7.1-7.3 (v2.0) | 400-600h | $20-30k | $40-60k | Salary-based |

---

# Dependencies & Blockers

| Issue | Mitigation |
|-------|-----------|
| Price API rate limits | Implement local caching (60s TTL) |
| CoinGecko API downtime | Fallback to Kraken API |
| User privacy concerns | Use only local APIs, no data sharing |
| Hardware wallet fragmentation | Support Ledger & Trezor only initially |
| Mobile platform complexity | Start with iOS, Android follows |

---

# Next Steps

1. **Week 1**: Design UI mockups for v1.1 features
2. **Week 2-3**: Implement Bitcoin price widget
3. **Week 4-5**: Build portfolio dashboard
4. **Week 6-7**: Polish and testing
5. **Week 8+**: Begin v1.2 (hardware wallets)

---

**Oracle Knots Development Roadmap - v1.0.0+**

Built for Bitcoin sovereignty. Ready for the future. 🚀

