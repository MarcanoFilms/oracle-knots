/**
 * Oracle Knots - Bitcoin Price Widget Component
 *
 * Real-time Bitcoin price display with sparkline chart
 * - Multiple currencies (USD, EUR, GBP, JPY, CAD, AUD)
 * - 24h price change with color indicator
 * - 7-day sparkline chart
 * - Market cap, volume, supply info
 * - Auto-refresh every 60 seconds
 * - Responsive design
 *
 * Usage:
 *   const widget = new PriceWidget('price-widget-container');
 *   widget.init();
 */

class PriceWidget {
    constructor(containerId = 'price-widget-container') {
        this.containerId = containerId;
        this.priceData = null;
        this.historyData = null;
        this.refreshInterval = 60000; // 60 seconds
        this.currencies = ['usd', 'eur', 'gbp', 'jpy', 'cad', 'aud'];
        this.currencySymbols = {
            'usd': '$',
            'eur': '€',
            'gbp': '£',
            'jpy': '¥',
            'cad': 'C$',
            'aud': 'A$'
        };
        this.selectedCurrency = localStorage.getItem('preferred_currency') || 'usd';
        this.autoRefreshTimer = null;
    }

    /**
     * Initialize widget and start auto-refresh
     */
    async init() {
        this.render();
        await this.fetchData();
        this.startAutoRefresh();
    }

    /**
     * Fetch price data from API
     */
    async fetchData() {
        try {
            // Fetch current price
            const priceResponse = await fetch('/api/bitcoin/price');
            if (!priceResponse.ok) throw new Error('Price fetch failed');
            this.priceData = await priceResponse.json();

            // Fetch historical data
            const historyResponse = await fetch('/api/bitcoin/history?days=7');
            if (!historyResponse.ok) throw new Error('History fetch failed');
            this.historyData = await historyResponse.json();

            this.updateUI();
        } catch (error) {
            console.error('Price widget error:', error);
            this.showError(error.message);
        }
    }

    /**
     * Update UI with fetched data
     */
    updateUI() {
        if (!this.priceData || !this.priceData.success) return;

        const price = this.priceData.price;
        const selectedPrice = price[this.selectedCurrency];
        const change24h = price[`${this.selectedCurrency}_24h_change`];

        // Update price display
        const priceEl = document.getElementById('btc-price');
        if (priceEl) {
            priceEl.textContent = this.formatCurrency(selectedPrice);
        }

        // Update 24h change
        const changeEl = document.getElementById('btc-change');
        if (changeEl) {
            changeEl.textContent = `${change24h.toFixed(2)}%`;
            changeEl.classList.remove('positive', 'negative');
            changeEl.classList.add(change24h >= 0 ? 'positive' : 'negative');
        }

        // Update sparkline
        if (this.historyData && this.historyData.success) {
            this.updateSparkline(this.historyData.data);
        }

        // Update market data
        this.updateMarketData(price);

        // Update timestamp
        const lastUpdated = new Date(this.priceData.updated_at * 1000);
        const updatedEl = document.getElementById('price-updated');
        if (updatedEl) {
            updatedEl.textContent = `Updated: ${this.formatTime(lastUpdated)}`;
        }
    }

    /**
     * Update sparkline chart
     */
    updateSparkline(history) {
        const prices = history.map(h => h.price);
        if (prices.length < 2) return;

        const min = Math.min(...prices);
        const max = Math.max(...prices);
        const range = max - min || 1;

        // Create SVG points for polyline
        const points = prices.map((p, i) => {
            const x = (i / (prices.length - 1)) * 100;
            const y = 100 - ((p - min) / range) * 100;
            return `${x},${y}`;
        }).join(' ');

        // Determine color based on change
        const startPrice = prices[0];
        const endPrice = prices[prices.length - 1];
        const isPositive = endPrice >= startPrice;
        const lineColor = isPositive ? '#22c55e' : '#ef4444';

        const svg = `
            <svg class="price-sparkline" viewBox="0 0 100 40" xmlns="http://www.w3.org/2000/svg">
                <defs>
                    <linearGradient id="sparkline-gradient" x1="0%" y1="0%" x2="0%" y2="100%">
                        <stop offset="0%" style="stop-color:${lineColor};stop-opacity:0.3" />
                        <stop offset="100%" style="stop-color:${lineColor};stop-opacity:0.01" />
                    </linearGradient>
                </defs>
                <polyline
                    points="${points}"
                    fill="none"
                    stroke="${lineColor}"
                    stroke-width="1.5"
                />
                <polyline
                    points="${points}"
                    fill="url(#sparkline-gradient)"
                />
            </svg>
        `;

        const container = document.getElementById('price-sparkline');
        if (container) {
            container.innerHTML = svg;
        }
    }

