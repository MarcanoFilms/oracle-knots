/**
 * Oracle Knots - Portfolio Dashboard Component
 * Phase 4.2: Portfolio Value Dashboard
 *
 * Tracks total BTC across all wallets, shows fiat value in selected currency,
 * renders a historical balance chart, and displays daily P&L.
 *
 * Lazy-initialized on first Portfolio tab visit to avoid API calls at startup.
 */
class PortfolioDashboard {
    constructor(containerId = 'portfolio-dashboard-container') {
        this.containerId = containerId;
        this.snapshotData = null;
        this.historyData = null;
        this.plData = null;
        this.selectedCurrency = localStorage.getItem('preferred_currency') || 'usd';
        this.selectedDays = parseInt(localStorage.getItem('portfolio_days') || '30', 10);
        this.refreshIntervalMs = 60000;
        this._refreshTimer = null;
        this._initialized = false;

        this.CURRENCIES = ['usd', 'eur', 'gbp', 'jpy', 'cad', 'aud'];
        this.CURRENCY_SYMBOLS = { usd: '$', eur: '€', gbp: '£', jpy: '¥', cad: 'C$', aud: 'A$' };
        this.CURRENCY_LABELS = { usd: 'USD', eur: 'EUR', gbp: 'GBP', jpy: 'JPY', cad: 'CAD', aud: 'AUD' };
    }

    async init() {
        if (this._initialized) return;
        this._initialized = true;
        this._render();
        await this.fetchData();
        this._startAutoRefresh();
    }

    destroy() {
        this._stopAutoRefresh();
    }

    // ──────────────────────────────────────────────────────────
    // Data fetching
    // ──────────────────────────────────────────────────────────

    async fetchData() {
        const container = document.getElementById(this.containerId);
        if (!container) return;

        const [snapRes, histRes, plRes] = await Promise.allSettled([
            fetch(`/api/portfolio/snapshot?currency=${this.selectedCurrency}`).then(r => r.json()),
            fetch(`/api/portfolio/history?days=${this.selectedDays}&currency=${this.selectedCurrency}`).then(r => r.json()),
            fetch(`/api/portfolio/pl?currency=${this.selectedCurrency}`).then(r => r.json()),
        ]);

        if (snapRes.status === 'fulfilled') this.snapshotData = snapRes.value;
        if (histRes.status === 'fulfilled') this.historyData = histRes.value;
        if (plRes.status === 'fulfilled') this.plData = plRes.value;

        this._updateUI();
    }

    // ──────────────────────────────────────────────────────────
    // Rendering
    // ──────────────────────────────────────────────────────────

