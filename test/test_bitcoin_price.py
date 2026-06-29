"""
Oracle Knots - Bitcoin Price Service Tests

Unit tests for bitcoin_price.py module

Tests cover:
- Price caching
- API data fetching
- Data formatting
- Error handling
"""

import unittest
import time
from unittest.mock import patch, MagicMock
from api.bitcoin_price import BitcoinPriceService, PriceCache


class TestPriceCache(unittest.TestCase):
    """Test caching functionality"""

    def setUp(self):
        self.cache = PriceCache(ttl_seconds=1)

    def test_cache_hit(self):
        """Test that cached values are returned within TTL"""
        call_count = 0

        @self.cache.cached(ttl=1)
        def expensive_function():
            nonlocal call_count
            call_count += 1
            return {"value": "result"}

        # First call - should execute
        result1 = expensive_function()
        self.assertEqual(result1["value"], "result")
        self.assertEqual(call_count, 1)

        # Second call within TTL - should use cache
        result2 = expensive_function()
        self.assertEqual(result2["value"], "result")
        self.assertEqual(call_count, 1)  # Not incremented

    def test_cache_miss(self):
        """Test that cache expires after TTL"""
        call_count = 0

        @self.cache.cached(ttl=1)
        def expensive_function():
            nonlocal call_count
            call_count += 1
            return {"value": f"result_{call_count}"}

        # First call
        result1 = expensive_function()
        self.assertEqual(call_count, 1)

        # Wait for cache to expire
        time.sleep(1.1)

        # Second call after TTL - should execute again
        result2 = expensive_function()
        self.assertEqual(call_count, 2)
        self.assertEqual(result2["value"], "result_2")


class TestBitcoinPriceService(unittest.TestCase):
    """Test BitcoinPriceService"""

    def setUp(self):
        self.service = BitcoinPriceService()

    @patch('requests.Session.get')
    def test_fetch_coingecko_price(self, mock_get):
        """Test CoinGecko API response parsing"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'bitcoin': {
                'usd': 45000.50,
                'usd_24h_change': 2.5,
                'usd_market_cap': 900000000000,
                'usd_24h_vol': 25000000000,
                'eur': 42000.00,
                'eur_24h_change': 2.5,
                'gbp': 35000.00,
                'gbp_24h_change': 2.5,
                'jpy': 5000000.00,
                'jpy_24h_change': 2.5,
                'cad': 60000.00,
                'cad_24h_change': 2.5,
                'aud': 70000.00,
                'aud_24h_change': 2.5,
                'circulating_supply': 21000000
            }
        }
        mock_get.return_value = mock_response

        result = self.service._fetch_coingecko_price()

        self.assertEqual(result['usd'], 45000.50)
        self.assertEqual(result['usd_24h_change'], 2.5)
        self.assertEqual(result['usd_market_cap'], 900000000000)
        self.assertEqual(result['circulating_supply'], 21000000)

    @patch('requests.Session.get')
    def test_price_history(self, mock_get):
        """Test price history fetching"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'prices': [
                [1234567890000, 44000],
                [1234654290000, 45000],
                [1234740690000, 45500]
            ]
        }
        mock_get.return_value = mock_response

        result = self.service.get_price_history(days=7)

        self.assertEqual(len(result), 3)
        self.assertEqual(result[0]['price'], 44000)
        self.assertEqual(result[1]['price'], 45000)

    def test_format_price(self):
        """Test price formatting"""
        # USD
        formatted = self.service.format_price(45000.50, 'usd')
        self.assertEqual(formatted, '$45,000.50')

        # EUR
        formatted = self.service.format_price(42000.00, 'eur')
        self.assertEqual(formatted, '€42,000.00')

        # GBP
        formatted = self.service.format_price(35000.00, 'gbp')
        self.assertEqual(formatted, '£35,000.00')

        # JPY
        formatted = self.service.format_price(5000000.00, 'jpy')
        self.assertEqual(formatted, '¥5,000,000')

    @patch('requests.Session.get')
    def test_error_fallback(self, mock_get):
        """Test fallback to Kraken when CoinGecko fails"""
        # First call to CoinGecko fails
        mock_get.side_effect = Exception("Network error")

        result = self.service.current_price

        # Should have error key
        self.assertIn('error', result)

    @patch('requests.Session.get')
    def test_market_data(self, mock_get):
        """Test market data aggregation"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'bitcoin': {
                'usd': 45000.50,
                'usd_24h_change': 2.5,
                'usd_market_cap': 900000000000,
                'usd_24h_vol': 25000000000,
                'eur': 42000.00,
                'eur_24h_change': 2.5,
                'gbp': 35000.00,
                'gbp_24h_change': 2.5,
                'jpy': 5000000.00,
                'jpy_24h_change': 2.5,
                'cad': 60000.00,
                'cad_24h_change': 2.5,
                'aud': 70000.00,
                'aud_24h_change': 2.5,
                'circulating_supply': 21000000
            }
        }
        mock_get.return_value = mock_response

        # Clear cache to force fresh fetch
        self.service.cache.cache.clear()

        market_data = self.service.get_market_data()

        self.assertTrue(market_data)
        self.assertIn('current_price', market_data)
        self.assertIn('market_cap', market_data)
        self.assertIn('volume_24h', market_data)


class TestBitcoinPriceIntegration(unittest.TestCase):
    """Integration tests with actual API calls (optional)"""

    def setUp(self):
        self.service = BitcoinPriceService()

    @patch('requests.Session.get')
    def test_complete_workflow(self, mock_get):
        """Test complete workflow: fetch price, history, format"""
        # Mock CoinGecko response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'bitcoin': {
                'usd': 45000.50,
                'usd_24h_change': 2.5,
                'usd_market_cap': 900000000000,
                'usd_24h_vol': 25000000000,
                'eur': 42000.00,
                'eur_24h_change': 2.5,
                'gbp': 35000.00,
                'gbp_24h_change': 2.5,
                'jpy': 5000000.00,
                'jpy_24h_change': 2.5,
                'cad': 60000.00,
                'cad_24h_change': 2.5,
                'aud': 70000.00,
                'aud_24h_change': 2.5,
                'circulating_supply': 21000000
            }
        }
        mock_get.return_value = mock_response

        # Get price
        price = self.service.current_price
        self.assertEqual(price['usd'], 45000.50)

        # Get market data
        market = self.service.get_market_data()
        self.assertTrue(market)

        # Format price
        formatted = self.service.format_price(price['usd'], 'usd')
        self.assertIn('$45,000', formatted)


class TestPriceCurrencies(unittest.TestCase):
    """Test currency support"""

    def setUp(self):
        self.service = BitcoinPriceService()

    def test_supported_currencies(self):
        """Test that all major currencies are supported"""
        currencies = ['usd', 'eur', 'gbp', 'jpy', 'cad', 'aud']

        for currency in currencies:
            # Should not raise error
            formatted = self.service.format_price(1000.00, currency)
            self.assertTrue(formatted)
            self.assertGreater(len(formatted), 0)


def run_tests():
    """Run all tests"""
    unittest.main(argv=[''], exit=False, verbosity=2)


if __name__ == '__main__':
    run_tests()
