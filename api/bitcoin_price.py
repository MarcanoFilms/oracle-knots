"""
Oracle Knots - Bitcoin Price & Market Data API

Provides real-time Bitcoin prices in multiple currencies with caching.
Uses CoinGecko API (free, no key required).

Features:
- Current price in 6+ currencies (USD, EUR, GBP, JPY, CAD, AUD)
- 24h change with color coding
- Market cap, volume, supply data
- Historical price data for sparkline charts
- Intelligent caching (60-second TTL)
- Fallback support (Kraken API as backup)

Dependencies: requests (standard library HTTP)
No external dependencies needed for basic functionality.
"""

import requests
import time
import json
from functools import wraps
from typing import Dict, List, Optional, Tuple
from decimal import Decimal


class PriceCache:
    """Simple in-memory cache with TTL"""

    def __init__(self, ttl_seconds: int = 60):
        self.cache = {}
        self.ttl = ttl_seconds

    def cached(self, ttl: Optional[int] = None):
        """Decorator for caching function results"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Create cache key from function name and args
                key = f"{func.__name__}_{str(args)}_{str(kwargs)}"

                # Check cache
                if key in self.cache:
                    value, timestamp = self.cache[key]
                    if time.time() - timestamp < (ttl or self.ttl):
                        return value

                # Call function and cache result
                result = func(*args, **kwargs)
                self.cache[key] = (result, time.time())
                return result

            return wrapper
        return decorator


class BitcoinPriceService:
    """
    Fetch Bitcoin prices from public APIs (no authentication required)

    Primary: CoinGecko API
    Fallback: Kraken API
    """

    # API Endpoints (free, public access)
    COINGECKO_SIMPLE = "https://api.coingecko.com/api/v3/simple/price"
    COINGECKO_MARKET = "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart"
    KRAKEN_TICKER = "https://api.kraken.com/0/public/Ticker"

    # Cache settings
    PRICE_CACHE_TTL = 60  # 60 seconds for current price
    HISTORY_CACHE_TTL = 300  # 5 minutes for historical data

    # Request settings
    REQUEST_TIMEOUT = 5  # seconds
    USER_AGENT = "OracleKnots/1.0"

    def __init__(self):
        self.cache = PriceCache()
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": self.USER_AGENT})

    @property
    def current_price(self) -> Dict:
        """
        Get current Bitcoin price in multiple currencies

        Returns:
            {
                'usd': 45000.50,
                'usd_24h_change': 2.5,
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
                'usd_market_cap': 900000000000,
                'usd_24h_vol': 25000000000,
                'circulating_supply': 21000000,
                'timestamp': 1234567890,
                'source': 'coingecko'
            }
        """
        return self._fetch_current_price()

    @PriceCache().cached(ttl=PRICE_CACHE_TTL)
    def _fetch_current_price(self) -> Dict:
        """Internal method with caching"""
        try:
            data = self._fetch_coingecko_price()
            if data:
                data['source'] = 'coingecko'
                data['timestamp'] = time.time()
                return data
        except Exception as e:
            print(f"CoinGecko API error: {e}")

        # Fallback to Kraken
        try:
            data = self._fetch_kraken_price()
            if data:
                data['source'] = 'kraken'
                data['timestamp'] = time.time()
                return data
        except Exception as e:
            print(f"Kraken API error: {e}")

        # Return cached data or error
        return {
            'error': 'Unable to fetch price data',
            'usd': 0,
            'timestamp': time.time()
        }

    def _fetch_coingecko_price(self) -> Dict:
        """Fetch from CoinGecko API"""
        params = {
            'ids': 'bitcoin',
            'vs_currencies': 'usd,eur,gbp,jpy,cad,aud',
            'include_market_cap': 'true',
            'include_24hr_vol': 'true',
            'include_24hr_change': 'true',
            'include_last_updated_at': 'true'
        }

        response = self.session.get(
            self.COINGECKO_SIMPLE,
            params=params,
            timeout=self.REQUEST_TIMEOUT
        )
        response.raise_for_status()

        data = response.json()['bitcoin']

        # Flatten the response
        return {
            'usd': data['usd'],
            'usd_24h_change': data['usd_24h_change'],
            'usd_market_cap': data['usd_market_cap'],
            'usd_24h_vol': data['usd_24h_vol'],
            'eur': data['eur'],
            'eur_24h_change': data['eur_24h_change'],
            'gbp': data['gbp'],
            'gbp_24h_change': data['gbp_24h_change'],
            'jpy': data['jpy'],
            'jpy_24h_change': data['jpy_24h_change'],
            'cad': data['cad'],
            'cad_24h_change': data['cad_24h_change'],
            'aud': data['aud'],
            'aud_24h_change': data['aud_24h_change'],
            'circulating_supply': data.get('circulating_supply', 0)
        }

    def _fetch_kraken_price(self) -> Dict:
        """Fallback: Fetch from Kraken API"""
        response = self.session.get(
            self.KRAKEN_TICKER,
            params={'pair': 'XBTUSDC'},  # Bitcoin to USD Coin
            timeout=self.REQUEST_TIMEOUT
        )
        response.raise_for_status()

        data = response.json()['result']['XXBTZUSD']

        return {
            'usd': float(data['c'][0]),  # Last price
            'usd_24h_change': float(data['p'][1]) * 100,  # % change
        }

    def get_price_history(self, days: int = 7, vs_currency: str = 'usd') -> List[Dict]:
        """
        Get historical prices for sparkline (daily data)

        Args:
            days: Number of days of history (7, 30, or higher)
            vs_currency: Currency code (usd, eur, gbp, etc)

        Returns:
            [
                {'date': 1234567890, 'price': 45000.50},
                {'date': 1234654290, 'price': 45100.00},
                ...
            ]
        """
        return self._fetch_price_history(days, vs_currency)

    @PriceCache().cached(ttl=HISTORY_CACHE_TTL)
    def _fetch_price_history(self, days: int, vs_currency: str) -> List[Dict]:
        """Internal method with caching"""
        try:
            params = {
                'id': 'bitcoin',
                'vs_currency': vs_currency,
                'days': days,
                'interval': 'daily'
            }

            response = self.session.get(
                self.COINGECKO_MARKET,
                params=params,
                timeout=self.REQUEST_TIMEOUT
            )
            response.raise_for_status()

            prices = response.json()['prices']
            return [
                {'date': p[0], 'price': p[1]}
                for p in prices
            ]
        except Exception as e:
            print(f"Price history error: {e}")
            return []

    def get_market_data(self) -> Dict:
        """
        Get complete market data for display

        Returns market cap, volume, and supply information
        """
        price_data = self.current_price

        return {
            'current_price': {
                'usd': price_data.get('usd', 0),
                'eur': price_data.get('eur', 0),
                'gbp': price_data.get('gbp', 0),
                'jpy': price_data.get('jpy', 0),
            },
            'change_24h': {
                'usd': price_data.get('usd_24h_change', 0),
                'eur': price_data.get('eur_24h_change', 0),
                'gbp': price_data.get('gbp_24h_change', 0),
                'jpy': price_data.get('jpy_24h_change', 0),
            },
            'market_cap': {
                'usd': price_data.get('usd_market_cap', 0),
            },
            'volume_24h': {
                'usd': price_data.get('usd_24h_vol', 0),
            },
            'supply': {
                'circulating': price_data.get('circulating_supply', 0),
            },
            'source': price_data.get('source', 'unknown'),
            'timestamp': price_data.get('timestamp', time.time())
        }

    def format_price(self, amount: float, currency: str = 'usd') -> str:
        """Format price for display"""
        if currency.upper() == 'JPY':
            return f"¥{amount:,.0f}"
        elif currency.upper() == 'GBP':
            return f"£{amount:,.2f}"
        elif currency.upper() == 'EUR':
            return f"€{amount:,.2f}"
        elif currency.upper() == 'CAD':
            return f"C${amount:,.2f}"
        elif currency.upper() == 'AUD':
            return f"A${amount:,.2f}"
        else:  # USD
            return f"${amount:,.2f}"


# Example usage
if __name__ == "__main__":
    service = BitcoinPriceService()

    # Current price
    print("Current Price:")
    print(json.dumps(service.current_price, indent=2))

    # Market data
    print("\nMarket Data:")
    print(json.dumps(service.get_market_data(), indent=2))

    # Price history
    print("\nPrice History (7 days):")
    history = service.get_price_history(7)
    for entry in history[-3:]:  # Last 3 entries
        print(f"  {entry['date']}: ${entry['price']:,.2f}")

    # Formatted price
    print("\nFormatted Prices:")
    current = service.current_price
    print(f"  USD: {service.format_price(current['usd'], 'usd')}")
    print(f"  EUR: {service.format_price(current['eur'], 'eur')}")
    print(f"  GBP: {service.format_price(current['gbp'], 'gbp')}")
    print(f"  JPY: {service.format_price(current['jpy'], 'jpy')}")