    /**
     * Update market data display
     */
    updateMarketData(price) {
        // Market cap
        const marketCapEl = document.getElementById('market-cap');
        if (marketCapEl && this.priceData.market_cap) {
            marketCapEl.textContent = this.formatLargeNumber(
                this.priceData.market_cap.usd
            );
        }

        // 24h volume
        const volumeEl = document.getElementById('volume-24h');
        if (volumeEl && this.priceData.volume_24h) {
            volumeEl.textContent = this.formatLargeNumber(
                this.priceData.volume_24h.usd
            );
        }

        // Circulating supply
        const supplyEl = document.getElementById('circulating-supply');
        if (supplyEl && this.priceData.supply) {
            supplyEl.textContent = this.formatNumber(
                this.priceData.supply.circulating
            ) + ' BTC';
        }
    }

    /**
     * Format currency display
     */
    formatCurrency(amount) {
        const symbol = this.currencySymbols[this.selectedCurrency] || '$';

        if (this.selectedCurrency === 'jpy') {
            return symbol + this.formatNumber(Math.floor(amount));
        } else {
            return symbol + this.formatNumber(amount, 2);
        }
    }

    /**
     * Format large numbers (millions, billions, trillions)
     */
    formatLargeNumber(num) {
        if (num >= 1e12) {
            return (num / 1e12).toFixed(1) + 'T';
        } else if (num >= 1e9) {
            return (num / 1e9).toFixed(1) + 'B';
        } else if (num >= 1e6) {
            return (num / 1e6).toFixed(1) + 'M';
        }
        return this.formatNumber(num, 0);
    }

    /**
     * Format regular numbers with thousands separator
     */
    formatNumber(num, decimals = 0) {
        return new Intl.NumberFormat('en-US', {
            minimumFractionDigits: decimals,
            maximumFractionDigits: decimals
        }).format(num);
    }

    /**
     * Format time for display
     */
    formatTime(date) {
        return date.toLocaleTimeString('en-US', {
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        });
    }

    /**
     * Start auto-refresh
     */
    startAutoRefresh() {
        this.autoRefreshTimer = setInterval(
            () => this.fetchData(),
            this.refreshInterval
        );
    }

    /**
     * Stop auto-refresh
     */
    stopAutoRefresh() {
        if (this.autoRefreshTimer) {
            clearInterval(this.autoRefreshTimer);
        }
    }

    /**
     * Render widget HTML
     */
    render() {
        const html = `
            <div class="price-widget card elevated">
                <div class="price-header">
                    <h2 class="price-title">Bitcoin Price</h2>
                    <div class="price-controls">
                        <select id="currency-selector" class="currency-dropdown">
                            ${this.currencies.map(c => `
                                <option value="${c}" ${c === this.selectedCurrency ? 'selected' : ''}>
                                    ${c.toUpperCase()}
                                </option>
                            `).join('')}
                        </select>
                        <button class="btn-refresh" id="btn-refresh-price" title="Refresh">
                            ⟳
                        </button>
                    </div>
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
                        <span id="market-cap" class="market-value">--</span>
                    </div>
                    <div class="market-item">
                        <label>24h Volume</label>
                        <span id="volume-24h" class="market-value">--</span>
                    </div>
                    <div class="market-item">
                        <label>Circulating Supply</label>
                        <span id="circulating-supply" class="market-value">--</span>
                    </div>
                </div>

                <div class="price-footer">
                    <small id="price-updated">Updated: --</small>
                </div>
            </div>
        `;

        const container = document.getElementById(this.containerId);
        if (container) {
            container.innerHTML = html;
            this.attachEventListeners();
        }
    }

    /**
     * Attach event listeners
     */
    attachEventListeners() {
        // Currency selector
        const currencySelector = document.getElementById('currency-selector');
        if (currencySelector) {
            currencySelector.addEventListener('change', (e) => {
                this.selectedCurrency = e.target.value;
                localStorage.setItem('preferred_currency', this.selectedCurrency);
                this.updateUI();
            });
        }

        // Refresh button
        const refreshBtn = document.getElementById('btn-refresh-price');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => {
                refreshBtn.classList.add('spinning');
                this.fetchData().finally(() => {
                    refreshBtn.classList.remove('spinning');
                });
            });
        }
    }

    /**
     * Show error message
     */
    showError(message) {
        const container = document.getElementById(this.containerId);
        if (container) {
            container.innerHTML = `
                <div class="alert alert-error">
                    <strong>Error:</strong> ${message}
                    <p style="margin-top: 0.5rem; font-size: 0.85rem;">
                        Unable to fetch Bitcoin price data.
                    </p>
                </div>
            `;
        }
    }

    /**
     * Destroy widget and cleanup
     */
    destroy() {
        this.stopAutoRefresh();
        const container = document.getElementById(this.containerId);
        if (container) {
            container.innerHTML = '';
        }
    }
}

// Auto-initialize on page load
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        const widget = new PriceWidget();
        widget.init();
    });
} else {
    const widget = new PriceWidget();
    widget.init();
}
