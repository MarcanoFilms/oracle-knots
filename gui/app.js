// Oracle Knots Control Center JavaScript Application

document.addEventListener('DOMContentLoaded', () => {
    const STORAGE_KEY_ACTIVE_WALLET = 'oracle_active_wallet';

    // ----------------------------------------------------
    // Toast Notification System
    // ----------------------------------------------------
    const toastContainer = document.getElementById('toast-container');

    function showToast(message, type = 'info', duration = 4500) {
        if (!toastContainer) return;
        const icons = { success: '✓', error: '✕', info: '◉' };
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.innerHTML = `
            <span class="toast-icon">${icons[type] || icons.info}</span>
            <span class="toast-message"></span>
            <button class="toast-close" aria-label="Dismiss">&times;</button>
        `;
        toast.querySelector('.toast-message').textContent = message;
        const dismiss = () => {
            toast.classList.add('toast-exit');
            setTimeout(() => toast.remove(), 250);
        };
        toast.querySelector('.toast-close').addEventListener('click', dismiss);
        toastContainer.appendChild(toast);
        if (duration > 0) setTimeout(dismiss, duration);
    }

    // ----------------------------------------------------
    // UI Elements
    // ----------------------------------------------------
    const navItems = document.querySelectorAll('.nav-item, .mobile-nav-item:not(#mobile-more-btn), .drawer-item-btn');
    const tabPanes = document.querySelectorAll('.tab-pane');
    const currentTabTitle = document.getElementById('current-tab-title');
    
    // Status Widgets
    const widgetStatusDot = document.getElementById('widget-status-dot');
    const widgetStatusText = document.getElementById('widget-status-text');
    const widgetNetworkBadge = document.getElementById('widget-network-badge');
    const syncStatusIndicator = document.getElementById('sync-status-indicator');
    const syncStatusText = document.getElementById('sync-status-text');
    
    // Topbar
    const topbarHeight = document.getElementById('topbar-height');
    const topbarPeers = document.getElementById('topbar-peers');
    const nodeToggleBtn = document.getElementById('node-toggle-btn');
    
    // Dashboard Stats
    const dashSyncVal = document.getElementById('dash-sync-val');
    const dashSyncProgress = document.getElementById('dash-sync-progress');
    const dashSyncDesc = document.getElementById('dash-sync-desc');
    const dashPolicyVal = document.getElementById('dash-policy-val');
    const dashBip110Badge = document.getElementById('dash-bip110-badge');
    const dashMempoolCount = document.getElementById('dash-mempool-count');
    const dashMempoolBytes = document.getElementById('dash-mempool-bytes');
    const dashRejectionCount = document.getElementById('dash-rejection-count');
    const dashRejectionRate = document.getElementById('dash-rejection-rate');
    const dashRejectionDelta = document.getElementById('dash-rejection-delta');
    const dashRdtsPct = document.getElementById('dash-rdts-pct');
    const dashRdtsStatus = document.getElementById('dash-rdts-status');
    const dashRdtsBlocks = document.getElementById('dash-rdts-blocks');
    const dashPassRate = document.getElementById('dash-pass-rate');
    const dashMempoolRam = document.getElementById('dash-mempool-ram');
    const dashMinFee = document.getElementById('dash-min-fee');
    const dashMempoolLoaded = document.getElementById('dash-mempool-loaded');
    const dashboardConflictBanner = document.getElementById('dashboard-conflict-banner');
    
    // Rejections panel
    const rejectionsEmptyView = document.getElementById('rejections-empty-view');
    const rejectionsList = document.getElementById('rejections-list');
    const dashRejectionsTotal = document.getElementById('dash-rejections-total');
    const mempoolSparkline = document.getElementById('mempool-sparkline');
    const heroBlockPulse = document.getElementById('hero-block-pulse');
    const heroPeerPulse = document.getElementById('hero-peer-pulse');
    const heroPeerPrivacy = document.getElementById('hero-peer-privacy');
    const heroPolicyTitle = document.getElementById('hero-policy-title');
    const heroBip110Enforced = document.getElementById('hero-bip110-enforced');
    const heroBip110Mode = document.getElementById('hero-bip110-mode');
    const oracleHeroDesc = document.getElementById('oracle-hero-desc');
    const infoUptime = document.getElementById('info-uptime');
    const syncOwlEye = document.getElementById('sync-owl-eye');
    const balanceCard = document.querySelector('.balance-card');
    
    // Node Info
    const infoChain = document.getElementById('info-chain');
    const infoAgent = document.getElementById('info-agent');
    const infoRpc = document.getElementById('info-rpc');
    const infoDatadir = document.getElementById('info-datadir');
    
    // Policy Tab
    const profileCards = document.querySelectorAll('.profile-card');
    const btnApplyProfile = document.getElementById('btn-apply-profile');
    const policyActiveIndicator = document.getElementById('policy-active-indicator');
    
    // Config Editors (Raw mode)
    const editorPolicy = document.getElementById('editor-policy');
    const editorBitcoinConf = document.getElementById('editor-bitcoinconf');
    const btnSavePolicy = document.getElementById('btn-save-policy');
    const btnSaveBitcoinConf = document.getElementById('btn-save-bitcoinconf');
    
    // Configuration Tab (Settings redone)
    const settingsSubTabs = document.querySelectorAll('.settings-sub-tab');
    const settingsSubPanes = document.querySelectorAll('.settings-sub-pane, #settings-pane-raw');
    const btnSaveVisualSettings = document.getElementById('btn-save-visual-settings');
    const setPruneMode = document.getElementById('set-prune-mode');
    const customPruneSizeRow = document.getElementById('custom-prune-size-row');
    
    // Logs Tab
    const logText = document.getElementById('log-text');
    const logAutoscroll = document.getElementById('log-autoscroll');
    const btnRefreshLogs = document.getElementById('btn-refresh-logs');
    
    // Modals
    const nodeStartModal = document.getElementById('node-start-modal');
    const modalCloseBtn = document.getElementById('modal-close-btn');
    const modalCancelBtn = document.getElementById('modal-cancel-btn');
    const modalStartBtn = document.getElementById('modal-start-btn');
    
    // Startup Form inputs
    const startNetwork = document.getElementById('start-network');
    const startDatadir = document.getElementById('start-datadir');
    const startExtra = document.getElementById('start-extra');
    
    // Quick Actions
    const btnQuickReloadPolicy = document.getElementById('btn-quick-reload-policy');
    const btnQuickMempoolInspect = document.getElementById('btn-quick-mempool-inspect');

    // Mobile More Drawer
    const mobileMoreBtn = document.getElementById('mobile-more-btn');
    const mobileMoreDrawer = document.getElementById('mobile-more-drawer');
    const btnCloseDrawer = document.getElementById('btn-close-drawer');
    
    // ----------------------------------------------------
    // WALLET UI ELEMENTS
    // ----------------------------------------------------
    const walletNoWalletView = document.getElementById('wallet-no-wallet-view');
    const walletActiveView = document.getElementById('wallet-active-view');
    const btnCreateWallet = document.getElementById('btn-create-wallet');
    const btnLoadWalletQuick = document.getElementById('btn-load-wallet-quick');
    const newWalletNameInput = document.getElementById('new-wallet-name');
    
    const activeWalletNameLabel = document.getElementById('active-wallet-name');
    const walletBalanceBtc = document.getElementById('wallet-balance-btc');
    const walletBalanceUsd = document.getElementById('wallet-balance-usd');
    const walletBalanceUnconfirmed = document.getElementById('wallet-balance-unconfirmed');
    
    // Wallet actions sub-navigation
    const pillWalletReceive = document.getElementById('pill-wallet-receive');
    const pillWalletSend = document.getElementById('pill-wallet-send');
    const pillWalletUtxos = document.getElementById('pill-wallet-utxos');
    const pillWalletHistory = document.getElementById('pill-wallet-history');
    const pillWalletAddresses = document.getElementById('pill-wallet-addresses');
    const pillWalletTools = document.getElementById('pill-wallet-tools');

    const walletSubReceive = document.getElementById('wallet-sub-receive');
    const walletSubSend = document.getElementById('wallet-sub-send');
    const walletSubUtxos = document.getElementById('wallet-sub-utxos');
    const walletSubHistory = document.getElementById('wallet-sub-history');
    const walletSubAddresses = document.getElementById('wallet-sub-addresses');
    const walletSubTools = document.getElementById('wallet-sub-tools');

    const walletSelector = document.getElementById('wallet-selector');
    const btnWalletUnload = document.getElementById('btn-wallet-unload');
    const walletAddressesList = document.getElementById('wallet-addresses-list');
    const btnRefreshAddresses = document.getElementById('btn-refresh-addresses');

    const subpillSignMsg = document.getElementById('subpill-sign-msg');
    const subpillPsbt = document.getElementById('subpill-psbt');
    const subpillSecurity = document.getElementById('subpill-security');
    const toolPaneSignMsg = document.getElementById('tool-pane-sign-msg');
    const toolPanePsbt = document.getElementById('tool-pane-psbt');
    const toolPaneSecurity = document.getElementById('tool-pane-security');

    const encryptPassphraseInput = document.getElementById('encrypt-passphrase');
    const btnEncryptWallet = document.getElementById('btn-encrypt-wallet');
    const unlockPassphraseInput = document.getElementById('unlock-passphrase');
    const unlockTimeoutInput = document.getElementById('unlock-timeout');
    const btnUnlockWallet = document.getElementById('btn-unlock-wallet');
    const btnLockWallet = document.getElementById('btn-lock-wallet');
    const changeOldPassInput = document.getElementById('change-old-pass');
    const changeNewPassInput = document.getElementById('change-new-pass');
    const btnChangePassphrase = document.getElementById('btn-change-passphrase');
    const backupDirHint = document.getElementById('backup-dir-hint');
    const backupResult = document.getElementById('backup-result');
    const btnBackupWallet = document.getElementById('btn-backup-wallet');
    const btnDumpWallet = document.getElementById('btn-dump-wallet');
    const importWalletPathInput = document.getElementById('import-wallet-path');
    const btnImportWallet = document.getElementById('btn-import-wallet');
    const watchonlyNameInput = document.getElementById('watchonly-name');
    const btnCreateWatchonly = document.getElementById('btn-create-watchonly');
    const importDescriptorInput = document.getElementById('import-descriptor');
    const btnImportDescriptor = document.getElementById('btn-import-descriptor');

    const cliOutput = document.getElementById('cli-output');
    const cliInput = document.getElementById('cli-input');
    const cliRunBtn = document.getElementById('cli-run-btn');
    const cliClearBtn = document.getElementById('cli-clear-btn');
    const cliWalletSelect = document.getElementById('cli-wallet-select');
    const cliQuickChips = document.getElementById('cli-quick-chips');
    const msgAddressInput = document.getElementById('msg-address');
    const msgTextInput = document.getElementById('msg-text');
    const msgSignatureInput = document.getElementById('msg-signature');
    const btnSignMessage = document.getElementById('btn-sign-message');
    const btnVerifyMessage = document.getElementById('btn-verify-message');
    const psbtDataInput = document.getElementById('psbt-data');
    const btnDecodePsbt = document.getElementById('btn-decode-psbt');
    const btnSignPsbt = document.getElementById('btn-sign-psbt');
    const btnBroadcastPsbt = document.getElementById('btn-broadcast-psbt');
    const psbtResultContainer = document.getElementById('psbt-result-container');

    const btnWalletGotoSend = document.getElementById('btn-wallet-goto-send');
    const btnWalletGotoReceive = document.getElementById('btn-wallet-goto-receive');
    
    // Wallet Receive pane
    const receiveAddressType = document.getElementById('receive-address-type');
    const btnGenerateAddress = document.getElementById('btn-generate-address');
    const receiveAddressContainer = document.getElementById('receive-address-container');
    const qrCodeContainer = document.getElementById('qr-code-container');
    const receiveAddressText = document.getElementById('receive-address-text');
    const btnCopyAddress = document.getElementById('btn-copy-address');
    
    // Wallet Send pane
    const sendModeSimple = document.getElementById('send-mode-simple');
    const sendModeAdvanced = document.getElementById('send-mode-advanced');
    const sendSimplePane = document.getElementById('send-simple-pane');
    const sendAdvancedPane = document.getElementById('send-advanced-pane');
    const sendAddressInput = document.getElementById('send-address');
    const sendAmountInput = document.getElementById('send-amount');
    const sendFeeRateInput = document.getElementById('send-fee-rate');
    const sendFeeHint = document.getElementById('send-fee-hint');
    const btnSendCoins = document.getElementById('btn-send-coins');
    const sendAdvAddressInput = document.getElementById('send-adv-address');
    const sendAdvAmountInput = document.getElementById('send-adv-amount');
    const sendAdvFeeRateInput = document.getElementById('send-adv-fee-rate');
    const sendUtxoList = document.getElementById('send-utxo-list');
    const sendUtxoSelectAll = document.getElementById('send-utxo-select-all');
    const sendSelectedCount = document.getElementById('send-selected-count');
    const sendSelectedTotal = document.getElementById('send-selected-total');
    const btnSendAdvanced = document.getElementById('btn-send-advanced');

    // Wallet UTXOs pane
    const walletUtxoList = document.getElementById('wallet-utxo-list');
    const btnRefreshUtxos = document.getElementById('btn-refresh-utxos');
    const utxoSelectAll = document.getElementById('utxo-select-all');
    const utxoTotalCount = document.getElementById('utxo-total-count');
    const utxoTotalBtc = document.getElementById('utxo-total-btc');
    const utxoLockedCount = document.getElementById('utxo-locked-count');
    const btnLockSelectedUtxos = document.getElementById('btn-lock-selected-utxos');
    const btnUnlockSelectedUtxos = document.getElementById('btn-unlock-selected-utxos');
    const btnUtxoGotoSend = document.getElementById('btn-utxo-goto-send');

    // Wallet History pane
    const walletTxList = document.getElementById('wallet-tx-list');
    
    // ----------------------------------------------------
    // State Variables
    // ----------------------------------------------------
    let isNodeRunning = false;
    let selectedPolicyProfile = 'maximalist';
    let currentActiveTab = 'dashboard';
    let updateIntervalId = null;
    let logIntervalId = null;
    let walletIntervalId = null;
    
    let activeWalletName = '';
    let loadedWallets = [];
    let currentPsbt = '';
    let cachedUtxos = [];
    let selectedUtxoKeys = new Set();
    let cliHistory = [];
    let cliHistoryIndex = -1;
    let mempoolHistory = [];
    let lastBlockHeight = 0;
    const MEMPOOL_HISTORY_MAX = 40;
    let btcPriceUsd = 93500;
    let lastPolicyStatus = null;
    let logFilterMode = 'all';

    const REJECTION_LABELS = {
        'inscription': 'Ordinals inscriptions',
        'tokens-runes': 'Runes / BRC-20 tokens',
        'tokens-olga': 'OLGA tokens',
        'dust-nonanchor': 'Dust (non-anchor)',
        'dust-nonzero': 'Dust (non-zero)',
        'bare-pubkey': 'Bare pubkey outputs',
        'bare-multisig': 'Bare multisig outputs',
        'parasite-cat21': 'Parasite CAT-21 overlays',
        'max-op-returns': 'Excess OP_RETURN outputs',
    };

    const POLICY_PRESETS = {
        'maximalist': { reject_tokens: true, reject_inscriptions: true, datacarrier_size: 0, max_op_return_outputs: 0, dust_relay_fee: 3000, permit_bare_multisig: false, reject_parasites: true },
        'bip110-strict': { reject_tokens: true, reject_inscriptions: true, datacarrier_size: 83, max_op_return_outputs: 1, dust_relay_fee: 3000, permit_bare_multisig: false, reject_parasites: true },
        'monetary-only': { reject_tokens: true, reject_inscriptions: true, datacarrier_size: 0, max_op_return_outputs: 0, dust_relay_fee: 3000, permit_bare_multisig: false, reject_parasites: true },
        'default-knots': { reject_tokens: false, reject_inscriptions: false, datacarrier_size: 83, max_op_return_outputs: 1, dust_relay_fee: 3000, permit_bare_multisig: false, reject_parasites: true },
    };

    function drawMempoolSparkline() {
        if (!mempoolSparkline || mempoolHistory.length < 2) return;
        const canvas = mempoolSparkline;
        const ctx = canvas.getContext('2d');
        const w = canvas.width;
        const h = canvas.height;
        const data = mempoolHistory;
        const max = Math.max(...data, 1);
        const min = Math.min(...data, 0);
        const range = max - min || 1;

        ctx.clearRect(0, 0, w, h);
        ctx.beginPath();
        data.forEach((val, i) => {
            const x = (i / (data.length - 1)) * (w - 4) + 2;
            const y = h - 4 - ((val - min) / range) * (h - 8);
            if (i === 0) ctx.moveTo(x, y);
            else ctx.lineTo(x, y);
        });
        const grad = ctx.createLinearGradient(0, 0, w, 0);
        grad.addColorStop(0, 'rgba(0, 240, 255, 0.9)');
        grad.addColorStop(1, 'rgba(189, 94, 255, 0.9)');
        ctx.strokeStyle = grad;
        ctx.lineWidth = 2;
        ctx.stroke();

        ctx.lineTo(w - 2, h - 2);
        ctx.lineTo(2, h - 2);
        ctx.closePath();
        const fillGrad = ctx.createLinearGradient(0, 0, 0, h);
        fillGrad.addColorStop(0, 'rgba(0, 240, 255, 0.15)');
        fillGrad.addColorStop(1, 'rgba(0, 240, 255, 0)');
        ctx.fillStyle = fillGrad;
        ctx.fill();
    }

    function pulseHeroBlock(height) {
        if (!heroBlockPulse) return;
        heroBlockPulse.textContent = `Block ${height.toLocaleString()}`;
        if (height !== lastBlockHeight && lastBlockHeight > 0) {
            heroBlockPulse.classList.remove('pulse-block');
            void heroBlockPulse.offsetWidth;
            heroBlockPulse.classList.add('pulse-block');
        }
        lastBlockHeight = height;
    }

    function utxoKey(utxo) {
        return `${utxo.txid}:${utxo.vout}`;
    }

    function getSelectedUtxoInputs() {
        return cachedUtxos
            .filter(u => selectedUtxoKeys.has(utxoKey(u)))
            .map(u => ({ txid: u.txid, vout: u.vout }));
    }

    function updateUtxoSelectionSummary() {
        const selected = cachedUtxos.filter(u => selectedUtxoKeys.has(utxoKey(u)));
        const total = selected.reduce((sum, u) => sum + u.amount, 0);
        if (sendSelectedCount) sendSelectedCount.textContent = `${selected.length} UTXO${selected.length !== 1 ? 's' : ''} selected`;
        if (sendSelectedTotal) sendSelectedTotal.textContent = `${total.toFixed(8)} BTC`;
    }
    
    // ----------------------------------------------------
    // Tab Navigation Logic
    // ----------------------------------------------------
    navItems.forEach(item => {
        item.addEventListener('click', () => {
            const tabId = item.getAttribute('data-tab');
            switchTab(tabId);
            closeDrawerMenu();
        });
    });
    
    function switchTab(tabId) {
        currentActiveTab = tabId;
        
        // Update Sidebar/Bottombar Nav Menu UI
        document.querySelectorAll('.nav-item, .mobile-nav-item').forEach(btn => {
            if (btn.getAttribute('data-tab') === tabId) {
                btn.classList.add('active');
            } else {
                btn.classList.remove('active');
            }
        });
        
        // Show selected tab pane
        tabPanes.forEach(pane => {
            if (pane.id === `tab-${tabId}`) {
                pane.classList.add('active');
            } else {
                pane.classList.remove('active');
            }
        });
        
        // Update header title
        const niceTitle = tabId.charAt(0).toUpperCase() + tabId.slice(1);
        const titles = {
            bip110: 'BIP-110 Status',
            config: 'Configuration',
            wallet: 'Wallet Manager',
            cli: 'Oracle CLI',
            logs: 'Console Logs',
        };
        currentTabTitle.textContent = titles[tabId] || niceTitle;
        
        // Handle specific tab actions
        if (tabId === 'config') {
            loadConfigFiles();
            loadParsedSettings();
        } else if (tabId === 'logs') {
            fetchLogs();
            startLogPolling();
        } else {
            stopLogPolling();
        }

        if (tabId === 'wallet') {
            startWalletPolling();
        } else {
            stopWalletPolling();
        }

        if (tabId === 'cli') {
            populateCliWalletSelect();
            if (cliInput) cliInput.focus();
        }

        if (tabId === 'dashboard' && isNodeRunning) {
            fetchDashboard();
        } else if (tabId === 'peers' && isNodeRunning) {
            fetchPeers();
        } else if (tabId === 'bip110' && isNodeRunning) {
            fetchBip110Status();
        }
    }
    
    // Mobile More Drawer Toggle
    mobileMoreBtn.addEventListener('click', () => {
        mobileMoreDrawer.classList.remove('hidden');
    });
    
    btnCloseDrawer.addEventListener('click', closeDrawerMenu);
    mobileMoreDrawer.addEventListener('click', (e) => {
        if (e.target === mobileMoreDrawer) closeDrawerMenu();
    });
    
    function closeDrawerMenu() {
        mobileMoreDrawer.classList.add('hidden');
    }
    
    // ----------------------------------------------------
    // Node Status Polling & Metrics
    // ----------------------------------------------------
    function startMetricsPolling() {
        updateNodeInfo();
        fetchBtcPrice();
        if (updateIntervalId) clearInterval(updateIntervalId);
        updateIntervalId = setInterval(updateNodeInfo, 2000);
    }
    
    async function updateNodeInfo() {
        try {
            const response = await fetch('/api/status');
            const status = await response.json();
            
            isNodeRunning = status.running;
            
            // Update Start/Stop button
            if (isNodeRunning) {
                nodeToggleBtn.textContent = 'Stop Node';
                nodeToggleBtn.className = 'btn btn-outline';
                
                widgetStatusDot.className = 'status-dot online';
                widgetStatusText.textContent = 'Node Online';
                widgetStatusText.title = `PID: ${status.pid}`;
                
                widgetNetworkBadge.textContent = status.network.toUpperCase();
                infoChain.textContent = status.network;
                infoDatadir.textContent = status.datadir;
                infoRpc.textContent = `127.0.0.1:${status.network === 'mainnet' ? '8332' : (status.network === 'testnet' ? '18332' : '18443')}`;
                
                fetchDashboard();
                
                if (currentActiveTab === 'peers') {
                    fetchPeers();
                }
                if (currentActiveTab === 'bip110') {
                    fetchBip110Status();
                }
            } else {
                nodeToggleBtn.textContent = 'Start Node';
                nodeToggleBtn.className = 'btn btn-primary';
                
                widgetStatusDot.className = 'status-dot offline';
                widgetStatusText.textContent = 'Node Offline';
                
                syncStatusIndicator.className = 'pulse-indicator';
                syncStatusText.textContent = 'Disconnected';
                
                topbarHeight.textContent = 'Block: 0';
                topbarPeers.textContent = 'Peers: 0';
                
                resetStatsToOffline();
            }
        } catch (err) {
            console.error('Failed to connect to backend server:', err);
            widgetStatusDot.className = 'status-dot offline';
            widgetStatusText.textContent = 'API Error';
            syncStatusText.textContent = 'Offline';
        }
    }
    
    async function fetchDashboard() {
        try {
            const res = await fetch('/api/dashboard');
            if (!res.ok) return;
            renderDashboard(await res.json());
        } catch (err) {
            console.error('Error fetching dashboard:', err);
        }
    }

    function renderDashboard(data) {
        if (!data.online) return;

        const blockHeight = data.metrics?.block_height || data.sync?.blocks || 0;
        const peers = data.peers?.total ?? data.network?.connections ?? 0;

        topbarHeight.textContent = `Block: ${blockHeight}`;
        topbarPeers.textContent = `Peers: ${peers}`;
        pulseHeroBlock(blockHeight);

        const policy = data.policy || {};
        const profile = policy.profile || 'unknown';
        const bip110Mode = (policy.bip110_mode || 'unknown').toUpperCase();
        const enforced = policy.bip110_enforced;

        if (heroPolicyTitle) heroPolicyTitle.textContent = `Policy: ${profile}`;
        if (heroBip110Mode) heroBip110Mode.textContent = `Mode: ${bip110Mode}`;
        if (heroBip110Enforced) {
            heroBip110Enforced.textContent = enforced ? 'ENFORCED' : 'NOT ENFORCED';
            heroBip110Enforced.className = enforced ? 'badge badge-success' : 'badge badge-outline';
        }
        if (heroPeerPulse) heroPeerPulse.textContent = `${peers} peers watching`;
        if (heroPeerPrivacy) {
            heroPeerPrivacy.textContent = `Tor ${data.peers?.tor || 0} · I2P ${data.peers?.i2p || 0} · Clear ${data.peers?.clearnet || 0}`;
        }

        const syncPct = data.sync?.progress_pct ?? 0;
        dashSyncVal.textContent = `${syncPct.toFixed(2)}%`;
        dashSyncProgress.style.width = `${syncPct}%`;
        if (syncPct >= 99.9) {
            syncStatusIndicator.className = 'pulse-indicator active';
            syncStatusText.textContent = 'Synced';
            dashSyncDesc.textContent = `Fully synced at block #${blockHeight}`;
            if (syncOwlEye) {
                syncOwlEye.classList.remove('hidden');
                syncOwlEye.classList.add('owl-watching');
            }
            if (oracleHeroDesc) oracleHeroDesc.textContent = 'The Oracle sees all — chain fully verified, mempool under watch.';
        } else {
            syncStatusIndicator.className = 'pulse-indicator syncing';
            syncStatusText.textContent = 'Syncing...';
            dashSyncDesc.textContent = `Syncing blockchain... (${data.sync?.blocks || 0} / ${data.sync?.headers || 0})`;
            widgetStatusDot.className = 'status-dot syncing';
            if (syncOwlEye) syncOwlEye.classList.remove('hidden', 'owl-watching');
            if (oracleHeroDesc) oracleHeroDesc.textContent = `Opening its eyes on the chain… ${syncPct.toFixed(1)}% synchronized.`;
        }

        dashPolicyVal.textContent = profile;
        dashBip110Badge.textContent = `BIP-110: ${bip110Mode}`;
        policyActiveIndicator.innerHTML = `Current profile: <strong style="color: var(--accent-cyan)">${profile}</strong>`;
        highlightActiveProfileCard(profile);

        const mempool = data.mempool || {};
        dashMempoolCount.textContent = mempool.size ?? 0;
        mempoolHistory.push(mempool.size ?? 0);
        if (mempoolHistory.length > MEMPOOL_HISTORY_MAX) mempoolHistory.shift();
        drawMempoolSparkline();
        const mBytes = ((mempool.bytes || 0) / 1024).toFixed(1);
        const mUsage = ((mempool.usage || 0) / (1024 * 1024)).toFixed(1);
        const maxMb = ((mempool.maxmempool || 0) / (1024 * 1024)).toFixed(0);
        dashMempoolBytes.textContent = `${mBytes} KB · ${mUsage}/${maxMb} MB RAM (${mempool.usage_pct || 0}%)`;

        const rej = data.rejections || {};
        const stats = rej.stats || {};
        if (dashRejectionCount) dashRejectionCount.textContent = stats.total ?? 0;
        if (dashRejectionRate) dashRejectionRate.textContent = `${stats.rate_pct ?? 0}% rejection rate (since startup)`;
        if (dashRejectionDelta) {
            const d = rej.deltas || {};
            dashRejectionDelta.textContent = `+${d.today ?? 0} today · +${d.session ?? 0} session`;
        }
        if (dashPassRate) dashPassRate.textContent = `${stats.pass_rate_pct ?? 100}% pass rate`;
        if (dashMempoolRam) dashMempoolRam.textContent = `${mUsage} / ${maxMb} MB`;
        if (dashMinFee) dashMinFee.textContent = mempool.mempoolminfee != null ? String(mempool.mempoolminfee) : '—';
        if (dashMempoolLoaded) dashMempoolLoaded.textContent = mempool.loaded ? 'Yes' : 'No';

        const rdts = data.rdts || {};
        if (dashRdtsPct) dashRdtsPct.textContent = `${rdts.signaling_pct ?? 0}%`;
        if (dashRdtsStatus) dashRdtsStatus.textContent = `Status: ${rdts.status || 'unknown'}`;
        if (dashRdtsBlocks) dashRdtsBlocks.textContent = `${rdts.blocks_signaling || 0} / ${rdts.period || 0} blocks signaling`;

        updateRejectionsPanel(rej.top || [], stats.total || 0);

        lastPolicyStatus = policy;
        updateRulesListFromStatus(policy);

        if (data.network?.subversion) infoAgent.textContent = data.network.subversion;
        if (data.sync?.chain) infoChain.textContent = data.sync.chain;
        if (infoUptime && data.metrics?.uptime) infoUptime.textContent = formatUptime(data.metrics.uptime);
        const ramModeEl = document.getElementById('info-ram-mode');
        if (ramModeEl) ramModeEl.textContent = `${maxMb} MB max mempool`;

        if (dashboardConflictBanner) {
            if (data.conflict) {
                dashboardConflictBanner.textContent = `Policy conflict: policy.toml uses "${data.conflict.toml_profile}" but bitcoin.conf has policyprofile=${data.conflict.conf_profile} (CLI overrides TOML on restart).`;
                dashboardConflictBanner.classList.remove('hidden');
            } else {
                dashboardConflictBanner.classList.add('hidden');
            }
        }

        renderSovereignMining(data.mining || {}, data.rdts || {});
        renderPreflightStrip(data.preflight || {});
        renderMempoolAuditSummary(data.mempool_audit || {});
    }

    function renderSovereignMining(mining, rdts) {
        const profile = mining.profile || mining.active_policy_profile || '—';
        const badge = document.getElementById('mining-profile-badge');
        if (badge) badge.textContent = `Profile: ${profile}`;

        const set = (id, val) => { const el = document.getElementById(id); if (el) el.textContent = val; };
        set('mining-txs-included', mining.txs_included ?? mining.currentblocktx ?? '—');
        set('mining-policy-filtered', mining.policy_filtered ?? '0');
        const rate = mining.template_filter_rate_pct;
        set('mining-filter-rate', rate != null ? `${Number(rate).toFixed(1)}%` : '—');
        const fees = mining.fees ?? mining.currentblockfees;
        set('mining-fees', fees != null ? `${fees} sats` : '—');

        const fill = document.getElementById('rdts-progress-fill');
        const marker = document.getElementById('rdts-threshold-marker');
        const desc = document.getElementById('rdts-progress-desc');
        const activeBadge = document.getElementById('rdts-active-badge');
        const sigPct = rdts.signaling_pct ?? 0;
        const threshPct = rdts.threshold_pct ?? 55;
        if (fill) fill.style.width = `${Math.min(100, sigPct)}%`;
        if (marker) marker.style.left = `${Math.min(100, threshPct)}%`;
        if (activeBadge) {
            activeBadge.textContent = rdts.active ? 'ACTIVE' : (rdts.status || 'unknown').toUpperCase();
            activeBadge.className = rdts.active ? 'badge badge-success' : 'badge badge-outline';
        }
        if (desc) {
            const blocks = rdts.blocks_signaling ?? 0;
            const period = rdts.period ?? 0;
            const threshold = rdts.threshold ?? 0;
            const toGo = rdts.blocks_to_threshold ?? Math.max(0, threshold - blocks);
            desc.textContent = `${blocks}/${period} blocks signaling (${sigPct}%) · need ${threshold} for lock-in · ${toGo} blocks to threshold · status: ${rdts.status || 'unknown'}`;
        }
    }

    function renderPreflightStrip(preflight) {
        const strip = document.getElementById('dashboard-preflight-strip');
        if (!strip || !preflight.checks) return;
        const warnings = preflight.checks.filter(c => c.severity === 'warning' || c.severity === 'critical');
        if (warnings.length === 0) {
            strip.classList.add('hidden');
            return;
        }
        strip.classList.remove('hidden');
        strip.innerHTML = warnings.slice(0, 3).map(c =>
            `<strong>${c.severity}:</strong> ${c.message}${c.recommendation ? ` — ${c.recommendation}` : ''}`
        ).join('<br>');
    }

    function renderMempoolAuditSummary(audit) {
        if (!audit || !audit.scanned) return;
        window._lastMempoolAudit = audit;
    }

    function openMempoolPolicyModal() {
        const modal = document.getElementById('mempool-policy-modal');
        const audit = window._lastMempoolAudit;
        if (!modal) return;
        modal.classList.remove('hidden');

        const set = (id, val) => { const el = document.getElementById(id); if (el) el.textContent = val; };
        if (!audit || audit.scanned === undefined) {
            set('audit-pass', '—');
            set('audit-fail', '—');
            set('audit-pass-rate', 'Start node / rebuild');
            set('audit-scanned', '—');
            return;
        }
        set('audit-pass', audit.would_pass ?? 0);
        set('audit-fail', audit.would_fail ?? 0);
        set('audit-pass-rate', `${(audit.pass_rate_pct ?? 0).toFixed(1)}%`);
        set('audit-scanned', `${audit.scanned} / ${audit.mempool_total ?? audit.scanned}`);

        const failBox = document.getElementById('mempool-audit-failures');
        if (failBox && audit.failures_by_reason) {
            failBox.innerHTML = '<h4 class="text-sm mb-2">Failures by reason</h4>';
            Object.entries(audit.failures_by_reason).sort((a, b) => b[1] - a[1]).forEach(([reason, count]) => {
                const label = REJECTION_LABELS[reason] || reason;
                failBox.innerHTML += `<div class="rejection-bar-row"><div class="rejection-bar-header"><span>${label}</span><span>${count}</span></div></div>`;
            });
        }
        const sampleBox = document.getElementById('mempool-audit-samples');
        if (sampleBox && audit.sample_failures) {
            sampleBox.innerHTML = '<h4 class="text-sm mb-2 mt-3">Sample failures</h4>';
            audit.sample_failures.forEach(s => {
                sampleBox.innerHTML += `<p class="text-xs font-mono text-secondary">${s.message} · ${s.txid?.slice(0, 16)}…</p>`;
            });
        }
    }

    async function fetchPeers() {
        try {
            const res = await fetch('/api/rpc/getpeerinfo');
            const data = await res.json();
            const tbody = document.getElementById('peers-table-body');
            const peersBadge = document.getElementById('peers-count-badge');
            
            if (data.success) {
                const peers = JSON.parse(data.output);
                peersBadge.textContent = `${peers.length} Peers`;
                
                if (peers.length === 0) {
                    tbody.innerHTML = `<tr><td colspan="6" class="text-center text-secondary py-4">No peers connected.</td></tr>`;
                    return;
                }
                
                tbody.innerHTML = '';
                peers.forEach(peer => {
                    const row = document.createElement('tr');
                    const dir = peer.inbound ? 'Inbound' : 'Outbound';
                    const ping = peer.pingtime ? `${Math.round(peer.pingtime * 1000)} ms` : 'N/A';
                    
                    row.innerHTML = `
                        <td class="font-mono">${peer.id}</td>
                        <td class="font-mono">${peer.addr}</td>
                        <td>${peer.subver}</td>
                        <td><span class="badge ${peer.inbound ? 'badge-outline' : 'badge-primary'}">${dir}</span></td>
                        <td>${peer.synced_blocks}</td>
                        <td class="font-mono">${ping}</td>
                    `;
                    tbody.appendChild(row);
                });
            } else {
                tbody.innerHTML = `<tr><td colspan="6" class="text-center text-secondary py-4">Error loading peers: ${data.output}</td></tr>`;
            }
        } catch (err) {
            console.error(err);
        }
    }

    async function fetchBip110Status() {
        try {
            const res = await fetch('/api/rpc/checkbip110status');
            const data = await res.json();
            const logBox = document.getElementById('bip110-audit-log');
            const complianceStatus = document.getElementById('bip110-compliance-status');
            const modeTitle = document.getElementById('bip110-mode-title');
            const profileLine = document.getElementById('bip110-profile-line');

            if (!data.success) {
                logBox.innerHTML = `<p class="text-danger">Failed to retrieve BIP-110 status: ${data.output}</p>`;
                return;
            }

            const status = JSON.parse(data.output);
            const enforced = status.bip110_enforced;
            complianceStatus.textContent = enforced ? 'Enforced: YES' : 'Enforced: NO';
            complianceStatus.className = enforced ? 'badge badge-success' : 'badge badge-outline';
            modeTitle.textContent = `Mode: ${(status.bip110_mode || 'unknown').toUpperCase()}`;
            if (profileLine) profileLine.textContent = `Profile: ${status.active_policy_profile || 'unknown'}`;

            lastPolicyStatus = status;
            updateRulesListFromStatus(status);

            const reasons = status.rejections_by_reason || {};
            logBox.innerHTML = '';
            const entries = Object.entries(reasons).filter(([k]) => k !== 'total').sort((a, b) => b[1] - a[1]);
            if (entries.length === 0) {
                logBox.innerHTML = '<p class="text-secondary">No policy rejections recorded since startup.</p>';
            } else {
                entries.forEach(([reason, count]) => {
                    const p = document.createElement('p');
                    p.className = 'log-warning';
                    const label = REJECTION_LABELS[reason] || reason;
                    p.textContent = `${label}: ${count}`;
                    logBox.appendChild(p);
                });
                const total = reasons.total ?? entries.reduce((s, [, c]) => s + c, 0);
                const totalP = document.createElement('p');
                totalP.className = 'log-success';
                totalP.textContent = `Total rejected: ${total}`;
                logBox.appendChild(totalP);
            }
        } catch (err) {
            console.error(err);
        }
    }

    function setRuleVal(el, text, blocking) {
        if (!el) return;
        el.textContent = text;
        el.className = 'rule-status-val';
        if (blocking === true) el.classList.add('status-yes');
        else if (blocking === false) el.classList.add('status-no');
    }

    function updateRulesListFromStatus(status) {
        if (!status) return;
        const profile = status.active_policy_profile || status.profile;
        const preset = POLICY_PRESETS[profile];
        const rules = preset || {
            reject_tokens: status.reject_tokens,
            reject_inscriptions: status.reject_inscriptions,
            datacarrier_size: status.datacarrier_size,
            max_op_return_outputs: status.max_op_return_outputs,
            dust_relay_fee: status.dust_relay_fee,
            permit_bare_multisig: status.permit_bare_multisig,
            reject_parasites: status.reject_parasites,
        };

        const ri = status.reject_inscriptions ?? rules.reject_inscriptions;
        const mopr = status.max_op_return_outputs ?? rules.max_op_return_outputs;

        setRuleVal(document.getElementById('rule-val-reject_tokens'),
            rules.reject_tokens ? 'TRUE (BLOCK)' : 'FALSE (RELAY)', rules.reject_tokens);
        setRuleVal(document.getElementById('rule-val-reject_inscriptions'),
            ri ? 'TRUE (BLOCK)' : 'FALSE (RELAY)', ri);
        setRuleVal(document.getElementById('rule-val-datacarrier_size'),
            `${rules.datacarrier_size ?? 0} bytes`, rules.datacarrier_size === 0);
        setRuleVal(document.getElementById('rule-val-max_op_return_outputs'), String(mopr ?? '—'), null);
        setRuleVal(document.getElementById('rule-val-dust_relay_fee'),
            `${rules.dust_relay_fee ?? 3000} sat/kvb`, null);
        setRuleVal(document.getElementById('rule-val-permit_bare_multisig'),
            rules.permit_bare_multisig ? 'TRUE' : 'FALSE', !rules.permit_bare_multisig);
        setRuleVal(document.getElementById('rule-val-reject_parasites'),
            rules.reject_parasites ? 'TRUE' : 'FALSE', rules.reject_parasites);
    }
    
    function resetStatsToOffline() {
        dashSyncVal.textContent = '0.00%';
        dashSyncProgress.style.width = '0%';
        dashSyncDesc.textContent = 'Node is stopped';
        
        dashPolicyVal.textContent = 'None';
        dashBip110Badge.textContent = 'BIP-110: Unknown';
        policyActiveIndicator.innerHTML = 'Current profile: <strong>Offline</strong>';
        
        dashMempoolCount.textContent = '0';
        dashMempoolBytes.textContent = '0 KB / 0 MB limit';
        if (dashRejectionCount) dashRejectionCount.textContent = '0';
        if (dashRejectionRate) dashRejectionRate.textContent = '0% rejection rate';
        if (dashRdtsPct) dashRdtsPct.textContent = '0%';
        if (heroPolicyTitle) heroPolicyTitle.textContent = 'Policy: —';
        if (heroBip110Enforced) heroBip110Enforced.textContent = 'BIP-110: —';
        if (infoUptime) infoUptime.textContent = '—';
        
        dashRejectionsTotal.textContent = '0 Rejected';
        dashRejectionsTotal.className = 'badge badge-outline';
        
        rejectionsEmptyView.classList.remove('hidden');
        rejectionsList.classList.add('hidden');
        
        infoChain.textContent = 'Unknown';
        infoAgent.textContent = 'Unknown';
        
        const tbody = document.getElementById('peers-table-body');
        if (tbody) tbody.innerHTML = `<tr><td colspan="6" class="text-center text-secondary py-4">No peers connected. Start the node to connect.</td></tr>`;
        
        const auditLog = document.getElementById('bip110-audit-log');
        if (auditLog) auditLog.innerHTML = `<p class="text-secondary text-center py-4">Start the node to view live BIP-110 and policy rejection stats.</p>`;
        
        document.querySelectorAll('.rule-status-val').forEach(el => {
            el.textContent = 'Offline';
            el.className = 'rule-status-val';
        });
        if (dashboardConflictBanner) dashboardConflictBanner.classList.add('hidden');
    }
    
    function updateRejectionsPanel(topItems, total) {
        if (!topItems || topItems.length === 0) {
            rejectionsEmptyView.classList.remove('hidden');
            rejectionsList.classList.add('hidden');
            dashRejectionsTotal.textContent = '0 Rejected';
            dashRejectionsTotal.className = 'badge badge-outline';
            return;
        }

        rejectionsEmptyView.classList.add('hidden');
        rejectionsList.classList.remove('hidden');
        rejectionsList.innerHTML = '';

        const maxCount = topItems[0]?.count || 1;
        topItems.forEach(item => {
            const row = document.createElement('div');
            row.className = 'rejection-bar-row';
            const pctBar = Math.round((item.count / maxCount) * 100);
            row.innerHTML = `
                <div class="rejection-bar-header">
                    <span>${item.label}</span>
                    <span class="font-mono">${item.count} (${item.pct}%)</span>
                </div>
                <div class="rejection-bar-track">
                    <div class="rejection-bar-fill" style="width: ${pctBar}%"></div>
                </div>
            `;
            rejectionsList.appendChild(row);
        });

        dashRejectionsTotal.textContent = `${total} Rejected`;
        dashRejectionsTotal.className = total > 0 ? 'badge badge-danger' : 'badge badge-outline';
    }
    
    function formatUptime(seconds) {
        if (!seconds) return '0m';
        const d = Math.floor(seconds / (3600*24));
        const h = Math.floor((seconds % (3600*24)) / 3600);
        const m = Math.floor((seconds % 3600) / 60);
        
        let res = '';
        if (d > 0) res += `${d}d `;
        if (h > 0 || d > 0) res += `${h}h `;
        res += `${m}m`;
        return res;
    }
    
    async function fetchBtcPrice() {
        try {
            const res = await fetch('https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd');
            const data = await res.json();
            if (data.bitcoin && data.bitcoin.usd) {
                btcPriceUsd = data.bitcoin.usd;
            }
        } catch (e) {
            console.log("CoinGecko offline, using simulated BTC price of $93,500");
        }
    }
    
    // ----------------------------------------------------
    // Node Start/Stop Operations
    // ----------------------------------------------------
    nodeToggleBtn.addEventListener('click', () => {
        if (isNodeRunning) {
            stopNodeProcess();
        } else {
            showStartModal();
        }
    });
    
    function showStartModal() {
        nodeStartModal.classList.remove('hidden');
    }
    
    function hideStartModal() {
        nodeStartModal.classList.add('hidden');
    }
    
    modalCloseBtn.addEventListener('click', hideStartModal);
    modalCancelBtn.addEventListener('click', hideStartModal);
    
    modalStartBtn.addEventListener('click', async () => {
        hideStartModal();
        
        const network = startNetwork.value;
        const datadir = startDatadir.value.trim();
        const extra = startExtra.value.trim();
        
        try {
            widgetStatusDot.className = 'status-dot syncing';
            widgetStatusText.textContent = 'Starting Node...';
            
            const res = await fetch('/api/start', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ network, datadir, extra_args: extra })
            });
            const data = await res.json();
            if (data.success) {
                console.log('Node started successfully', data);
                setTimeout(updateNodeInfo, 1000);
            } else {
                alert(`Error starting node: ${data.error}`);
                updateNodeInfo();
            }
        } catch (err) {
            alert(`API error starting node: ${err.message}`);
            updateNodeInfo();
        }
    });
    
    async function stopNodeProcess() {
        if (!confirm('Are you sure you want to stop the Oracle Knots node?')) return;
        
        try {
            widgetStatusDot.className = 'status-dot syncing';
            widgetStatusText.textContent = 'Stopping Node...';
            
            const res = await fetch('/api/stop', { method: 'POST' });
            const data = await res.json();
            if (data.success) {
                console.log('Node stopped successfully');
                setTimeout(updateNodeInfo, 1500);
            } else {
                alert(`Error stopping node: ${data.error}`);
                updateNodeInfo();
            }
        } catch (err) {
            alert(`API error stopping node: ${err.message}`);
            updateNodeInfo();
        }
    }
    
    // ----------------------------------------------------
    // Policy Engine Profile Switcher
    // ----------------------------------------------------
    profileCards.forEach(card => {
        card.addEventListener('click', () => {
            profileCards.forEach(c => c.classList.remove('selected'));
            card.classList.add('selected');
            selectedPolicyProfile = card.getAttribute('data-profile');
        });
    });
    
    function highlightActiveProfileCard(profile) {
        profileCards.forEach(card => {
            if (card.getAttribute('data-profile') === profile) {
                card.classList.add('selected');
            } else {
                card.classList.remove('selected');
            }
        });
    }
    
    btnApplyProfile.addEventListener('click', async () => {
        if (!isNodeRunning) {
            showToast('Start the node before applying a profile.', 'error');
            return;
        }
        
        try {
            btnApplyProfile.disabled = true;
            btnApplyProfile.textContent = 'Applying...';
            
            const res = await fetch('/api/rpc/set-policy', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ profile: selectedPolicyProfile })
            });
            const data = await res.json();
            
            if (data.success) {
                showToast(`Activated profile: ${selectedPolicyProfile}`, 'success');
                fetchDashboard();
                fetchBip110Status();
            } else {
                showToast(`Failed to apply profile: ${data.output}`, 'error', 6000);
            }
        } catch (err) {
            showToast(`API error: ${err.message}`, 'error');
        } finally {
            btnApplyProfile.disabled = false;
            btnApplyProfile.textContent = 'Activate Selected Profile';
        }
    });
    
    // ----------------------------------------------------
    // Config Editor Files (policy.toml & bitcoin.conf)
    // ----------------------------------------------------
    async function loadConfigFiles() {
        try {
            editorPolicy.value = 'Loading policy.toml...';
            editorBitcoinConf.value = 'Loading bitcoin.conf...';
            
            const res = await fetch('/api/config');
            const data = await res.json();
            
            if (data.success) {
                editorPolicy.value = data.policy_toml || '# policy.toml is empty or not created yet';
                editorBitcoinConf.value = data.bitcoin_conf || '# bitcoin.conf is empty or not created yet';
            } else {
                editorPolicy.value = `# Error loading configs:\n# ${data.error}`;
                editorBitcoinConf.value = `# Error loading configs:\n# ${data.error}`;
            }
        } catch (err) {
            editorPolicy.value = `# API Error: ${err.message}`;
            editorBitcoinConf.value = `# API Error: ${err.message}`;
        }
    }
    
    btnSavePolicy.addEventListener('click', () => saveConfig('policy.toml', editorPolicy.value));
    btnSaveBitcoinConf.addEventListener('click', () => saveConfig('bitcoin.conf', editorBitcoinConf.value));
    
    async function saveConfig(filename, content) {
        try {
            const saveBtn = filename === 'policy.toml' ? btnSavePolicy : btnSaveBitcoinConf;
            const originalText = saveBtn.textContent;
            
            saveBtn.disabled = true;
            saveBtn.textContent = 'Saving...';
            
            const res = await fetch('/api/config', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ filename, content })
            });
            const data = await res.json();
            
            if (data.success) {
                alert(`Successfully saved ${filename}!`);
                loadParsedSettings(); // Refresh settings form
            } else {
                alert(`Failed to save: ${data.error}`);
            }
            saveBtn.disabled = false;
            saveBtn.textContent = originalText;
        } catch (err) {
            alert(`API error saving file: ${err.message}`);
        }
    }
    
    // ----------------------------------------------------
    // Configuration Visual Form Sub-tabs Navigation
    // ----------------------------------------------------
    settingsSubTabs.forEach(tab => {
        tab.addEventListener('click', () => {
            // Remove active class from all tabs
            settingsSubTabs.forEach(t => t.classList.remove('active'));
            // Add active class to clicked tab
            tab.classList.add('active');
            
            const targetTab = tab.getAttribute('data-settings-tab');
            
            // Hide all settings panes
            settingsSubPanes.forEach(pane => pane.classList.add('hidden'));
            
            // Show current settings pane
            if (targetTab === 'raw') {
                document.getElementById('settings-pane-raw').classList.remove('hidden');
                btnSaveVisualSettings.classList.add('hidden');
                loadConfigFiles();
            } else {
                document.getElementById(`settings-pane-${targetTab}`).classList.remove('hidden');
                btnSaveVisualSettings.classList.remove('hidden');
            }
        });
    });

    // Pruning mode row visibility toggle
    setPruneMode.addEventListener('change', () => {
        if (setPruneMode.value === 'custom') {
            customPruneSizeRow.classList.remove('hidden');
        } else {
            customPruneSizeRow.classList.add('hidden');
        }
    });

    // Peer Block Filters requires Block Filter Index
    const setPeerBlockFilters = document.getElementById('set-peerblockfilters');
    const setBlockFilterIndex = document.getElementById('set-blockfilterindex');

    const handlePeerBlockFiltersChange = () => {
        if (setPeerBlockFilters.checked) {
            setBlockFilterIndex.checked = true;
            setBlockFilterIndex.disabled = true;
        } else {
            setBlockFilterIndex.disabled = false;
        }
    };

    setPeerBlockFilters.addEventListener('change', handlePeerBlockFiltersChange);

    // Datacarrier toggle controls size and cost fields
    const setDatacarrier = document.getElementById('set-datacarrier');
    const setDatacarrierSize = document.getElementById('set-datacarriersize');
    const setDatacarrierCost = document.getElementById('set-datacarriercost');

    const handleDatacarrierChange = () => {
        if (setDatacarrier.checked) {
            setDatacarrierSize.disabled = false;
            setDatacarrierCost.disabled = false;
        } else {
            setDatacarrierSize.disabled = true;
            setDatacarrierCost.disabled = true;
        }
    };

    setDatacarrier.addEventListener('change', handleDatacarrierChange);

    // Pruning mode visibility and txindex incompatibility check
    const setTxindex = document.getElementById('set-txindex');

    const handlePruneModeChange = () => {
        const pMode = setPruneMode.value;
        if (pMode === 'custom') {
            customPruneSizeRow.classList.remove('hidden');
        } else {
            customPruneSizeRow.classList.add('hidden');
        }

        if (pMode !== '0') {
            setTxindex.checked = false;
            setTxindex.disabled = true;
            setPeerBlockFilters.checked = false;
            setPeerBlockFilters.disabled = true;
            setBlockFilterIndex.checked = false;
            setBlockFilterIndex.disabled = true;
        } else {
            setTxindex.disabled = false;
            setPeerBlockFilters.disabled = false;
            handlePeerBlockFiltersChange();
        }

    };

    setPruneMode.addEventListener('change', handlePruneModeChange);




    async function loadParsedSettings() {
        try {
            const res = await fetch('/api/config/parsed');
            const data = await res.json();
            if (data.success) {
                const conf = data.settings;
                
                // 1. Storage Pane
                document.getElementById('set-chain').value = conf['chain'] || 'main';
                document.getElementById('set-blocksonly').checked = conf['blocksonly'] === '1' || conf['blocksonly'] === 1;


                
                // Peer Block Filters & Index
                setPeerBlockFilters.checked = conf['peerblockfilters'] === '1' || conf['peerblockfilters'] === 1 || conf['peerblockfilters'] === undefined;
                setBlockFilterIndex.checked = conf['blockfilterindex'] === '1' || conf['blockfilterindex'] === 1 || conf['blockfilterindex'] === undefined;
                handlePeerBlockFiltersChange(); // Update disabled status
                
                // 2. Network Pane
                // Outgoing networks onlynet
                if (conf['onlynet'] === undefined) {
                    document.getElementById('set-onlynet-clearnet').checked = true;
                    document.getElementById('set-onlynet-tor').checked = true;
                    document.getElementById('set-onlynet-i2p').checked = true;
                } else {
                    const onlynetStr = Array.isArray(conf['onlynet']) ? conf['onlynet'].join(',') : String(conf['onlynet']);
                    document.getElementById('set-onlynet-clearnet').checked = onlynetStr.includes('ipv4') || onlynetStr.includes('ipv6');
                    document.getElementById('set-onlynet-tor').checked = onlynetStr.includes('onion');
                    document.getElementById('set-onlynet-i2p').checked = onlynetStr.includes('i2p');
                }

                // Proxy all over Tor
                document.getElementById('set-proxy-all-tor').checked = !!conf['proxy'];

                // Incoming networks listen, listenonion, i2pacceptincoming
                document.getElementById('set-incoming-clearnet').checked = conf['listen'] === '1' || conf['listen'] === 1 || conf['listen'] === undefined;
                document.getElementById('set-incoming-tor').checked = conf['listenonion'] === '1' || conf['listenonion'] === 1 || conf['listenonion'] === undefined;
                document.getElementById('set-incoming-i2p').checked = conf['i2pacceptincoming'] === '1' || conf['i2pacceptincoming'] === 1;

                // Connection limits & buffers
                document.getElementById('set-maxconnections').value = conf['maxconnections'] !== undefined ? conf['maxconnections'] : 125;
                document.getElementById('set-maxuploadtarget').value = conf['maxuploadtarget'] !== undefined ? conf['maxuploadtarget'] : 0;
                document.getElementById('set-maxreceivebuffer').value = conf['maxreceivebuffer'] !== undefined ? conf['maxreceivebuffer'] : 5000;
                document.getElementById('set-maxsendbuffer').value = conf['maxsendbuffer'] !== undefined ? conf['maxsendbuffer'] : 5000;
                document.getElementById('set-peertimeout').value = conf['peertimeout'] !== undefined ? conf['peertimeout'] : 60;
                document.getElementById('set-timeout').value = conf['timeout'] !== undefined ? conf['timeout'] : 5000;
                document.getElementById('set-bantime').value = conf['bantime'] !== undefined ? conf['bantime'] : 86400;
                document.getElementById('set-peerbloomfilters').checked = conf['peerbloomfilters'] === '1' || conf['peerbloomfilters'] === 1;

                // Custom seeds & proxies
                document.getElementById('set-connect').value = Array.isArray(conf['connect']) ? conf['connect'].join(', ') : (conf['connect'] || '');
                document.getElementById('set-addnode').value = Array.isArray(conf['addnode']) ? conf['addnode'].join(', ') : (conf['addnode'] || '');
                document.getElementById('set-proxy').value = conf['proxy'] || '';
                document.getElementById('set-onion').value = conf['onion'] || '';
                document.getElementById('set-discover').checked = conf['discover'] === '1' || conf['discover'] === 1 || conf['discover'] === undefined;
                
                // 3. Policy Pane
                document.getElementById('set-policyprofile').value = conf['profile'] || 'maximalist';
                document.getElementById('set-bip110').value = conf['bip110_mode'] || 'auto';

                // Data Carrier
                setDatacarrier.checked = conf['datacarrier'] === '1' || conf['datacarrier'] === 1 || conf['datacarrier'] === undefined;
                setDatacarrierSize.value = conf['datacarriersize'] !== undefined ? conf['datacarriersize'] : 83;
                setDatacarrierCost.value = conf['datacarriercost'] !== undefined ? conf['datacarriercost'] : 1;
                document.getElementById('set-permitbaredatacarrier').checked = conf['permitbaredatacarrier'] === '1' || conf['permitbaredatacarrier'] === 1;
                document.getElementById('set-acceptnonstddatacarrier').checked = conf['acceptnonstddatacarrier'] === '1' || conf['acceptnonstddatacarrier'] === 1;
                handleDatacarrierChange(); // Update fields state

                // Relay Rules
                document.getElementById('set-rejectparasites').checked = conf['rejectparasites'] === '1' || conf['rejectparasites'] === 1 || conf['rejectparasites'] === undefined;
                document.getElementById('set-rejecttokens').checked = conf['rejecttokens'] === '1' || conf['rejecttokens'] === 1;
                document.getElementById('set-permitbaremultisig').checked = conf['permitbaremultisig'] === '1' || conf['permitbaremultisig'] === 1;
                document.getElementById('set-permitbarepubkey').checked = conf['permitbarepubkey'] === '1' || conf['permitbarepubkey'] === 1;
                document.getElementById('set-maxscriptsize').value = conf['maxscriptsize'] !== undefined ? conf['maxscriptsize'] : 1650;

                // Block Construction & Fees
                document.getElementById('set-blockmaxsize').value = conf['blockmaxsize'] !== undefined ? conf['blockmaxsize'] : 3985000;
                document.getElementById('set-blockmaxweight').value = conf['blockmaxweight'] !== undefined ? conf['blockmaxweight'] : 3985000;
                document.getElementById('set-blockmintxfee').value = conf['blockmintxfee'] !== undefined ? Math.round(parseFloat(conf['blockmintxfee']) * 100000) : 1;
                document.getElementById('set-minrelaytxfee').value = conf['minrelaytxfee'] !== undefined ? Math.round(parseFloat(conf['minrelaytxfee']) * 100000) : 1;
                document.getElementById('set-incrementalrelayfee').value = conf['incrementalrelayfee'] !== undefined ? Math.round(parseFloat(conf['incrementalrelayfee']) * 100000) : 1;

                
                // 4. Optimization Pane
                document.getElementById('set-dbcache').value = conf['dbcache'] || 450;
                
                const pVal = conf['prune'];
                if (pVal === undefined || pVal === 0 || pVal === '0') {
                    setPruneMode.value = '0';
                } else if (pVal === 1 || pVal === '1') {
                    setPruneMode.value = '1';
                } else {
                    setPruneMode.value = 'custom';
                    document.getElementById('set-pruning-target-gb').value = Math.max(1, Math.round(pVal / 1000));
                }
                handlePruneModeChange();
                
                if (pVal === undefined || pVal === 0 || pVal === '0') {
                    setTxindex.checked = conf['txindex'] === '1' || conf['txindex'] === 1 || conf['txindex'] === undefined;
                }


                document.getElementById('set-coinstatsindex').checked = conf['coinstatsindex'] === '1' || conf['coinstatsindex'] === 1;
                document.getElementById('set-blockreconstructionextratxn').value = conf['blockreconstructionextratxn'] !== undefined ? conf['blockreconstructionextratxn'] : 32768;
                document.getElementById('set-blockreconstructionextratxnsize').value = conf['blockreconstructionextratxnsize'] !== undefined ? conf['blockreconstructionextratxnsize'] : 10;
                document.getElementById('set-maxmempool').value = conf['maxmempool'] !== undefined ? conf['maxmempool'] : 300;
                document.getElementById('set-mempoolexpiry').value = conf['mempoolexpiry'] !== undefined ? conf['mempoolexpiry'] : 336;
                document.getElementById('set-maxorphantx').value = conf['maxorphantx'] !== undefined ? conf['maxorphantx'] : 100;
                document.getElementById('set-persistmempool').checked = conf['persistmempool'] === '1' || conf['persistmempool'] === 1 || conf['persistmempool'] === undefined;
                document.getElementById('set-datum').checked = conf['datum'] === '1' || conf['datum'] === 1 || conf['datum'] === undefined;

                // 5. System Pane (RPC & API)
                document.getElementById('set-par').value = conf['par'] !== undefined ? conf['par'] : '0';
                document.getElementById('set-server').checked = conf['server'] === '1' || conf['server'] === 1 || conf['server'] === undefined;
                document.getElementById('set-rpcport').value = conf['rpcport'] || 8332;
                document.getElementById('set-rpcallowip').value = conf['rpcallowip'] || '127.0.0.1';
                document.getElementById('set-prometheusport').value = conf['prometheusport'] || 9332;
                document.getElementById('set-rest').checked = conf['rest'] === '1' || conf['rest'] === 1;
                document.getElementById('set-rpcworkqueue').value = conf['rpcworkqueue'] !== undefined ? conf['rpcworkqueue'] : 128;


            }
        } catch (err) {
            console.error('Failed to load parsed settings', err);
        }
    }

    btnSaveVisualSettings.addEventListener('click', async () => {
        const formData = {};
        
        // 1. Storage
        formData['chain'] = document.getElementById('set-chain').value;
        formData['blocksonly'] = document.getElementById('set-blocksonly').checked ? 1 : 0;
        formData['peerblockfilters'] = setPeerBlockFilters.checked ? 1 : 0;
        formData['blockfilterindex'] = setBlockFilterIndex.checked ? 1 : 0;


        
        // 2. Network
        // onlynet outgoing connections
        const onlynet = [];
        const outClearnet = document.getElementById('set-onlynet-clearnet').checked;
        const outTor = document.getElementById('set-onlynet-tor').checked;
        const outI2P = document.getElementById('set-onlynet-i2p').checked;

        if (outClearnet) {
            onlynet.push('ipv4');
            onlynet.push('ipv6');
        }
        if (outTor) {
            onlynet.push('onion');
        }
        if (outI2P) {
            onlynet.push('i2p');
        }
        
        // If all are checked, we can clear onlynet (or write them all). Let's write them explicitly if not all checked.
        if (onlynet.length === 0) {
            alert('Warning: You must select at least one network for outgoing connections. Defaulting to Clearnet.');
            formData['onlynet'] = ['ipv4', 'ipv6'];
        } else if (onlynet.length === 4) {
            formData['onlynet'] = ''; // Empty defaults to all
        } else {
            formData['onlynet'] = onlynet;
        }

        // Proxy all over Tor
        if (document.getElementById('set-proxy-all-tor').checked) {
            formData['proxy'] = document.getElementById('set-proxy').value.trim() || '127.0.0.1:9050';
        } else {
            formData['proxy'] = '';
        }

        // Incoming connections
        formData['listen'] = document.getElementById('set-incoming-clearnet').checked ? 1 : 0;
        formData['listenonion'] = document.getElementById('set-incoming-tor').checked ? 1 : 0;
        formData['i2pacceptincoming'] = document.getElementById('set-incoming-i2p').checked ? 1 : 0;

        // Connections limits and buffers
        formData['maxconnections'] = parseInt(document.getElementById('set-maxconnections').value);
        formData['maxuploadtarget'] = parseInt(document.getElementById('set-maxuploadtarget').value);
        formData['maxreceivebuffer'] = parseInt(document.getElementById('set-maxreceivebuffer').value);
        formData['maxsendbuffer'] = parseInt(document.getElementById('set-maxsendbuffer').value);
        formData['peertimeout'] = parseInt(document.getElementById('set-peertimeout').value);
        formData['timeout'] = parseInt(document.getElementById('set-timeout').value);
        formData['bantime'] = parseInt(document.getElementById('set-bantime').value);
        formData['peerbloomfilters'] = document.getElementById('set-peerbloomfilters').checked ? 1 : 0;

        // Custom seeds and proxies
        formData['connect'] = document.getElementById('set-connect').value.trim();
        formData['addnode'] = document.getElementById('set-addnode').value.trim();
        formData['onion'] = document.getElementById('set-onion').value.trim();
        formData['discover'] = document.getElementById('set-discover').checked ? 1 : 0;
        
        // 3. Policy
        formData['profile'] = document.getElementById('set-policyprofile').value;
        formData['bip110_mode'] = document.getElementById('set-bip110').value;

        // Data Carrier
        formData['datacarrier'] = setDatacarrier.checked ? 1 : 0;
        formData['datacarriersize'] = parseInt(setDatacarrierSize.value);
        formData['datacarriercost'] = parseInt(setDatacarrierCost.value);
        formData['permitbaredatacarrier'] = document.getElementById('set-permitbaredatacarrier').checked ? 1 : 0;
        formData['acceptnonstddatacarrier'] = document.getElementById('set-acceptnonstddatacarrier').checked ? 1 : 0;

        // Relay Rules
        formData['rejectparasites'] = document.getElementById('set-rejectparasites').checked ? 1 : 0;
        formData['rejecttokens'] = document.getElementById('set-rejecttokens').checked ? 1 : 0;
        formData['permitbaremultisig'] = document.getElementById('set-permitbaremultisig').checked ? 1 : 0;
        formData['permitbarepubkey'] = document.getElementById('set-permitbarepubkey').checked ? 1 : 0;
        formData['maxscriptsize'] = parseInt(document.getElementById('set-maxscriptsize').value);

        // Block Construction & Fees (divide by 100000 to convert to BTC/kB)
        formData['blockmaxsize'] = parseInt(document.getElementById('set-blockmaxsize').value);
        formData['blockmaxweight'] = parseInt(document.getElementById('set-blockmaxweight').value);
        formData['blockmintxfee'] = parseFloat(document.getElementById('set-blockmintxfee').value) / 100000;
        formData['minrelaytxfee'] = parseFloat(document.getElementById('set-minrelaytxfee').value) / 100000;
        formData['incrementalrelayfee'] = parseFloat(document.getElementById('set-incrementalrelayfee').value) / 100000;

        
        // 4. Optimization
        formData['dbcache'] = parseInt(document.getElementById('set-dbcache').value);
        const pMode = setPruneMode.value;
        if (pMode === '0') {
            formData['prune'] = 0;
        } else if (pMode === '1') {
            formData['prune'] = 1;
        } else {
            formData['prune'] = parseInt(document.getElementById('set-pruning-target-gb').value) * 1000;
        }
        formData['txindex'] = setTxindex.checked ? 1 : 0;

        formData['coinstatsindex'] = document.getElementById('set-coinstatsindex').checked ? 1 : 0;
        formData['blockreconstructionextratxn'] = parseInt(document.getElementById('set-blockreconstructionextratxn').value);
        formData['blockreconstructionextratxnsize'] = parseInt(document.getElementById('set-blockreconstructionextratxnsize').value);
        formData['maxmempool'] = parseInt(document.getElementById('set-maxmempool').value);
        formData['mempoolexpiry'] = parseInt(document.getElementById('set-mempoolexpiry').value);
        formData['maxorphantx'] = parseInt(document.getElementById('set-maxorphantx').value);
        formData['persistmempool'] = document.getElementById('set-persistmempool').checked ? 1 : 0;
        formData['datum'] = document.getElementById('set-datum').checked ? 1 : 0;

        // 5. System (RPC & API)
        formData['par'] = document.getElementById('set-par').value;
        formData['server'] = document.getElementById('set-server').checked ? 1 : 0;
        formData['rpcport'] = parseInt(document.getElementById('set-rpcport').value);
        formData['rpcallowip'] = document.getElementById('set-rpcallowip').value.trim();
        formData['prometheusport'] = parseInt(document.getElementById('set-prometheusport').value);
        formData['rest'] = document.getElementById('set-rest').checked ? 1 : 0;
        formData['rpcworkqueue'] = parseInt(document.getElementById('set-rpcworkqueue').value);



        try {
            btnSaveVisualSettings.disabled = true;
            btnSaveVisualSettings.textContent = 'Saving...';
            
            const res = await fetch('/api/config/parsed', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(formData)
            });
            const data = await res.json();
            
            if (data.success) {
                alert('All configurations saved successfully! Restart the node to apply these changes.');
            } else {
                alert(`Failed to save settings: ${data.error}`);
            }
        } catch (err) {
            alert(`API Error saving configurations: ${err.message}`);
        } finally {
            btnSaveVisualSettings.disabled = false;
            btnSaveVisualSettings.textContent = 'Save All Settings';
        }
    });


    // ----------------------------------------------------
    // WALLET OPERATIONS AND MANAGEMENT
    // ----------------------------------------------------
    function resolveActiveWallet(wallets) {
        const saved = localStorage.getItem(STORAGE_KEY_ACTIVE_WALLET);
        if (saved && wallets.includes(saved)) return saved;
        return wallets[0];
    }

    function populateCliWalletSelect() {
        if (!cliWalletSelect) return;
        const current = cliWalletSelect.value;
        cliWalletSelect.innerHTML = '<option value="">(none — node RPC)</option>';
        loadedWallets.forEach(w => {
            const opt = document.createElement('option');
            opt.value = w;
            opt.textContent = w;
            cliWalletSelect.appendChild(opt);
        });
        if (activeWalletName && loadedWallets.includes(activeWalletName)) {
            cliWalletSelect.value = activeWalletName;
        } else if (current && [...cliWalletSelect.options].some(o => o.value === current)) {
            cliWalletSelect.value = current;
        }
    }

    async function loadBackupDirHint() {
        if (!backupDirHint) return;
        try {
            const res = await fetch('/api/wallet/backup-path');
            const data = await res.json();
            if (data.success) backupDirHint.textContent = data.path;
        } catch { /* ignore */ }
    }

    function populateWalletSelector(wallets, onDisk = []) {
        if (!walletSelector) return;
        walletSelector.innerHTML = '';
        wallets.forEach(w => {
            const opt = document.createElement('option');
            opt.value = w;
            opt.textContent = w;
            walletSelector.appendChild(opt);
        });
        const notLoaded = (onDisk || []).filter(w => !wallets.includes(w));
        if (notLoaded.length > 0) {
            const group = document.createElement('optgroup');
            group.label = 'On disk (not loaded)';
            notLoaded.forEach(w => {
                const opt = document.createElement('option');
                opt.value = w;
                opt.textContent = `${w} — load`;
                opt.dataset.needsLoad = 'true';
                group.appendChild(opt);
            });
            walletSelector.appendChild(group);
        }
        if (activeWalletName) {
            walletSelector.value = activeWalletName;
        }
    }

    function setActiveWallet(name) {
        activeWalletName = name;
        selectedUtxoKeys.clear();
        cachedUtxos = [];
        localStorage.setItem(STORAGE_KEY_ACTIVE_WALLET, name);
        if (activeWalletNameLabel) activeWalletNameLabel.textContent = name;
        if (walletSelector) walletSelector.value = name;
        fetchWalletInfo();
        fetchWalletHistory();
        if (walletSubAddresses && !walletSubAddresses.classList.contains('hidden')) {
            fetchWalletAddresses();
        }
        if (walletSubUtxos && !walletSubUtxos.classList.contains('hidden')) {
            fetchAndRenderUtxos('manager');
        }
    }

    function refreshWalletData() {
        fetchWalletInfo();
        fetchWalletHistory();
        if (walletSubAddresses && !walletSubAddresses.classList.contains('hidden')) {
            fetchWalletAddresses();
        }
        if (walletSubUtxos && !walletSubUtxos.classList.contains('hidden')) {
            fetchAndRenderUtxos('manager');
        }
        if (sendAdvancedPane && !sendAdvancedPane.classList.contains('hidden')) {
            fetchAndRenderUtxos('send');
        }
    }

    function renderNoWalletView() {
        walletNoWalletView.classList.remove('hidden');
        walletActiveView.classList.add('hidden');
        walletNoWalletView.innerHTML = `
            <div class="empty-icon">🪙</div>
            <h3>No Wallet Loaded</h3>
            <p class="text-secondary mt-2">To start sending and receiving Bitcoin, you must load an existing wallet or create a new one.</p>
            <div class="form-group mt-4" style="max-width: 340px; margin: 16px auto;">
                <input type="text" id="new-wallet-name" placeholder="Wallet Name (e.g. sovereign_wallet)" value="sovereign_wallet">
            </div>
            <div class="btn-group mt-2" style="justify-content: center;">
                <button class="btn btn-primary" id="btn-create-wallet">Create New Wallet</button>
                <button class="btn btn-outline" id="btn-load-wallet-quick">Load Wallet</button>
            </div>
        `;
        document.getElementById('btn-create-wallet').addEventListener('click', createWallet);
        document.getElementById('btn-load-wallet-quick').addEventListener('click', loadWallet);
    }

    function startWalletPolling() {
        checkWalletStatus();
        if (walletIntervalId) clearInterval(walletIntervalId);
        walletIntervalId = setInterval(checkWalletStatus, 3000);
    }

    function stopWalletPolling() {
        if (walletIntervalId) {
            clearInterval(walletIntervalId);
            walletIntervalId = null;
        }
    }

    async function checkWalletStatus() {
        if (!isNodeRunning) {
            walletNoWalletView.classList.remove('hidden');
            walletActiveView.classList.add('hidden');
            walletNoWalletView.innerHTML = `
                <div class="empty-icon">🪙</div>
                <h3>Node is Offline</h3>
                <p class="text-secondary mt-2">The Bitcoin node daemon is currently stopped. Please start the node from the dashboard to enable wallet operations.</p>
            `;
            return;
        }

        try {
            const res = await fetch('/api/wallet/status');
            const data = await res.json();

            if (data.loaded && data.wallets.length > 0) {
                loadedWallets = data.wallets;
                const resolved = resolveActiveWallet(loadedWallets);
                const walletChanged = resolved !== activeWalletName;
                activeWalletName = resolved;

                walletNoWalletView.classList.add('hidden');
                walletActiveView.classList.remove('hidden');
                populateWalletSelector(loadedWallets, data.on_disk || []);

                populateCliWalletSelect();

                if (walletChanged) {
                    setActiveWallet(activeWalletName);
                } else {
                    fetchWalletInfo();
                }
            } else {
                activeWalletName = '';
                loadedWallets = [];
                renderNoWalletView();
            }
        } catch (err) {
            console.error('Error checking wallet status:', err);
        }
    }

    async function loadWalletByName(name) {
        try {
            const res = await fetch('/api/wallet/load', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name })
            });
            const data = await res.json();
            if (data.success) {
                showToast(`Wallet "${name}" loaded`, 'success');
                localStorage.setItem(STORAGE_KEY_ACTIVE_WALLET, name);
                await checkWalletStatus();
            } else {
                showToast(`Failed to load wallet: ${data.error}`, 'error', 6000);
            }
        } catch (err) {
            showToast(`API error: ${err.message}`, 'error');
        }
    }

    async function createWallet() {
        const nameInput = document.getElementById('new-wallet-name');
        const name = nameInput.value.trim() || 'sovereign_wallet';

        try {
            const btn = document.getElementById('btn-create-wallet');
            btn.disabled = true;
            btn.textContent = 'Creating...';

            const res = await fetch('/api/wallet/create', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name })
            });
            const data = await res.json();

            if (data.success) {
                localStorage.setItem(STORAGE_KEY_ACTIVE_WALLET, name);
                showToast(`Wallet "${name}" created and loaded`, 'success');
                checkWalletStatus();
            } else {
                showToast(`Failed to create wallet: ${data.error}`, 'error', 6000);
            }
        } catch (err) {
            showToast(`API error: ${err.message}`, 'error');
        } finally {
            const btn = document.getElementById('btn-create-wallet');
            if (btn) {
                btn.disabled = false;
                btn.textContent = 'Create New Wallet';
            }
        }
    }

    async function loadWallet() {
        const nameInput = document.getElementById('new-wallet-name');
        const name = nameInput ? nameInput.value.trim() : 'sovereign_wallet';
        await loadWalletByName(name);
    }

    async function fetchWalletInfo() {
        if (!activeWalletName) return;
        try {
            const res = await fetch(`/api/wallet/info?name=${activeWalletName}`);
            const data = await res.json();
            if (data.success) {
                const info = JSON.parse(data.output);
                
                const bal = info.balance;
                const unconfirmed = info.unconfirmed_balance || 0;
                
                walletBalanceBtc.textContent = `${bal.toFixed(8)} BTC`;
                
                const balUsd = bal * btcPriceUsd;
                walletBalanceUsd.textContent = `$${balUsd.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})} USD`;
                
                if (unconfirmed > 0) {
                    walletBalanceUnconfirmed.textContent = `Unconfirmed: ${unconfirmed.toFixed(8)} BTC`;
                    walletBalanceUnconfirmed.classList.remove('hidden');
                    balanceCard?.classList.add('has-unconfirmed');
                } else {
                    walletBalanceUnconfirmed.classList.add('hidden');
                    balanceCard?.classList.remove('has-unconfirmed');
                }
            }
        } catch (err) {
            console.error(err);
        }
    }

    async function fetchWalletHistory() {
        if (!activeWalletName) return;
        try {
            const res = await fetch(`/api/wallet/transactions?name=${activeWalletName}`);
            const data = await res.json();
            
            if (data.success) {
                const txs = JSON.parse(data.output);
                
                if (!txs || txs.length === 0) {
                    walletTxList.innerHTML = `<p class="text-secondary text-center py-4">No recent transactions found.</p>`;
                    return;
                }
                
                txs.sort((a, b) => b.time - a.time);
                
                walletTxList.innerHTML = '';
                txs.forEach(tx => {
                    const div = document.createElement('div');
                    div.className = 'tx-item';
                    
                    const isReceive = tx.category === 'receive';
                    const typeClass = isReceive ? 'tx-receive' : 'tx-send';
                    const symbol = isReceive ? '↓' : '↑';
                    const typeText = isReceive ? 'Received' : 'Sent';
                    const conf = tx.confirmations || 0;
                    const confClass = conf >= 6 ? 'tx-confirmed' : conf > 0 ? 'tx-pending' : 'tx-unconfirmed';
                    const confLabel = conf >= 6 ? `${conf} conf` : conf > 0 ? `${conf} conf` : 'unconfirmed';

                    const txDate = new Date(tx.time * 1000).toLocaleString();
                    const shortAddr = tx.address ? (tx.address.substring(0, 10) + '...' + tx.address.substring(tx.address.length - 8)) : 'N/A';

                    div.innerHTML = `
                        <div class="tx-details">
                            <span class="tx-dir-icon ${typeClass}">${symbol}</span>
                            <div>
                                <span class="tx-type ${typeClass}">${typeText}</span>
                                <span class="tx-conf-badge ${confClass}">${confLabel}</span>
                                <span class="tx-address" title="${tx.address || ''}">${isReceive ? 'From' : 'To'}: ${shortAddr}</span>
                            </div>
                        </div>
                        <div class="tx-amount-col">
                            <span class="tx-amount ${typeClass}">${isReceive ? '+' : '-'}${Math.abs(tx.amount).toFixed(8)} BTC</span>
                            <div class="tx-date">${txDate}</div>
                        </div>
                    `;
                    walletTxList.appendChild(div);
                });
            }
        } catch (err) {
            console.error(err);
        }
    }

    const walletSubPills = [pillWalletReceive, pillWalletSend, pillWalletUtxos, pillWalletHistory, pillWalletAddresses, pillWalletTools];
    const walletSubPanes = [walletSubReceive, walletSubSend, walletSubUtxos, walletSubHistory, walletSubAddresses, walletSubTools];

    function switchSendMode(mode) {
        const isAdvanced = mode === 'advanced';
        sendModeSimple.classList.toggle('active', !isAdvanced);
        sendModeAdvanced.classList.toggle('active', isAdvanced);
        sendSimplePane.classList.toggle('hidden', isAdvanced);
        sendAdvancedPane.classList.toggle('hidden', !isAdvanced);
        if (isAdvanced) fetchAndRenderUtxos('send');
    }

    async function fetchFeeEstimate() {
        try {
            const res = await fetch('/api/wallet/fee-estimate?blocks=6');
            const data = await res.json();
            if (data.success && data.sat_vb) {
                if (sendFeeHint) sendFeeHint.textContent = `(recommended: ~${data.sat_vb} sat/vB)`;
                if (sendAdvFeeRateInput && !sendAdvFeeRateInput.value) {
                    sendAdvFeeRateInput.value = data.sat_vb;
                }
            } else if (sendFeeHint) {
                const err = data.errors?.[0];
                sendFeeHint.textContent = err ? `(${err})` : '(estimate unavailable — sync node)';
            }
        } catch {
            if (sendFeeHint) sendFeeHint.textContent = '';
        }
    }

    function utxoStatusBadge(utxo) {
        if (utxo.locked) return '<span class="utxo-badge utxo-badge-locked">Locked</span>';
        if (utxo.spendable === false) return '<span class="utxo-badge utxo-badge-unspendable">Unspendable</span>';
        return '<span class="utxo-badge utxo-badge-spendable">Spendable</span>';
    }

    function bindUtxoCheckbox(checkbox, key) {
        checkbox.checked = selectedUtxoKeys.has(key);
        checkbox.addEventListener('change', () => {
            if (checkbox.checked) selectedUtxoKeys.add(key);
            else selectedUtxoKeys.delete(key);
            updateUtxoSelectionSummary();
        });
    }

    function renderUtxoManagerTable(utxos) {
        if (!walletUtxoList) return;
        if (!utxos.length) {
            walletUtxoList.innerHTML = '<tr><td colspan="7" class="text-secondary text-center py-4">No UTXOs found.</td></tr>';
            if (utxoTotalCount) utxoTotalCount.textContent = '0';
            if (utxoTotalBtc) utxoTotalBtc.textContent = '0.00000000';
            if (utxoLockedCount) utxoLockedCount.textContent = '0';
            return;
        }
        const totalBtc = utxos.reduce((s, u) => s + u.amount, 0);
        const lockedN = utxos.filter(u => u.locked).length;
        if (utxoTotalCount) utxoTotalCount.textContent = String(utxos.length);
        if (utxoTotalBtc) utxoTotalBtc.textContent = totalBtc.toFixed(8);
        if (utxoLockedCount) utxoLockedCount.textContent = String(lockedN);

        walletUtxoList.innerHTML = '';
        utxos.sort((a, b) => b.amount - a.amount).forEach(utxo => {
            const key = utxoKey(utxo);
            const tr = document.createElement('tr');
            if (utxo.locked) tr.classList.add('utxo-locked');
            if (selectedUtxoKeys.has(key)) tr.classList.add('utxo-selected');
            const shortTx = utxo.txid.substring(0, 8) + '…';
            tr.innerHTML = `
                <td><input type="checkbox" class="utxo-cb" data-key="${key}"></td>
                <td class="utxo-amount">${utxo.amount.toFixed(8)}</td>
                <td>${utxo.confirmations}</td>
                <td class="utxo-addr" title="${utxo.address || ''}">${utxo.address || '—'}</td>
                <td>${utxo.label || '—'}</td>
                <td>${utxoStatusBadge(utxo)}</td>
                <td class="utxo-txid" title="${utxo.txid}">${shortTx}</td>
            `;
            const cb = tr.querySelector('.utxo-cb');
            bindUtxoCheckbox(cb, key);
            cb.addEventListener('change', () => tr.classList.toggle('utxo-selected', cb.checked));
            walletUtxoList.appendChild(tr);
        });
        if (utxoSelectAll) utxoSelectAll.checked = false;
    }

    function renderSendUtxoTable(utxos) {
        if (!sendUtxoList) return;
        const spendable = utxos.filter(u => u.spendable !== false);
        if (!spendable.length) {
            sendUtxoList.innerHTML = '<tr><td colspan="5" class="text-secondary text-center py-3">No spendable UTXOs.</td></tr>';
            updateUtxoSelectionSummary();
            return;
        }
        sendUtxoList.innerHTML = '';
        spendable.sort((a, b) => b.amount - a.amount).forEach(utxo => {
            const key = utxoKey(utxo);
            const tr = document.createElement('tr');
            if (utxo.locked) tr.classList.add('utxo-locked');
            if (selectedUtxoKeys.has(key)) tr.classList.add('utxo-selected');
            tr.innerHTML = `
                <td><input type="checkbox" class="send-utxo-cb" data-key="${key}"></td>
                <td class="utxo-amount">${utxo.amount.toFixed(8)}</td>
                <td>${utxo.confirmations}</td>
                <td class="utxo-addr" title="${utxo.address || ''}">${utxo.address || '—'}</td>
                <td>${utxoStatusBadge(utxo)}</td>
            `;
            const cb = tr.querySelector('.send-utxo-cb');
            bindUtxoCheckbox(cb, key);
            cb.addEventListener('change', () => tr.classList.toggle('utxo-selected', cb.checked));
            sendUtxoList.appendChild(tr);
        });
        if (sendUtxoSelectAll) sendUtxoSelectAll.checked = false;
        updateUtxoSelectionSummary();
    }

    async function fetchAndRenderUtxos(mode) {
        if (!activeWalletName) return;
        const tbody = mode === 'manager' ? walletUtxoList : sendUtxoList;
        if (tbody) tbody.innerHTML = '<tr><td colspan="7" class="text-secondary text-center py-3">Loading...</td></tr>';
        try {
            const res = await fetch(`/api/wallet/utxos?name=${encodeURIComponent(activeWalletName)}`);
            const data = await res.json();
            if (!data.success) {
                const err = data.error || 'Failed to load UTXOs';
                if (mode === 'manager' && walletUtxoList) {
                    walletUtxoList.innerHTML = `<tr><td colspan="7" class="text-secondary text-center py-4">${err}</td></tr>`;
                } else if (sendUtxoList) {
                    sendUtxoList.innerHTML = `<tr><td colspan="5" class="text-secondary text-center py-3">${err}</td></tr>`;
                }
                showToast(err, 'error', 5000);
                return;
            }
            cachedUtxos = data.utxos || [];
            if (mode === 'manager') renderUtxoManagerTable(cachedUtxos);
            else renderSendUtxoTable(cachedUtxos);
        } catch (err) {
            showToast(`UTXO load error: ${err.message}`, 'error');
        }
    }

    async function lockSelectedUtxos(unlock) {
        const inputs = getSelectedUtxoInputs();
        if (!inputs.length) {
            showToast('Select at least one UTXO', 'error');
            return;
        }
        try {
            const res = await fetch('/api/wallet/lock-utxo', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name: activeWalletName, inputs, unlock })
            });
            const data = await res.json();
            if (data.success) {
                showToast(unlock ? 'UTXOs unlocked' : 'UTXOs locked', 'success');
                await fetchAndRenderUtxos('manager');
                if (!sendAdvancedPane.classList.contains('hidden')) {
                    await fetchAndRenderUtxos('send');
                }
            } else {
                showToast(`Lock failed: ${data.error}`, 'error', 6000);
            }
        } catch (err) {
            showToast(`API error: ${err.message}`, 'error');
        }
    }

    function switchWalletSubTab(activePill, activePane) {
        walletSubPills.forEach(pill => pill.classList.remove('active'));
        activePill.classList.add('active');
        walletSubPanes.forEach(pane => pane.classList.add('hidden'));
        activePane.classList.remove('hidden');
        if (activePane === walletSubAddresses) fetchWalletAddresses();
        if (activePane === walletSubUtxos) fetchAndRenderUtxos('manager');
        if (activePane === walletSubSend) {
            fetchFeeEstimate();
            if (!sendAdvancedPane.classList.contains('hidden')) fetchAndRenderUtxos('send');
        }
    }

    pillWalletReceive.addEventListener('click', () => switchWalletSubTab(pillWalletReceive, walletSubReceive));
    pillWalletSend.addEventListener('click', () => switchWalletSubTab(pillWalletSend, walletSubSend));
    pillWalletUtxos.addEventListener('click', () => switchWalletSubTab(pillWalletUtxos, walletSubUtxos));
    pillWalletHistory.addEventListener('click', () => switchWalletSubTab(pillWalletHistory, walletSubHistory));
    pillWalletAddresses.addEventListener('click', () => switchWalletSubTab(pillWalletAddresses, walletSubAddresses));
    pillWalletTools.addEventListener('click', () => switchWalletSubTab(pillWalletTools, walletSubTools));

    if (sendModeSimple) sendModeSimple.addEventListener('click', () => switchSendMode('simple'));
    if (sendModeAdvanced) sendModeAdvanced.addEventListener('click', () => switchSendMode('advanced'));

    if (utxoSelectAll) {
        utxoSelectAll.addEventListener('change', () => {
            walletUtxoList.querySelectorAll('.utxo-cb').forEach(cb => {
                cb.checked = utxoSelectAll.checked;
                const key = cb.dataset.key;
                if (utxoSelectAll.checked) selectedUtxoKeys.add(key);
                else selectedUtxoKeys.delete(key);
                cb.closest('tr')?.classList.toggle('utxo-selected', cb.checked);
            });
            updateUtxoSelectionSummary();
        });
    }

    if (sendUtxoSelectAll) {
        sendUtxoSelectAll.addEventListener('change', () => {
            sendUtxoList.querySelectorAll('.send-utxo-cb').forEach(cb => {
                cb.checked = sendUtxoSelectAll.checked;
                const key = cb.dataset.key;
                if (sendUtxoSelectAll.checked) selectedUtxoKeys.add(key);
                else selectedUtxoKeys.delete(key);
                cb.closest('tr')?.classList.toggle('utxo-selected', cb.checked);
            });
            updateUtxoSelectionSummary();
        });
    }

    if (btnRefreshUtxos) btnRefreshUtxos.addEventListener('click', () => fetchAndRenderUtxos('manager'));
    if (btnLockSelectedUtxos) btnLockSelectedUtxos.addEventListener('click', () => lockSelectedUtxos(false));
    if (btnUnlockSelectedUtxos) btnUnlockSelectedUtxos.addEventListener('click', () => lockSelectedUtxos(true));

    if (btnUtxoGotoSend) {
        btnUtxoGotoSend.addEventListener('click', () => {
            if (!selectedUtxoKeys.size) {
                showToast('Select UTXOs first', 'error');
                return;
            }
            switchWalletSubTab(pillWalletSend, walletSubSend);
            switchSendMode('advanced');
        });
    }

    btnWalletGotoSend.addEventListener('click', () => switchWalletSubTab(pillWalletSend, walletSubSend));
    btnWalletGotoReceive.addEventListener('click', () => switchWalletSubTab(pillWalletReceive, walletSubReceive));

    if (walletSelector) {
        walletSelector.addEventListener('change', async () => {
            const selected = walletSelector.value;
            const opt = walletSelector.selectedOptions[0];
            if (opt?.dataset.needsLoad === 'true') {
                await loadWalletByName(selected);
                return;
            }
            if (selected && selected !== activeWalletName) {
                setActiveWallet(selected);
                showToast(`Switched to wallet "${selected}"`, 'info', 2500);
            }
        });
    }

    if (btnWalletUnload) {
        btnWalletUnload.addEventListener('click', async () => {
            if (!activeWalletName) return;
            if (!confirm(`Unload wallet "${activeWalletName}"?`)) return;
            try {
                btnWalletUnload.disabled = true;
                const res = await fetch('/api/wallet/unload', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name: activeWalletName })
                });
                const data = await res.json();
                if (data.success) {
                    showToast(`Wallet "${activeWalletName}" unloaded`, 'success');
                    activeWalletName = '';
                    localStorage.removeItem(STORAGE_KEY_ACTIVE_WALLET);
                    checkWalletStatus();
                } else {
                    showToast(`Failed to unload: ${data.error}`, 'error', 6000);
                }
            } catch (err) {
                showToast(`API error: ${err.message}`, 'error');
            } finally {
                btnWalletUnload.disabled = false;
            }
        });
    }

    function switchToolSubTab(activePill, activePane) {
        [subpillSignMsg, subpillPsbt, subpillSecurity].forEach(p => p?.classList.remove('active'));
        activePill.classList.add('active');
        [toolPaneSignMsg, toolPanePsbt, toolPaneSecurity].forEach(p => p?.classList.add('hidden'));
        activePane.classList.remove('hidden');
        if (activePane === toolPaneSecurity) loadBackupDirHint();
    }

    subpillSignMsg.addEventListener('click', () => switchToolSubTab(subpillSignMsg, toolPaneSignMsg));
    subpillPsbt.addEventListener('click', () => switchToolSubTab(subpillPsbt, toolPanePsbt));
    if (subpillSecurity) subpillSecurity.addEventListener('click', () => switchToolSubTab(subpillSecurity, toolPaneSecurity));

    // ----------------------------------------------------
    // Wallet Security Handlers
    // ----------------------------------------------------
    if (btnEncryptWallet) {
        btnEncryptWallet.addEventListener('click', async () => {
            if (!activeWalletName) return;
            const passphrase = encryptPassphraseInput.value;
            if (!passphrase || passphrase.length < 8) {
                showToast('Passphrase must be at least 8 characters', 'error');
                return;
            }
            if (!confirm('Encrypt wallet? You will need the passphrase to spend. This cannot be undone easily.')) return;
            try {
                btnEncryptWallet.disabled = true;
                const res = await fetch('/api/wallet/encrypt', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name: activeWalletName, passphrase })
                });
                const data = await res.json();
                if (data.success) {
                    showToast('Wallet encrypted — restart may be required', 'success', 6000);
                    encryptPassphraseInput.value = '';
                } else {
                    showToast(`Encrypt failed: ${data.error}`, 'error', 6000);
                }
            } catch (err) {
                showToast(`API error: ${err.message}`, 'error');
            } finally {
                btnEncryptWallet.disabled = false;
            }
        });
    }

    if (btnUnlockWallet) {
        btnUnlockWallet.addEventListener('click', async () => {
            if (!activeWalletName) return;
            const passphrase = unlockPassphraseInput.value;
            const timeout = parseInt(unlockTimeoutInput?.value || '600', 10);
            if (!passphrase) { showToast('Enter passphrase', 'error'); return; }
            try {
                const res = await fetch('/api/wallet/unlock', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name: activeWalletName, passphrase, timeout })
                });
                const data = await res.json();
                if (data.success) {
                    showToast(`Wallet unlocked for ${timeout}s`, 'success');
                    unlockPassphraseInput.value = '';
                } else {
                    showToast(`Unlock failed: ${data.error}`, 'error', 6000);
                }
            } catch (err) {
                showToast(`API error: ${err.message}`, 'error');
            }
        });
    }

    if (btnLockWallet) {
        btnLockWallet.addEventListener('click', async () => {
            if (!activeWalletName) return;
            try {
                const res = await fetch('/api/wallet/lock', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name: activeWalletName })
                });
                const data = await res.json();
                if (data.success) showToast('Wallet locked', 'success');
                else showToast(`Lock failed: ${data.error}`, 'error');
            } catch (err) {
                showToast(`API error: ${err.message}`, 'error');
            }
        });
    }

    if (btnChangePassphrase) {
        btnChangePassphrase.addEventListener('click', async () => {
            if (!activeWalletName) return;
            const oldPass = changeOldPassInput.value;
            const newPass = changeNewPassInput.value;
            if (!oldPass || !newPass || newPass.length < 8) {
                showToast('Enter current and new passphrase (min 8 chars)', 'error');
                return;
            }
            try {
                const res = await fetch('/api/wallet/change-passphrase', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name: activeWalletName, old_passphrase: oldPass, new_passphrase: newPass })
                });
                const data = await res.json();
                if (data.success) {
                    showToast('Passphrase changed', 'success');
                    changeOldPassInput.value = '';
                    changeNewPassInput.value = '';
                } else {
                    showToast(`Change failed: ${data.error}`, 'error', 6000);
                }
            } catch (err) {
                showToast(`API error: ${err.message}`, 'error');
            }
        });
    }

    async function doWalletBackup(dump) {
        if (!activeWalletName) return;
        const endpoint = dump ? '/api/wallet/dump' : '/api/wallet/backup';
        try {
            const btn = dump ? btnDumpWallet : btnBackupWallet;
            if (btn) btn.disabled = true;
            const res = await fetch(endpoint, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name: activeWalletName })
            });
            const data = await res.json();
            if (data.success) {
                showToast(`Saved to ${data.path}`, 'success', 6000);
                if (backupResult) {
                    backupResult.textContent = data.path;
                    backupResult.classList.remove('hidden');
                }
            } else {
                showToast(`Backup failed: ${data.error}`, 'error', 6000);
            }
        } catch (err) {
            showToast(`API error: ${err.message}`, 'error');
        } finally {
            if (btnBackupWallet) btnBackupWallet.disabled = false;
            if (btnDumpWallet) btnDumpWallet.disabled = false;
        }
    }

    if (btnBackupWallet) btnBackupWallet.addEventListener('click', () => doWalletBackup(false));
    if (btnDumpWallet) btnDumpWallet.addEventListener('click', () => doWalletBackup(true));

    if (btnImportWallet) {
        btnImportWallet.addEventListener('click', async () => {
            const filepath = importWalletPathInput?.value.trim();
            if (!filepath) { showToast('Enter dump file path', 'error'); return; }
            if (!confirm('Import wallet dump? This may take a while on large wallets.')) return;
            try {
                btnImportWallet.disabled = true;
                const res = await fetch('/api/wallet/import-wallet', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ filepath })
                });
                const data = await res.json();
                if (data.success) {
                    showToast('Wallet imported — check listwallets', 'success', 6000);
                    checkWalletStatus();
                } else {
                    showToast(`Import failed: ${data.error}`, 'error', 7000);
                }
            } catch (err) {
                showToast(`API error: ${err.message}`, 'error');
            } finally {
                btnImportWallet.disabled = false;
            }
        });
    }

    if (btnCreateWatchonly) {
        btnCreateWatchonly.addEventListener('click', async () => {
            const name = watchonlyNameInput?.value.trim();
            if (!name) { showToast('Enter watch-only wallet name', 'error'); return; }
            try {
                const res = await fetch('/api/wallet/create-watchonly', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name })
                });
                const data = await res.json();
                if (data.success) {
                    showToast(`Watch-only wallet "${name}" created`, 'success');
                    checkWalletStatus();
                } else {
                    showToast(`Create failed: ${data.error}`, 'error', 6000);
                }
            } catch (err) {
                showToast(`API error: ${err.message}`, 'error');
            }
        });
    }

    if (btnImportDescriptor) {
        btnImportDescriptor.addEventListener('click', async () => {
            const descriptor = importDescriptorInput?.value.trim();
            if (!activeWalletName) { showToast('Load a wallet first', 'error'); return; }
            if (!descriptor) { showToast('Enter descriptor', 'error'); return; }
            try {
                const res = await fetch('/api/wallet/import-descriptors', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name: activeWalletName, descriptor })
                });
                const data = await res.json();
                if (data.success) {
                    showToast('Descriptor imported', 'success');
                    importDescriptorInput.value = '';
                } else {
                    showToast(`Import failed: ${data.error}`, 'error', 6000);
                }
            } catch (err) {
                showToast(`API error: ${err.message}`, 'error');
            }
        });
    }

    // ----------------------------------------------------
    // Oracle CLI Terminal
    // ----------------------------------------------------
    function appendCliLine(type, text, command) {
        if (!cliOutput) return;
        const line = document.createElement('div');
        line.className = 'cli-line';
        if (type === 'cmd') {
            line.innerHTML = `<div class="cli-line-cmd">${command || text}</div>`;
        } else if (type === 'err') {
            line.innerHTML = `<div class="cli-line-err">${escapeHtml(text)}</div>`;
        } else {
            let formatted = text;
            try {
                const parsed = JSON.parse(text);
                formatted = JSON.stringify(parsed, null, 2);
            } catch { /* plain text */ }
            line.innerHTML = `<div class="cli-line-out">${escapeHtml(formatted)}</div>`;
        }
        cliOutput.appendChild(line);
        cliOutput.scrollTop = cliOutput.scrollHeight;
    }

    function escapeHtml(str) {
        return String(str)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;');
    }

    async function runCliCommand(command) {
        if (!command.trim()) return;
        const walletName = cliWalletSelect?.value || null;
        const displayCmd = walletName ? `-rpcwallet=${walletName} ${command}` : command;
        appendCliLine('cmd', command, displayCmd);

        cliHistory.push(command);
        cliHistoryIndex = cliHistory.length;

        try {
            const res = await fetch('/api/cli', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ command, wallet_name: walletName })
            });
            const data = await res.json();
            if (data.success) {
                appendCliLine('out', data.output || '(empty)');
            } else {
                appendCliLine('err', data.error || data.output || 'Command failed');
            }
        } catch (err) {
            appendCliLine('err', `API error: ${err.message}`);
        }
    }

    if (cliRunBtn) {
        cliRunBtn.addEventListener('click', () => {
            const cmd = cliInput.value.trim();
            if (cmd) {
                runCliCommand(cmd);
                cliInput.value = '';
            }
        });
    }

    if (cliInput) {
        cliInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                const cmd = cliInput.value.trim();
                if (cmd) {
                    runCliCommand(cmd);
                    cliInput.value = '';
                }
            } else if (e.key === 'ArrowUp') {
                e.preventDefault();
                if (cliHistory.length > 0) {
                    cliHistoryIndex = Math.max(0, cliHistoryIndex - 1);
                    cliInput.value = cliHistory[cliHistoryIndex] || '';
                }
            } else if (e.key === 'ArrowDown') {
                e.preventDefault();
                if (cliHistoryIndex < cliHistory.length - 1) {
                    cliHistoryIndex++;
                    cliInput.value = cliHistory[cliHistoryIndex] || '';
                } else {
                    cliHistoryIndex = cliHistory.length;
                    cliInput.value = '';
                }
            }
        });
    }

    if (cliClearBtn) {
        cliClearBtn.addEventListener('click', () => {
            if (cliOutput) {
                cliOutput.innerHTML = '<div class="cli-welcome">Terminal cleared.</div>';
            }
        });
    }

    if (cliQuickChips) {
        cliQuickChips.querySelectorAll('.cli-chip').forEach(chip => {
            chip.addEventListener('click', () => {
                const cmd = chip.dataset.cmd;
                if (cmd) runCliCommand(cmd);
            });
        });
    }

    async function fetchWalletAddresses() {
        if (!activeWalletName || !walletAddressesList) return;
        try {
            const res = await fetch(`/api/wallet/addresses?name=${encodeURIComponent(activeWalletName)}`);
            const data = await res.json();
            if (!data.success) {
                walletAddressesList.innerHTML = `<tr><td colspan="4" class="text-secondary text-center py-4">Error: ${data.error || 'Failed to load addresses'}</td></tr>`;
                return;
            }
            const addresses = JSON.parse(data.output);
            if (!addresses.length) {
                walletAddressesList.innerHTML = `<tr><td colspan="4" class="text-secondary text-center py-4">No addresses yet. Go to Receive to generate one.</td></tr>`;
                return;
            }
            addresses.sort((a, b) => b.amount - a.amount);
            walletAddressesList.innerHTML = '';
            addresses.forEach(entry => {
                const tr = document.createElement('tr');
                const label = entry.label || '—';
                const received = entry.amount.toFixed(8);
                tr.innerHTML = `
                    <td class="addr-cell" title="${entry.address}">${entry.address}</td>
                    <td>${label}</td>
                    <td>${received} BTC</td>
                    <td style="text-align: right; white-space: nowrap;">
                        <button class="addr-action-btn" data-action="copy" data-addr="${entry.address}">Copy</button>
                        <button class="addr-action-btn" data-action="receive" data-addr="${entry.address}">Receive</button>
                    </td>
                `;
                walletAddressesList.appendChild(tr);
            });
            walletAddressesList.querySelectorAll('.addr-action-btn').forEach(btn => {
                btn.addEventListener('click', () => {
                    const addr = btn.dataset.addr;
                    if (btn.dataset.action === 'copy') {
                        navigator.clipboard.writeText(addr).then(() => showToast('Address copied', 'success', 2000));
                    } else {
                        switchWalletSubTab(pillWalletReceive, walletSubReceive);
                        receiveAddressText.value = addr;
                        receiveAddressContainer.classList.remove('hidden');
                        qrCodeContainer.innerHTML = '';
                        if (typeof QRCode !== 'undefined') {
                            new QRCode(qrCodeContainer, {
                                text: addr, width: 180, height: 180,
                                colorDark: '#000000', colorLight: '#ffffff',
                                correctLevel: QRCode.CorrectLevel.M
                            });
                        }
                    }
                });
            });
        } catch (err) {
            console.error(err);
            walletAddressesList.innerHTML = `<tr><td colspan="4" class="text-secondary text-center py-4">Error loading addresses</td></tr>`;
        }
    }

    if (btnRefreshAddresses) {
        btnRefreshAddresses.addEventListener('click', fetchWalletAddresses);
    }

    if (btnSignMessage) {
        btnSignMessage.addEventListener('click', async () => {
            if (!activeWalletName) return;
            const address = msgAddressInput.value.trim();
            const message = msgTextInput.value;
            if (!address || !message) {
                showToast('Address and message are required', 'error');
                return;
            }
            try {
                btnSignMessage.disabled = true;
                const res = await fetch('/api/wallet/sign-message', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name: activeWalletName, address, message })
                });
                const data = await res.json();
                if (data.success) {
                    msgSignatureInput.value = data.signature;
                    showToast('Message signed successfully', 'success');
                } else {
                    showToast(`Sign failed: ${data.error}`, 'error', 6000);
                }
            } catch (err) {
                showToast(`API error: ${err.message}`, 'error');
            } finally {
                btnSignMessage.disabled = false;
            }
        });
    }

    if (btnVerifyMessage) {
        btnVerifyMessage.addEventListener('click', async () => {
            const address = msgAddressInput.value.trim();
            const message = msgTextInput.value;
            const signature = msgSignatureInput.value.trim();
            if (!address || !message || !signature) {
                showToast('Address, message, and signature are required', 'error');
                return;
            }
            try {
                btnVerifyMessage.disabled = true;
                const res = await fetch('/api/wallet/verify-message', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ address, message, signature })
                });
                const data = await res.json();
                if (data.success) {
                    showToast(data.valid ? 'Signature is VALID' : 'Signature is INVALID', data.valid ? 'success' : 'error', 5000);
                } else {
                    showToast(`Verify failed: ${data.error}`, 'error', 6000);
                }
            } catch (err) {
                showToast(`API error: ${err.message}`, 'error');
            } finally {
                btnVerifyMessage.disabled = false;
            }
        });
    }

    function showPsbtResult(text) {
        psbtResultContainer.textContent = text;
        psbtResultContainer.classList.remove('hidden');
        psbtResultContainer.classList.add('visible');
    }

    if (btnDecodePsbt) {
        btnDecodePsbt.addEventListener('click', async () => {
            if (!activeWalletName) return;
            const psbt = psbtDataInput.value.trim();
            if (!psbt) { showToast('Paste PSBT data first', 'error'); return; }
            try {
                btnDecodePsbt.disabled = true;
                const res = await fetch('/api/wallet/psbt/decode', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name: activeWalletName, psbt })
                });
                const data = await res.json();
                if (data.success) {
                    currentPsbt = psbt;
                    const decoded = JSON.parse(data.output);
                    showPsbtResult(JSON.stringify(decoded, null, 2));
                    showToast('PSBT decoded', 'success', 2500);
                } else {
                    showToast(`Decode failed: ${data.error}`, 'error', 6000);
                }
            } catch (err) {
                showToast(`API error: ${err.message}`, 'error');
            } finally {
                btnDecodePsbt.disabled = false;
            }
        });
    }

    if (btnSignPsbt) {
        btnSignPsbt.addEventListener('click', async () => {
            if (!activeWalletName) return;
            const psbt = psbtDataInput.value.trim();
            if (!psbt) { showToast('Paste PSBT data first', 'error'); return; }
            try {
                btnSignPsbt.disabled = true;
                const res = await fetch('/api/wallet/psbt/sign', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name: activeWalletName, psbt })
                });
                const data = await res.json();
                if (data.success) {
                    if (data.psbt) {
                        currentPsbt = data.psbt;
                        psbtDataInput.value = data.psbt;
                    }
                    const status = data.complete ? 'PSBT fully signed' : 'PSBT partially signed';
                    showPsbtResult(data.output ? JSON.stringify(JSON.parse(data.output), null, 2) : status);
                    showToast(status, data.complete ? 'success' : 'info');
                } else {
                    showToast(`Sign failed: ${data.error}`, 'error', 6000);
                }
            } catch (err) {
                showToast(`API error: ${err.message}`, 'error');
            } finally {
                btnSignPsbt.disabled = false;
            }
        });
    }

    if (btnBroadcastPsbt) {
        btnBroadcastPsbt.addEventListener('click', async () => {
            if (!activeWalletName) return;
            const psbt = psbtDataInput.value.trim() || currentPsbt;
            if (!psbt) { showToast('Paste or sign a PSBT first', 'error'); return; }
            if (!confirm('Finalize and broadcast this PSBT to the network?')) return;
            try {
                btnBroadcastPsbt.disabled = true;
                const res = await fetch('/api/wallet/psbt/finalize', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name: activeWalletName, psbt, broadcast: true })
                });
                const data = await res.json();
                if (data.success) {
                    showPsbtResult(`Broadcast successful!\nTxID: ${data.txid}\nHex: ${data.hex}`);
                    showToast(`Transaction broadcast: ${data.txid}`, 'success', 6000);
                    psbtDataInput.value = '';
                    currentPsbt = '';
                    refreshWalletData();
                    switchWalletSubTab(pillWalletHistory, walletSubHistory);
                } else {
                    showPsbtResult(data.error || 'Finalize/broadcast failed');
                    showToast(`Broadcast failed: ${data.error}`, 'error', 6000);
                }
            } catch (err) {
                showToast(`API error: ${err.message}`, 'error');
            } finally {
                btnBroadcastPsbt.disabled = false;
            }
        });
    }

    // Generate Receive Address
    btnGenerateAddress.addEventListener('click', async () => {
        if (!activeWalletName) return;
        const type = receiveAddressType.value;
        
        try {
            btnGenerateAddress.disabled = true;
            btnGenerateAddress.textContent = 'Generating...';
            
            const res = await fetch('/api/wallet/address', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name: activeWalletName, type })
            });
            const data = await res.json();
            
            if (data.success) {
                receiveAddressText.value = data.address;
                receiveAddressContainer.classList.remove('hidden');
                
                qrCodeContainer.innerHTML = '';
                
                if (typeof QRCode !== 'undefined') {
                    new QRCode(qrCodeContainer, {
                        text: data.address,
                        width: 180,
                        height: 180,
                        colorDark: "#000000",
                        colorLight: "#ffffff",
                        correctLevel: QRCode.CorrectLevel.M
                    });
                } else {
                    qrCodeContainer.innerHTML = `<p class="text-muted" style="color:#000; font-size:11px; text-align:center;">QR Code library not loaded.<br>Address is fully readable below.</p>`;
                }
            } else {
                showToast(`Failed to generate address: ${data.error}`, 'error', 6000);
            }
        } catch (err) {
            showToast(`API error: ${err.message}`, 'error');
        } finally {
            btnGenerateAddress.disabled = false;
            btnGenerateAddress.textContent = 'Generate Receive Address';
        }
    });

    // Copy Address Button
    btnCopyAddress.addEventListener('click', () => {
        const addr = receiveAddressText.value;
        if (addr) {
            navigator.clipboard.writeText(addr).then(() => showToast('Address copied', 'success', 2000));
        }
        btnCopyAddress.textContent = 'Copied!';
        setTimeout(() => { btnCopyAddress.textContent = 'Copy'; }, 1500);
    });

    // Send Coins Button
    btnSendCoins.addEventListener('click', async () => {
        if (!activeWalletName) return;
        const address = sendAddressInput.value.trim();
        const amount = parseFloat(sendAmountInput.value);
        
        if (!address) {
            showToast('Enter a valid recipient address', 'error');
            return;
        }
        if (isNaN(amount) || amount <= 0) {
            showToast('Enter a valid amount greater than 0', 'error');
            return;
        }
        
        if (!confirm(`Are you sure you want to send ${amount.toFixed(8)} BTC to ${address}?`)) {
            return;
        }
        
        const feeRate = sendFeeRateInput?.value ? parseInt(sendFeeRateInput.value, 10) : null;
        const payload = { name: activeWalletName, address, amount };
        if (feeRate && feeRate > 0) payload.fee_rate = feeRate;

        try {
            btnSendCoins.disabled = true;
            btnSendCoins.textContent = 'Sending...';

            const res = await fetch('/api/wallet/send', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            const data = await res.json();

            if (data.success) {
                showToast(`Sent ${amount} BTC — TxID: ${data.txid}`, 'success', 6000);
                sendAddressInput.value = '';
                sendAmountInput.value = '';
                switchWalletSubTab(pillWalletHistory, walletSubHistory);
                refreshWalletData();
            } else {
                showToast(`Send failed: ${data.error}`, 'error', 6000);
            }
        } catch (err) {
            showToast(`API error: ${err.message}`, 'error');
        } finally {
            btnSendCoins.disabled = false;
            btnSendCoins.textContent = 'Send Transaction';
        }
    });

    if (btnSendAdvanced) {
        btnSendAdvanced.addEventListener('click', async () => {
            if (!activeWalletName) return;
            const address = sendAdvAddressInput.value.trim();
            const amount = parseFloat(sendAdvAmountInput.value);
            const feeRate = sendAdvFeeRateInput?.value ? parseInt(sendAdvFeeRateInput.value, 10) : null;
            const inputs = getSelectedUtxoInputs();

            if (!address) { showToast('Enter recipient address', 'error'); return; }
            if (isNaN(amount) || amount <= 0) { showToast('Enter a valid amount', 'error'); return; }
            if (!inputs.length) { showToast('Select at least one UTXO', 'error'); return; }

            const selectedTotal = cachedUtxos
                .filter(u => selectedUtxoKeys.has(utxoKey(u)))
                .reduce((s, u) => s + u.amount, 0);
            if (selectedTotal < amount) {
                showToast(`Selected UTXOs (${selectedTotal.toFixed(8)} BTC) may not cover amount + fees`, 'error', 6000);
            }

            if (!confirm(`Send ${amount.toFixed(8)} BTC using ${inputs.length} selected UTXO(s)?`)) return;

            const payload = { name: activeWalletName, address, amount, inputs };
            if (feeRate && feeRate > 0) payload.fee_rate = feeRate;

            try {
                btnSendAdvanced.disabled = true;
                btnSendAdvanced.textContent = 'Building PSBT...';
                const res = await fetch('/api/wallet/send-advanced', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                const data = await res.json();
                if (data.success) {
                    const feeMsg = data.fee != null ? ` (fee: ${Number(data.fee).toFixed(8)} BTC)` : '';
                    showToast(`Sent via coin control — TxID: ${data.txid}${feeMsg}`, 'success', 7000);
                    sendAdvAddressInput.value = '';
                    sendAdvAmountInput.value = '';
                    selectedUtxoKeys.clear();
                    switchWalletSubTab(pillWalletHistory, walletSubHistory);
                    refreshWalletData();
                } else {
                    showToast(`Advanced send failed: ${data.error}`, 'error', 7000);
                }
            } catch (err) {
                showToast(`API error: ${err.message}`, 'error');
            } finally {
                btnSendAdvanced.disabled = false;
                btnSendAdvanced.textContent = 'Send with Selected Coins';
            }
        });
    }

    // ----------------------------------------------------
    // Console Logs Tab
    // ----------------------------------------------------
    async function fetchLogs() {
        try {
            const res = await fetch(`/api/logs?filter=${logFilterMode}`);
            const data = await res.json();
            
            if (data.success) {
                logText.textContent = data.logs;
                if (logAutoscroll.checked) {
                    logText.scrollTop = logText.scrollHeight;
                }
            } else {
                logText.textContent = `Error reading logs: ${data.error}`;
            }
        } catch (err) {
            logText.textContent = `API Error reading logs: ${err.message}`;
        }
    }
    
    function startLogPolling() {
        if (logIntervalId) clearInterval(logIntervalId);
        logIntervalId = setInterval(fetchLogs, 3000);
    }
    
    function stopLogPolling() {
        if (logIntervalId) {
            clearInterval(logIntervalId);
            logIntervalId = null;
        }
    }
    
    btnRefreshLogs.addEventListener('click', fetchLogs);
    
    // Quick actions handlers
    btnQuickReloadPolicy.addEventListener('click', async () => {
        if (!isNodeRunning) {
            showToast('Node is offline.', 'error');
            return;
        }
        try {
            const res = await fetch('/api/policy/apply', { method: 'POST' });
            const data = await res.json();
            if (data.success) {
                showToast('Policy applied from policy.toml', 'success');
                fetchDashboard();
                fetchBip110Status();
            } else {
                showToast(`Failed to apply policy: ${data.output || data.error}`, 'error', 6000);
            }
        } catch (err) {
            showToast(`API error: ${err.message}`, 'error');
        }
    });

    if (btnQuickMempoolInspect) {
        btnQuickMempoolInspect.addEventListener('click', async () => {
            if (isNodeRunning) {
                try {
                    const res = await fetch('/api/mempool-audit?limit=500');
                    const data = await res.json();
                    if (data.success) window._lastMempoolAudit = data.audit;
                } catch (e) { /* use cached */ }
            }
            openMempoolPolicyModal();
        });
    }

    const mempoolModalClose = document.getElementById('mempool-modal-close');
    const mempoolPolicyModal = document.getElementById('mempool-policy-modal');
    if (mempoolModalClose && mempoolPolicyModal) {
        mempoolModalClose.addEventListener('click', () => mempoolPolicyModal.classList.add('hidden'));
        mempoolPolicyModal.addEventListener('click', (e) => {
            if (e.target === mempoolPolicyModal) mempoolPolicyModal.classList.add('hidden');
        });
    }

    const btnLogsAll = document.getElementById('btn-logs-all');
    const btnLogsPolicy = document.getElementById('btn-logs-policy');
    if (btnLogsAll) btnLogsAll.addEventListener('click', () => { logFilterMode = 'all'; fetchLogs(); });
    if (btnLogsPolicy) btnLogsPolicy.addEventListener('click', () => { logFilterMode = 'policy'; fetchLogs(); });

    // ----------------------------------------------------
    // Application Initialization
    // ----------------------------------------------------
    startMetricsPolling();
});
