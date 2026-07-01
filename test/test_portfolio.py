"""
Oracle Knots - Portfolio Manager Tests

Unit tests for api/portfolio.py

Tests cover:
- Database initialization
- Wallet balance aggregation
- Daily snapshot recording (idempotency)
- Portfolio history retrieval
- P&L calculation
- CSV export
"""

import unittest
import json
import os
import csv
import io
import tempfile
import shutil
import sys
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

import api.portfolio as portfolio_module


def _make_manager(tmpdir, mock_run_cli=None, mock_get_ctx=None):
    """Helper: create a PortfolioManager with a temp DB path."""
    portfolio_module.DB_PATH = os.path.join(tmpdir, 'portfolio.db')
    if mock_run_cli is None:
        mock_run_cli = MagicMock(return_value=(False, 'not connected'))
    if mock_get_ctx is None:
        mock_get_ctx = MagicMock(return_value=(False, '/tmp', 'mainnet'))
    return portfolio_module.PortfolioManager(mock_run_cli, mock_get_ctx)


class TestPortfolioManagerDB(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.mock_run_cli = MagicMock()
        self.mock_get_ctx = MagicMock(return_value=(False, '/tmp', 'mainnet'))
        self.manager = _make_manager(self.tmpdir, self.mock_run_cli, self.mock_get_ctx)

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_db_initialization_creates_tables(self):
        with self.manager._get_db() as conn:
            tables = {row[0] for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()}
        self.assertIn('portfolio_history', tables)
        self.assertIn('address_labels', tables)

    def test_db_path_directory_created(self):
        self.assertTrue(os.path.isfile(self.manager.db_path))

    def test_get_wallet_balance_success(self):
        self.mock_run_cli.return_value = (
            True, json.dumps({'balance': 0.5, 'unconfirmed_balance': 0.02})
        )
        bal, unconf = self.manager._get_wallet_balance('my_wallet', '/tmp', 'mainnet')
        self.assertAlmostEqual(bal, 0.5)
        self.assertAlmostEqual(unconf, 0.02)

    def test_get_wallet_balance_cli_failure(self):
        self.mock_run_cli.return_value = (False, 'Wallet not loaded')
        bal, unconf = self.manager._get_wallet_balance('bad_wallet', '/tmp', 'mainnet')
        self.assertEqual(bal, 0.0)
        self.assertEqual(unconf, 0.0)

    def test_get_wallet_balance_invalid_json(self):
        self.mock_run_cli.return_value = (True, 'not json')
        bal, unconf = self.manager._get_wallet_balance('wallet', '/tmp', 'mainnet')
        self.assertEqual(bal, 0.0)
        self.assertEqual(unconf, 0.0)


class TestPortfolioSnapshot(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.mock_run_cli = MagicMock()
        self.mock_get_ctx = MagicMock()
        self.manager = _make_manager(self.tmpdir, self.mock_run_cli, self.mock_get_ctx)

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_snapshot_node_offline(self):
        self.mock_get_ctx.return_value = (False, '/tmp', 'mainnet')
        result = self.manager.get_portfolio_snapshot()
        self.assertFalse(result['success'])
        self.assertIn('error', result)
        self.assertEqual(result['total_btc'], 0.0)

    def test_snapshot_no_wallets(self):
        self.mock_get_ctx.return_value = (True, '/tmp', 'mainnet')
        self.mock_run_cli.return_value = (True, json.dumps([]))
        with patch.object(self.manager.price_service, '_fetch_current_price', return_value={'usd': 50000, 'usd_24h_change': 1.0}):
            result = self.manager.get_portfolio_snapshot()
        self.assertTrue(result['success'])
        self.assertEqual(result['total_btc'], 0.0)
        self.assertEqual(len(result['wallets']), 0)

    def test_snapshot_multiple_wallets_sums_correctly(self):
        self.mock_get_ctx.return_value = (True, '/tmp', 'mainnet')

        def mock_cli(args, datadir=None, network='mainnet', wallet_name=None, timeout=5.0):
            if args == ['listwallets']:
                return (True, json.dumps(['wallet_a', 'wallet_b']))
            if args == ['getwalletinfo']:
                if wallet_name == 'wallet_a':
                    return (True, json.dumps({'balance': 0.3, 'unconfirmed_balance': 0.0}))
                if wallet_name == 'wallet_b':
                    return (True, json.dumps({'balance': 0.7, 'unconfirmed_balance': 0.05}))
            return (False, 'error')

        self.mock_run_cli.side_effect = mock_cli
        with patch.object(self.manager.price_service, '_fetch_current_price', return_value={'usd': 100000, 'usd_24h_change': 0.0}):
            result = self.manager.get_portfolio_snapshot('usd')

        self.assertTrue(result['success'])
        self.assertAlmostEqual(result['total_btc'], 1.0)
        self.assertAlmostEqual(result['total_value'], 100000.0)
        self.assertEqual(result['wallet_count'], 2)
        self.assertEqual(len(result['wallets']), 2)

    def test_snapshot_unsupported_currency_falls_back_to_usd(self):
        self.mock_get_ctx.return_value = (True, '/tmp', 'mainnet')
        self.mock_run_cli.return_value = (True, json.dumps([]))
        with patch.object(self.manager.price_service, '_fetch_current_price', return_value={'usd': 50000, 'usd_24h_change': 0.0}):
            result = self.manager.get_portfolio_snapshot('xyz')
        self.assertEqual(result['currency'], 'usd')


class TestDailySnapshot(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.mock_run_cli = MagicMock()
        self.mock_get_ctx = MagicMock()
        self.manager = _make_manager(self.tmpdir, self.mock_run_cli, self.mock_get_ctx)

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _mock_snapshot(self):
        return {
            'success': True,
            'total_btc': 0.5,
            'total_unconfirmed_btc': 0.0,
            'total_value': 25000.0,
            'price_usd': 50000.0,
            'price': 50000.0,
            'wallet_count': 1,
            'wallets': [],
            'updated_at': 1000,
        }

    def test_record_daily_snapshot_inserts_row(self):
        with patch.object(self.manager, 'get_portfolio_snapshot', return_value=self._mock_snapshot()):
            inserted = self.manager.record_daily_snapshot()
        self.assertTrue(inserted)
        with self.manager._get_db() as conn:
            count = conn.execute("SELECT COUNT(*) FROM portfolio_history").fetchone()[0]
        self.assertEqual(count, 1)

    def test_record_daily_snapshot_is_idempotent(self):
        with patch.object(self.manager, 'get_portfolio_snapshot', return_value=self._mock_snapshot()):
            first = self.manager.record_daily_snapshot()
            second = self.manager.record_daily_snapshot()
        self.assertTrue(first)
        self.assertFalse(second)
        with self.manager._get_db() as conn:
            count = conn.execute("SELECT COUNT(*) FROM portfolio_history").fetchone()[0]
        self.assertEqual(count, 1)

    def test_record_snapshot_node_offline_returns_false(self):
        with patch.object(self.manager, 'get_portfolio_snapshot', return_value={'success': False, 'error': 'offline'}):
            result = self.manager.record_daily_snapshot()
        self.assertFalse(result)


class TestPortfolioHistory(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.manager = _make_manager(self.tmpdir)

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _insert_days(self, n):
        with self.manager._get_db() as conn:
            for i in range(n):
                date = (datetime.now() - timedelta(days=n - 1 - i)).strftime('%Y-%m-%d')
                conn.execute(
                    "INSERT OR IGNORE INTO portfolio_history (date, total_btc, total_unconfirmed_btc, total_value_usd, price_usd, wallet_count) VALUES (?,?,?,?,?,?)",
                    (date, 0.5 + i * 0.01, 0, 25000 + i * 500, 50000 + i * 100, 1)
                )

    def test_history_empty_returns_has_enough_data_false(self):
        result = self.manager.get_portfolio_history(days=30)
        self.assertTrue(result['success'])
        self.assertFalse(result['has_enough_data'])
        self.assertEqual(result['data'], [])

    def test_history_one_row_not_enough_for_chart(self):
        self._insert_days(1)
        result = self.manager.get_portfolio_history(days=30)
        self.assertFalse(result['has_enough_data'])

    def test_history_two_rows_enough(self):
        self._insert_days(2)
        result = self.manager.get_portfolio_history(days=30)
        self.assertTrue(result['has_enough_data'])

    def test_history_chronological_order(self):
        self._insert_days(5)
        result = self.manager.get_portfolio_history(days=30)
        dates = [d['date'] for d in result['data']]
        self.assertEqual(dates, sorted(dates))

    def test_history_respects_days_limit(self):
        self._insert_days(10)
        result = self.manager.get_portfolio_history(days=5)
        self.assertLessEqual(len(result['data']), 5)

    def test_history_hint_present_when_not_enough_data(self):
        result = self.manager.get_portfolio_history(days=30)
        self.assertIsNotNone(result['hint'])

    def test_history_hint_none_when_enough_data(self):
        self._insert_days(5)
        result = self.manager.get_portfolio_history(days=30)
        self.assertIsNone(result['hint'])


class TestPLCalculation(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.mock_run_cli = MagicMock()
        self.mock_get_ctx = MagicMock(return_value=(True, '/tmp', 'mainnet'))
        self.manager = _make_manager(self.tmpdir, self.mock_run_cli, self.mock_get_ctx)

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _insert_yesterday(self, btc=0.5, value_usd=24000.0, price_usd=48000.0):
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        with self.manager._get_db() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO portfolio_history (date, total_btc, total_unconfirmed_btc, total_value_usd, price_usd, wallet_count) VALUES (?,?,?,?,?,?)",
                (yesterday, btc, 0.0, value_usd, price_usd, 1)
            )

    def test_calculate_pl_no_history(self):
        with patch.object(self.manager, 'get_portfolio_snapshot', return_value={
            'success': True, 'total_btc': 0.5, 'total_value': 25000, 'currency': 'usd'
        }):
            result = self.manager.calculate_pl('usd')
        self.assertFalse(result['success'])
        self.assertEqual(result['reason'], 'no_history')
        self.assertIn('days_tracked', result)

    def test_calculate_pl_gain(self):
        self._insert_yesterday(btc=0.5, value_usd=24000.0)
        with patch.object(self.manager, 'get_portfolio_snapshot', return_value={
            'success': True, 'total_btc': 0.5, 'total_value': 25000.0, 'currency': 'usd'
        }):
            result = self.manager.calculate_pl('usd')
        self.assertTrue(result['success'])
        self.assertAlmostEqual(result['change']['value'], 1000.0)
        self.assertEqual(result['direction'], 'up')

    def test_calculate_pl_loss(self):
        self._insert_yesterday(btc=0.5, value_usd=26000.0)
        with patch.object(self.manager, 'get_portfolio_snapshot', return_value={
            'success': True, 'total_btc': 0.5, 'total_value': 25000.0, 'currency': 'usd'
        }):
            result = self.manager.calculate_pl('usd')
        self.assertTrue(result['success'])
        self.assertAlmostEqual(result['change']['value'], -1000.0)
        self.assertEqual(result['direction'], 'down')

    def test_calculate_pl_node_offline(self):
        with patch.object(self.manager, 'get_portfolio_snapshot', return_value={
            'success': False, 'error': 'Node is offline'
        }):
            result = self.manager.calculate_pl('usd')
        self.assertFalse(result['success'])


class TestCSVExport(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.manager = _make_manager(self.tmpdir)

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_export_csv_empty_returns_header_only(self):
        csv_str = self.manager.export_csv()
        lines = [l for l in csv_str.strip().split('\n') if l]
        self.assertEqual(len(lines), 1)
        self.assertIn('Date', lines[0])
        self.assertIn('Total BTC', lines[0])

    def test_export_csv_format_with_data(self):
        with self.manager._get_db() as conn:
            conn.execute(
                "INSERT INTO portfolio_history (date, total_btc, total_unconfirmed_btc, total_value_usd, price_usd, wallet_count) VALUES (?,?,?,?,?,?)",
                ('2026-06-15', 0.5, 0.0, 25000.0, 50000.0, 1)
            )
        csv_str = self.manager.export_csv()
        reader = csv.reader(io.StringIO(csv_str))
        rows = list(reader)
        self.assertGreaterEqual(len(rows), 2)
        self.assertIn('2026-06-15', rows[1][0])
        self.assertIn('0.50000000', rows[1][1])

    def test_export_csv_respects_days_limit(self):
        with self.manager._get_db() as conn:
            for i in range(10):
                date = f"2026-06-{i+1:02d}"
                conn.execute(
                    "INSERT INTO portfolio_history (date, total_btc, total_unconfirmed_btc, total_value_usd, price_usd, wallet_count) VALUES (?,?,?,?,?,?)",
                    (date, 0.1, 0.0, 5000.0, 50000.0, 1)
                )
        csv_str = self.manager.export_csv(days=5)
        reader = csv.reader(io.StringIO(csv_str))
        rows = list(reader)
        # header + up to 5 data rows
        self.assertLessEqual(len(rows) - 1, 5)


class TestPortfolioStats(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.manager = _make_manager(self.tmpdir)

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_stats_empty_db(self):
        result = self.manager.get_stats()
        self.assertTrue(result['success'])
        self.assertEqual(result['days_tracked'], 0)
        self.assertIsNone(result['oldest_date'])

    def test_stats_with_data(self):
        with self.manager._get_db() as conn:
            conn.execute(
                "INSERT INTO portfolio_history (date, total_btc, total_unconfirmed_btc, total_value_usd, price_usd, wallet_count) VALUES (?,?,?,?,?,?)",
                ('2026-06-15', 0.5, 0.0, 25000.0, 50000.0, 1)
            )
        result = self.manager.get_stats()
        self.assertEqual(result['days_tracked'], 1)
        self.assertEqual(result['oldest_date'], '2026-06-15')
        self.assertEqual(result['newest_date'], '2026-06-15')


if __name__ == '__main__':
    unittest.main()