    _render() {
        const container = document.getElementById(this.containerId);
        if (!container) return;

        const currencyOptions = this.CURRENCIES
            .map(c => `<option value="${c}" ${c === this.selectedCurrency ? 'selected' : ''}>${this.CURRENCY_LABELS[c]}</option>`)
            .join('');

        container.innerHTML = `
<div class="portfolio-dashboard">

  <!-- Header -->
  <div class="portfolio-header">
    <span class="portfolio-title">Portfolio</span>
    <div class="portfolio-header-controls">
      <select class="portfolio-currency-select" id="portfolio-currency-select">
        ${currencyOptions}
      </select>
      <button class="portfolio-export-btn" id="portfolio-export-btn" title="Download CSV">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor">
          <path d="M19 9h-4V3H9v6H5l7 7 7-7zM5 18v2h14v-2H5z"/>
        </svg>
        Export CSV
      </button>
    </div>
  </div>

  <!-- Hero metrics -->
  <div class="portfolio-hero">
    <div class="portfolio-hero-tile">
      <div class="portfolio-hero-label">Total Bitcoin</div>
      <div class="portfolio-hero-value" id="portfolio-total-btc">—</div>
      <div class="portfolio-hero-sub" id="portfolio-wallet-count"></div>
    </div>
    <div class="portfolio-hero-tile">
      <div class="portfolio-hero-label" id="portfolio-value-label">Total Value</div>
      <div class="portfolio-hero-value" id="portfolio-total-value">—</div>
      <div class="portfolio-hero-sub" id="portfolio-price-sub"></div>
    </div>
    <div class="portfolio-hero-tile">
      <div class="portfolio-hero-label">24h Change</div>
      <div class="portfolio-hero-value" id="portfolio-change-24h">—</div>
      <div class="portfolio-hero-sub" id="portfolio-change-sub"></div>
    </div>
  </div>

  <!-- History chart -->
  <div class="portfolio-chart-card">
    <div class="portfolio-chart-header">
      <span class="portfolio-chart-title">Balance History</span>
      <div class="portfolio-days-toggle">
        <button class="portfolio-days-btn ${this.selectedDays === 7 ? 'active' : ''}" data-days="7">7d</button>
        <button class="portfolio-days-btn ${this.selectedDays === 30 ? 'active' : ''}" data-days="30">30d</button>
        <button class="portfolio-days-btn ${this.selectedDays === 365 ? 'active' : ''}" data-days="1y">1y</button>
      </div>
    </div>
    <div class="portfolio-chart-body">
      <div id="portfolio-chart-area" class="portfolio-chart-svg-wrap">
        <div class="portfolio-loading"><div class="portfolio-spinner"></div> Loading chart…</div>
      </div>
    </div>
  </div>

  <!-- Wallet breakdown (hidden until data arrives) -->
  <div id="portfolio-wallets-section" style="display:none">
    <div class="portfolio-wallets-label">By Wallet</div>
    <div class="portfolio-wallets-grid" id="portfolio-wallets-grid"></div>
  </div>

  <!-- P&L -->
  <div id="portfolio-pl-card" class="portfolio-pl-card direction-neutral">
    <span class="portfolio-pl-text">Loading daily change…</span>
  </div>

  <!-- Footer -->
  <div class="portfolio-footer" id="portfolio-footer"></div>

</div>`;

        // Wire up events
        container.querySelector('#portfolio-currency-select').addEventListener('change', e => {
            this.selectedCurrency = e.target.value;
            localStorage.setItem('preferred_currency', this.selectedCurrency);
            this.fetchData();
        });

        container.querySelector('#portfolio-export-btn').addEventListener('click', () => {
            this._handleExportCsv();
        });

        container.querySelectorAll('.portfolio-days-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const days = btn.dataset.days === '1y' ? 365 : parseInt(btn.dataset.days, 10);
                this.selectedDays = days;
                localStorage.setItem('portfolio_days', String(days));
                container.querySelectorAll('.portfolio-days-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                this.fetchData();
            });
        });
    }

    _updateUI() {
        this._renderHeroMetrics();
        this._renderHistoryChart();
        this._renderWalletBreakdown();
        this._renderPLCard();
        this._renderFooter();
    }

    _renderHeroMetrics() {
        const snap = this.snapshotData;
        const btcEl = document.getElementById('portfolio-total-btc');
        const valueEl = document.getElementById('portfolio-total-value');
        const valueLabelEl = document.getElementById('portfolio-value-label');
        const priceSub = document.getElementById('portfolio-price-sub');
        const changeEl = document.getElementById('portfolio-change-24h');
        const changeSub = document.getElementById('portfolio-change-sub');
        const walletCount = document.getElementById('portfolio-wallet-count');

        if (!btcEl) return;

        if (!snap || !snap.success) {
            const msg = snap ? snap.error || 'Error' : '—';
            btcEl.textContent = 'Offline';
            valueEl.textContent = '—';
            changeEl.textContent = '—';
            if (priceSub) priceSub.textContent = msg;
            return;
        }

        btcEl.textContent = this._formatBtc(snap.total_btc);
        if (walletCount) {
            walletCount.textContent = `${snap.wallet_count} wallet${snap.wallet_count !== 1 ? 's' : ''}`;
        }

        if (valueLabelEl) {
            valueLabelEl.textContent = `Total Value (${(this.selectedCurrency).toUpperCase()})`;
        }
        valueEl.textContent = this._formatCurrency(snap.total_value, this.selectedCurrency);
        if (priceSub && snap.price) {
            priceSub.textContent = `1 BTC = ${this._formatCurrency(snap.price, this.selectedCurrency)}`;
        }

        const change = snap.price_change_24h || 0;
        if (changeEl) {
            const sign = change >= 0 ? '▲' : '▼';
            changeEl.textContent = `${sign} ${Math.abs(change).toFixed(2)}%`;
            changeEl.className = `portfolio-hero-value ${change >= 0 ? 'change-up' : 'change-down'}`;
            if (changeSub) {
                changeSub.textContent = 'vs 24h ago';
            }
        }
    }

    _renderHistoryChart() {
        const area = document.getElementById('portfolio-chart-area');
        if (!area) return;

        const hist = this.historyData;

        if (!hist || !hist.success) {
            area.innerHTML = `<div class="portfolio-error">
                <div>Could not load chart data</div>
                <div class="portfolio-error-hint">${hist ? (hist.error || '') : 'Check API connection'}</div>
            </div>`;
            return;
        }

        if (!hist.has_enough_data) {
            const days = hist.days_available || 0;
            area.innerHTML = `
<div class="portfolio-empty-state">
  <div class="portfolio-empty-icon">📅</div>
  <div class="portfolio-empty-title">Your history is building up</div>
  <div class="portfolio-empty-text">Oracle Knots records your portfolio balance every day. Come back tomorrow to see your first chart.</div>
  <div class="portfolio-empty-progress">${days} of 2 days tracked</div>
</div>`;
            return;
        }

        this._drawSvgChart(area, hist.data, this.selectedCurrency, hist.min_value, hist.max_value);
    }

    _drawSvgChart(container, dataPoints, currency, minVal, maxVal) {
        const W = 600;
        const H = 160;
        const padLeft = 52;
        const padRight = 10;
        const padTop = 10;
        const padBottom = 24;
        const chartW = W - padLeft - padRight;
        const chartH = H - padTop - padBottom;

        const n = dataPoints.length;
        if (n < 2) {
            container.innerHTML = '<div class="portfolio-empty-state"><div class="portfolio-empty-icon">📅</div><div class="portfolio-empty-title">Not enough data yet</div></div>';
            return;
        }

        const range = maxVal - minVal || 1;
        const toX = i => padLeft + (i / (n - 1)) * chartW;
        const toY = v => padTop + chartH - ((v - minVal) / range) * chartH;

        const points = dataPoints.map((d, i) => `${toX(i).toFixed(1)},${toY(d.total_value).toFixed(1)}`).join(' ');

        // Close the path for gradient fill
        const fillPath = [
            `M ${toX(0).toFixed(1)} ${(padTop + chartH).toFixed(1)}`,
            ...dataPoints.map((d, i) => `L ${toX(i).toFixed(1)} ${toY(d.total_value).toFixed(1)}`),
            `L ${toX(n - 1).toFixed(1)} ${(padTop + chartH).toFixed(1)}`,
            'Z'
        ].join(' ');

        // Y-axis labels (4 ticks)
        const yLabels = [0, 0.33, 0.66, 1].map(pct => {
            const val = minVal + pct * range;
            const y = toY(val);
            return `<text x="${(padLeft - 4).toFixed(0)}" y="${y.toFixed(0)}" text-anchor="end" font-size="9" fill="currentColor" dominant-baseline="middle" opacity="0.55">${this._formatCompact(val, currency)}</text>`;
        }).join('');

        // X-axis labels (first, middle, last)
        const xIndices = [0, Math.floor((n - 1) / 2), n - 1];
        const xLabels = xIndices.map(i => {
            const d = dataPoints[i];
            return `<text x="${toX(i).toFixed(0)}" y="${(padTop + chartH + 14).toFixed(0)}" text-anchor="middle" font-size="9" fill="currentColor" opacity="0.55">${this._shortDate(d.date)}</text>`;
        }).join('');

        // Last point dot
        const lastX = toX(n - 1).toFixed(1);
        const lastY = toY(dataPoints[n - 1].total_value).toFixed(1);
        const lastVal = this._formatCurrency(dataPoints[n - 1].total_value, currency);

        const svgId = `portfolio-grad-${Date.now()}`;

        const svg = `<svg viewBox="0 0 ${W} ${H}" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="${svgId}" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="var(--accent-cyan, #00d4ff)" stop-opacity="0.25"/>
      <stop offset="100%" stop-color="var(--accent-cyan, #00d4ff)" stop-opacity="0.02"/>
    </linearGradient>
  </defs>
  <path d="${fillPath}" fill="url(#${svgId})"/>
  <polyline points="${points}" fill="none" stroke="var(--accent-cyan, #00d4ff)" stroke-width="1.5" stroke-linejoin="round"/>
  ${yLabels}
  ${xLabels}
  <circle cx="${lastX}" cy="${lastY}" r="4" fill="var(--accent-cyan, #00d4ff)" stroke="var(--bg-card, #111)" stroke-width="2">
    <title>${lastVal}</title>
  </circle>
</svg>`;

        container.innerHTML = svg;
    }

    _renderWalletBreakdown() {
        const snap = this.snapshotData;
        const section = document.getElementById('portfolio-wallets-section');
        const grid = document.getElementById('portfolio-wallets-grid');
        if (!section || !grid) return;

        if (!snap || !snap.success || !snap.wallets || snap.wallets.length <= 1) {
            section.style.display = 'none';
            return;
        }

        section.style.display = '';
        const totalBtc = snap.total_btc || 1;

        grid.innerHTML = snap.wallets.map(w => {
            const sharePct = totalBtc > 0 ? Math.round((w.btc / totalBtc) * 100) : 0;
            return `
<div class="portfolio-wallet-card">
  <div class="portfolio-wallet-name">${this._escapeHtml(w.name)}</div>
  <div class="portfolio-wallet-btc">${this._formatBtc(w.btc)}</div>
  <div class="portfolio-wallet-value">${this._formatCurrency(w.value, this.selectedCurrency)}</div>
  <div class="portfolio-wallet-share-bar-track">
    <div class="portfolio-wallet-share-bar-fill" style="width:${sharePct}%"></div>
  </div>
</div>`;
        }).join('');
    }

    _renderPLCard() {
        const card = document.getElementById('portfolio-pl-card');
        if (!card) return;

        const pl = this.plData;
        card.className = 'portfolio-pl-card direction-neutral';

        if (!pl) {
            card.innerHTML = '<span class="portfolio-pl-text">Loading daily change…</span>';
            return;
        }

        if (!pl.success) {
            if (pl.reason === 'no_history') {
                const snap = this.snapshotData;
                const todayVal = snap && snap.success ? this._formatCurrency(snap.total_value, this.selectedCurrency) : '—';
                card.innerHTML = `
<span class="portfolio-pl-text">Today is your first tracked day. Your baseline is set at <strong>${todayVal}</strong>. Check back tomorrow for P&amp;L tracking.</span>`;
            } else if (!pl.success && pl.error) {
                card.innerHTML = `<span class="portfolio-pl-text" style="color:var(--text-secondary)">${this._escapeHtml(pl.error || 'Node offline')}</span>`;
            }
            return;
        }

        const direction = pl.direction || 'neutral';
        card.className = `portfolio-pl-card direction-${direction}`;

        const changeVal = pl.change && pl.change.value != null ? pl.change.value : 0;
        const changePct = pl.change && pl.change.pct != null ? pl.change.pct : 0;
        const isUp = direction === 'up';
        const verb = isUp ? 'grew' : 'decreased';
        const absVal = this._formatCurrency(Math.abs(changeVal), this.selectedCurrency);
        const absPct = Math.abs(changePct).toFixed(2);
        const todayVal = pl.today ? this._formatCurrency(pl.today.value, this.selectedCurrency) : '—';
        const sign = isUp ? '+' : '-';

        card.innerHTML = `
<span class="portfolio-pl-text">Your portfolio ${verb} to <strong>${todayVal}</strong> since yesterday.</span>
<span class="portfolio-pl-value ${isUp ? 'positive' : 'negative'}">
  ${sign}${absVal}
  <span class="portfolio-pl-badge ${isUp ? 'up' : 'down'}">${sign}${absPct}%</span>
</span>`;
    }

    _renderFooter() {
        const footer = document.getElementById('portfolio-footer');
        if (!footer) return;

        const snap = this.snapshotData;
        const parts = [];

        if (snap && snap.updated_at) {
            const d = new Date(snap.updated_at * 1000);
            parts.push(`Updated ${d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`);
        }

        const hist = this.historyData;
        if (hist && hist.days_available != null) {
            parts.push(`${hist.days_available} day${hist.days_available !== 1 ? 's' : ''} tracked`);
        }

        footer.textContent = parts.join(' · ');
    }

    // ──────────────────────────────────────────────────────────
    // Actions
    // ──────────────────────────────────────────────────────────

    _handleExportCsv() {
        window.location.href = `/api/portfolio/export/csv?days=365`;
    }

    // ──────────────────────────────────────────────────────────
    // Auto refresh
    // ──────────────────────────────────────────────────────────

    _startAutoRefresh() {
        this._stopAutoRefresh();
        this._refreshTimer = setInterval(() => this.fetchData(), this.refreshIntervalMs);
    }

    _stopAutoRefresh() {
        if (this._refreshTimer) {
            clearInterval(this._refreshTimer);
            this._refreshTimer = null;
        }
    }

    // ──────────────────────────────────────────────────────────
    // Formatting helpers
    // ──────────────────────────────────────────────────────────

    _formatBtc(amount) {
        if (amount == null || isNaN(amount)) return '—';
        return `${(+amount).toFixed(8)} BTC`;
    }

    _formatCurrency(amount, currency) {
        if (amount == null || isNaN(amount)) return '—';
        const sym = this.CURRENCY_SYMBOLS[currency] || '$';
        if (currency === 'jpy') {
            return `${sym}${Math.floor(amount).toLocaleString()}`;
        }
        return `${sym}${(+amount).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
    }

    _formatCompact(amount, currency) {
        const sym = this.CURRENCY_SYMBOLS[currency] || '$';
        if (currency === 'jpy') {
            if (amount >= 1000000) return `${sym}${(amount / 1000000).toFixed(1)}M`;
            if (amount >= 1000) return `${sym}${(amount / 1000).toFixed(0)}k`;
            return `${sym}${Math.floor(amount)}`;
        }
        if (amount >= 1000000) return `${sym}${(amount / 1000000).toFixed(1)}M`;
        if (amount >= 1000) return `${sym}${(amount / 1000).toFixed(1)}k`;
        return `${sym}${(+amount).toFixed(0)}`;
    }

    _shortDate(dateStr) {
        if (!dateStr) return '';
        const [, m, d] = dateStr.split('-');
        return `${parseInt(m, 10)}/${parseInt(d, 10)}`;
    }

    _escapeHtml(str) {
        return String(str)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;');
    }
}
