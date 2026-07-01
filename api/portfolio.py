"""
Oracle Knots - Portfolio Manager

Tracks total BTC holdings across all loaded wallets, records daily snapshots
to SQLite, computes P&L vs yesterday, and exports CSV.

Dependencies:
- api.bitcoin_price.BitcoinPriceService (price data)
- run_bitcoin_cli / get_node_context injected from gui.py (avoids circular imports)
"""

import sqlite3
import os
import json
import csv
import io
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from api.bitcoin_price import BitcoinPriceService

DB_PATH = os.path.expanduser("~/.oracle-knots/portfolio.db")

SUPPORTED_CURRENCIES = ['usd', 'eur', 'gbp', 'jpy', 'cad', 'aud']


class PortfolioManager:
    """
    Manages portfolio tracking across all Bitcoin wallets.

    Accepts run_bitcoin_cli and get_node_context as constructor arguments
    to avoid circular imports with gui.py.
    """

    def __init__(self, run_cli_func, get_node_ctx_func):
        self.run_cli = run_cli_func
        self.get_node_ctx = get_node_ctx_func
        self.price_service = BitcoinPriceService()
        self.db_path = DB_PATH
        self._init_db()

    def _init_db(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        with self._get_db() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS portfolio_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL UNIQUE,
                    total_btc REAL NOT NULL,
                    total_unconfirmed_btc REAL NOT NULL DEFAULT 0,
                    total_value_usd REAL NOT NULL,
                    price_usd REAL NOT NULL,
                    wallet_count INTEGER NOT NULL DEFAULT 0,
                    wallets_json TEXT
                );
                CREATE TABLE IF NOT EXISTS address_labels (
                    address TEXT PRIMARY KEY,
                    label TEXT NOT NULL DEFAULT '',
                    category TEXT NOT NULL DEFAULT 'personal',
                    wallet_name TEXT,
                    created_at TEXT DEFAULT (datetime('now'))
                );
            """)

    def _get_db(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _get_wallet_balance(self, wallet_name: str, datadir: str, network: str) -> Tuple[float, float]:
        success, output = self.run_cli(
            ["getwalletinfo"], datadir, network, wallet_name=wallet_name
        )
        if not success:
            return 0.0, 0.0
        try:
            data = json.loads(output)
            return float(data.get("balance", 0.0)), float(data.get("unconfirmed_balance", 0.0))
        except (json.JSONDecodeError, TypeError, ValueError):
            return 0.0, 0.0

    def get_portfolio_snapshot(self, currency: str = 'usd') -> Dict:
        if currency not in SUPPORTED_CURRENCIES:
            currency = 'usd'

        running, datadir, network = self.get_node_ctx()
        if not running:
            return {
                'success': False,
                'error': 'Node is offline',
                'wallets': [],
                'total_btc': 0.0,
                'total_value': 0.0,
                'currency': currency,
            }

        # Get list of loaded wallets
        ok, output = self.run_cli(["listwallets"], datadir, network)
        if not ok:
            return {'success': False, 'error': f'Could not list wallets: {output}', 'wallets': [], 'total_btc': 0.0, 'total_value': 0.0, 'currency': currency}

        try:
            wallet_names = json.loads(output)
        except json.JSONDecodeError:
            wallet_names = []

        # Fetch balance for each wallet
        wallet_details = []
        total_btc = 0.0
        total_unconfirmed = 0.0

        for name in wallet_names:
            bal, unconf = self._get_wallet_balance(name, datadir, network)
            total_btc += bal
            total_unconfirmed += unconf
            wallet_details.append({'name': name, 'btc': bal, 'unconfirmed': unconf})

        # Fetch price (uses 60-second cache — no extra API calls during normal polling)
        try:
            price_data = self.price_service.current_price
            price_in_currency = float(price_data.get(currency, price_data.get('usd', 0)))
            price_usd = float(price_data.get('usd', 0))
            change_24h = float(price_data.get(f'{currency}_24h_change', price_data.get('usd_24h_change', 0)))
        except Exception:
            price_in_currency = 0.0
            price_usd = 0.0
            change_24h = 0.0

        total_value = total_btc * price_in_currency

        # Add per-wallet fiat values
        for w in wallet_details:
            w['value'] = w['btc'] * price_in_currency

        return {
            'success': True,
            'currency': currency,
            'total_btc': total_btc,
            'total_unconfirmed_btc': total_unconfirmed,
            'total_value': total_value,
            'price': price_in_currency,
            'price_usd': price_usd,
            'price_change_24h': change_24h,
            'wallet_count': len(wallet_names),
            'wallets': wallet_details,
            'updated_at': time.time(),
        }

    def record_daily_snapshot(self) -> bool:
        """
        Record today's portfolio snapshot to DB. Idempotent — multiple calls
        on the same day insert only once (INSERT OR IGNORE on the UNIQUE date).

        Returns True if a new row was inserted, False if today's row already existed.
        """
        snap = self.get_portfolio_snapshot('usd')
        if not snap.get('success'):
            return False

        today = datetime.now().strftime('%Y-%m-%d')
        wallets_json = json.dumps(snap.get('wallets', []))

        try:
            with self._get_db() as conn:
                cursor = conn.execute(
                    """INSERT OR IGNORE INTO portfolio_history
                       (date, total_btc, total_unconfirmed_btc, total_value_usd, price_usd, wallet_count, wallets_json)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (
                        today,
                        snap['total_btc'],
                        snap['total_unconfirmed_btc'],
                        snap['total_value'],
                        snap['price_usd'],
                        snap['wallet_count'],
                        wallets_json,
                    )
                )
                inserted = cursor.rowcount > 0
            if inserted:
                print(f"[portfolio] Snapshot recorded for {today}: {snap['total_btc']:.8f} BTC")
            return inserted
        except Exception as e:
            print(f"[portfolio] Failed to record snapshot: {e}")
            return False

    def get_portfolio_history(self, days: int = 30, currency: str = 'usd') -> Dict:
        """
        Return historical portfolio snapshots for charting.

        Note: Snapshots are stored in USD. For other currencies we apply the
        current price ratio as an approximation (accurate multi-currency history
        is deferred to a future iteration).
        """
        days = min(max(days, 1), 3650)
        if currency not in SUPPORTED_CURRENCIES:
            currency = 'usd'

        try:
            with self._get_db() as conn:
                rows = conn.execute(
                    """SELECT date, total_btc, total_unconfirmed_btc, total_value_usd, price_usd, wallet_count
                       FROM portfolio_history
                       ORDER BY date DESC
                       LIMIT ?""",
                    (days,)
                ).fetchall()
        except Exception as e:
            return {'success': False, 'error': str(e), 'data': [], 'has_enough_data': False}

        rows = list(reversed(rows))  # chronological order

        # Currency conversion ratio
        ratio = 1.0
        if currency != 'usd':
            try:
                price_data = self.price_service.current_price
                usd_price = float(price_data.get('usd', 1) or 1)
                currency_price = float(price_data.get(currency, usd_price) or usd_price)
                ratio = currency_price / usd_price
            except Exception:
                ratio = 1.0

        data = []
        for row in rows:
            value = row['total_value_usd'] * ratio
            data.append({
                'date': row['date'],
                'total_btc': row['total_btc'],
                'total_value': value,
                'price_usd': row['price_usd'],
                'wallet_count': row['wallet_count'],
            })

        has_enough = len(data) >= 2
        min_value = min((d['total_value'] for d in data), default=0)
        max_value = max((d['total_value'] for d in data), default=0)
        change_pct = 0.0
        change_value = 0.0
        if len(data) >= 2:
            first_val = data[0]['total_value']
            last_val = data[-1]['total_value']
            change_value = last_val - first_val
            change_pct = (change_value / first_val * 100) if first_val else 0.0

        return {
            'success': True,
            'data': data,
            'days_requested': days,
            'days_available': len(data),
            'has_enough_data': has_enough,
            'currency': currency,
            'min_value': min_value,
            'max_value': max_value,
            'change': {'pct': change_pct, 'value': change_value},
            'hint': "Keep Oracle Knots running daily to build your history. Check back tomorrow!" if not has_enough else None,
        }

    def calculate_pl(self, currency: str = 'usd') -> Dict:
        """
        Compare today's live snapshot against yesterday's DB record to compute P&L.
        """
        if currency not in SUPPORTED_CURRENCIES:
            currency = 'usd'

        today = datetime.now().strftime('%Y-%m-%d')
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')

        snap = self.get_portfolio_snapshot(currency)
        if not snap.get('success'):
            return {'success': False, 'error': snap.get('error', 'Node offline'), 'currency': currency}

        today_value = snap['total_value']
        today_btc = snap['total_btc']

        try:
            with self._get_db() as conn:
                yest_row = conn.execute(
                    "SELECT total_btc, total_value_usd, price_usd FROM portfolio_history WHERE date = ?",
                    (yesterday,)
                ).fetchone()
                days_tracked = conn.execute(
                    "SELECT COUNT(*) FROM portfolio_history"
                ).fetchone()[0]
        except Exception as e:
            return {'success': False, 'error': str(e), 'currency': currency}

        if not yest_row:
            return {
                'success': False,
                'reason': 'no_history',
                'days_tracked': days_tracked,
                'currency': currency,
                'today': {'value': today_value, 'btc': today_btc, 'date': today},
            }

        # Apply currency ratio to yesterday's USD value
        ratio = 1.0
        if currency != 'usd':
            try:
                price_data = self.price_service.current_price
                usd_price = float(price_data.get('usd', 1) or 1)
                cur_price = float(price_data.get(currency, usd_price) or usd_price)
                ratio = cur_price / usd_price
            except Exception:
                ratio = 1.0

        yest_value = yest_row['total_value_usd'] * ratio
        yest_btc = yest_row['total_btc']

        change_value = today_value - yest_value
        change_pct = (change_value / yest_value * 100) if yest_value else 0.0
        change_btc = today_btc - yest_btc

        return {
            'success': True,
            'currency': currency,
            'today': {'value': today_value, 'btc': today_btc, 'date': today},
            'yesterday': {'value': yest_value, 'btc': yest_btc, 'date': yesterday},
            'change': {'value': change_value, 'pct': change_pct, 'btc': change_btc},
            'direction': 'up' if change_value >= 0 else 'down',
            'days_tracked': days_tracked,
        }

    def export_csv(self, days: int = 365) -> str:
        days = min(max(days, 1), 3650)
        try:
            with self._get_db() as conn:
                rows = conn.execute(
                    """SELECT date, total_btc, total_unconfirmed_btc, total_value_usd, price_usd, wallet_count
                       FROM portfolio_history
                       ORDER BY date DESC
                       LIMIT ?""",
                    (days,)
                ).fetchall()
        except Exception:
            rows = []

        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(['Date', 'Total BTC', 'Unconfirmed BTC', 'Total Value (USD)', 'BTC Price (USD)', 'Wallets'])
        for row in reversed(rows):
            writer.writerow([
                row['date'],
                f"{row['total_btc']:.8f}",
                f"{row['total_unconfirmed_btc']:.8f}",
                f"{row['total_value_usd']:.2f}",
                f"{row['price_usd']:.2f}",
                row['wallet_count'],
            ])
        return buf.getvalue()

    def get_stats(self) -> Dict:
        try:
            with self._get_db() as conn:
                count = conn.execute("SELECT COUNT(*) FROM portfolio_history").fetchone()[0]
                if count > 0:
                    oldest = conn.execute("SELECT MIN(date) FROM portfolio_history").fetchone()[0]
                    newest = conn.execute("SELECT MAX(date) FROM portfolio_history").fetchone()[0]
                else:
                    oldest = newest = None
        except Exception as e:
            return {'success': False, 'error': str(e)}

        return {
            'success': True,
            'days_tracked': count,
            'oldest_date': oldest,
            'newest_date': newest,
            'db_path': self.db_path,
        }

    def start_daily_scheduler(self):
        """
        Daemon thread: records a snapshot immediately on startup, then every day at 00:05 AM.
        Run as daemon=True so it dies when the main window closes.
        """
        self.record_daily_snapshot()
        while True:
            now = datetime.now()
            next_run = (now + timedelta(days=1)).replace(hour=0, minute=5, second=0, microsecond=0)
            sleep_secs = (next_run - now).total_seconds()
            time.sleep(sleep_secs)
            self.record_daily_snapshot()
