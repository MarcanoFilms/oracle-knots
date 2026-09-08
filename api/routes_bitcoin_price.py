"""
Oracle Knots - Bitcoin Price API Routes

Bottle.py routes for Bitcoin price and market data endpoints.

Endpoints:
- GET /api/bitcoin/price - Current price and market data
- GET /api/bitcoin/history - Historical price data (for charts)
- GET /api/bitcoin/market - Complete market information
"""

from bottle import Bottle, request, response, JSONPlugin
import json
from api.bitcoin_price import BitcoinPriceService


def setup_price_routes(app: Bottle):
    """
    Register Bitcoin price routes with Bottle app

    Args:
        app: Bottle application instance
    """
    price_service = BitcoinPriceService()

    # ============================================================
    # GET /api/bitcoin/price
    # ============================================================
    @app.route('/api/bitcoin/price', method='GET')
    def get_bitcoin_price():
        """
        Get current Bitcoin price in multiple currencies

        Query Parameters:
            currency: Optional, specific currency (default: all)
            format: Optional, 'formatted' for display format

        Response:
            {
                'success': true,
                'price': {
                    'usd': 45000.50,
                    'eur': 42000.00,
                    'gbp': 35000.00,
                    'jpy': 5000000.00,
                    'cad': 60000.00,
                    'aud': 70000.00,
                    'usd_24h_change': 2.5,
                    'eur_24h_change': 2.5,
                    ...
                },
                'market_cap': {
                    'usd': 900000000000
                },
                'volume_24h': {
                    'usd': 25000000000
                },
                'supply': {
                    'circulating': 21000000
                },
                'source': 'coingecko',
                'updated_at': 1234567890
            }
        """
        try:
            currency = request.query.get('currency', '').lower()
            format_mode = request.query.get('format', '')

            price_data = price_service.current_price

            if 'error' in price_data:
                return {
                    'success': False,
                    'error': price_data['error'],
                    'timestamp': price_data['timestamp']
                }

            # Build response
            result = {
                'success': True,
                'price': {},
                'market_cap': {},
                'volume_24h': {},
                'supply': {},
                'source': price_data.get('source', 'unknown'),
                'updated_at': price_data.get('timestamp', 0)
            }

            # Add requested currencies
            currencies_requested = ['usd', 'eur', 'gbp', 'jpy', 'cad', 'aud']

            for curr in currencies_requested:
                if currency and curr != currency:
                    continue

                price_key = curr
                change_key = f'{curr}_24h_change'

                if price_key in price_data:
                    if format_mode == 'formatted':
                        result['price'][curr] = price_service.format_price(
                            price_data[price_key],
                            curr
                        )
                    else:
                        result['price'][curr] = price_data[price_key]

                if change_key in price_data:
                    result['price'][change_key] = price_data[change_key]

            # Add market data
            result['market_cap']['usd'] = price_data.get('usd_market_cap', 0)
            result['volume_24h']['usd'] = price_data.get('usd_24h_vol', 0)
            result['supply']['circulating'] = price_data.get('circulating_supply', 0)

            response.content_type = 'application/json'
            return result

        except Exception as e:
            response.status = 500
            return {
                'success': False,
                'error': str(e),
                'timestamp': 0
            }

    # ============================================================
    # GET /api/bitcoin/history
    # ============================================================
    @app.route('/api/bitcoin/history', method='GET')
    def get_bitcoin_history():
        """
        Get historical Bitcoin price data for charts

        Query Parameters:
            days: Number of days (default: 7, max: 365)
            currency: Currency code (default: usd)

        Response:
            {
                'success': true,
                'data': [
                    {'date': 1234567890000, 'price': 45000.50},
                    {'date': 1234654290000, 'price': 45100.00},
                    ...
                ],
                'currency': 'usd',
                'min_price': 44500.00,
                'max_price': 46000.00,
                'avg_price': 45250.00
            }
        """
        try:
            days = int(request.query.get('days', 7))
            currency = request.query.get('currency', 'usd').lower()

            # Validate days
            days = max(1, min(365, days))

            # Get history
            history = price_service.get_price_history(days, currency)

            if not history:
                return {
                    'success': False,
                    'error': 'Unable to fetch price history',
                    'data': []
                }

            # Calculate statistics
            prices = [h['price'] for h in history]
            min_price = min(prices)
            max_price = max(prices)
            avg_price = sum(prices) / len(prices)

            response.content_type = 'application/json'
            return {
                'success': True,
                'data': history,
                'currency': currency,
                'days': days,
                'min_price': min_price,
                'max_price': max_price,
                'avg_price': avg_price,
                'change': {
                    'percent': ((prices[-1] - prices[0]) / prices[0]) * 100,
                    'absolute': prices[-1] - prices[0]
                }
            }

        except ValueError:
            response.status = 400
            return {
                'success': False,
                'error': 'Invalid days parameter'
            }
        except Exception as e:
            response.status = 500
            return {
                'success': False,
                'error': str(e)
            }

    # ============================================================
    # GET /api/bitcoin/market
    # ============================================================
    @app.route('/api/bitcoin/market', method='GET')
    def get_bitcoin_market():
        """
        Get complete Bitcoin market data

        Response:
            {
                'success': true,
                'current_price': {...},
                'change_24h': {...},
                'market_cap': {...},
                'volume_24h': {...},
                'supply': {...},
                'source': 'coingecko',
                'timestamp': 1234567890
            }
        """
        try:
            market_data = price_service.get_market_data()

            if 'error' in market_data:
                return {
                    'success': False,
                    'error': market_data['error']
                }

            response.content_type = 'application/json'
            return {
                'success': True,
                **market_data
            }

        except Exception as e:
            response.status = 500
            return {
                'success': False,
                'error': str(e)
            }

    # ============================================================
    # GET /api/bitcoin/status
    # ============================================================
    @app.route('/api/bitcoin/status', method='GET')
    def get_bitcoin_status():
        """
        Get Bitcoin price service status

        Response:
            {
                'success': true,
                'service': 'bitcoin_price',
                'status': 'operational',
                'source': 'coingecko',
                'response_time_ms': 125,
                'last_update': 1234567890
            }
        """
        try:
            import time
            start = time.time()

            # Test price fetch
            price_data = price_service.current_price
            elapsed = (time.time() - start) * 1000

            status = 'operational' if 'error' not in price_data else 'degraded'

            response.content_type = 'application/json'
            return {
                'success': True,
                'service': 'bitcoin_price',
                'status': status,
                'source': price_data.get('source', 'unknown'),
                'response_time_ms': elapsed,
                'last_update': price_data.get('timestamp', 0),
                'currencies': ['usd', 'eur', 'gbp', 'jpy', 'cad', 'aud']
            }

        except Exception as e:
            response.status = 500
            return {
                'success': False,
                'service': 'bitcoin_price',
                'status': 'error',
                'error': str(e)
            }

    return app


# Example: Register routes with app
# In your main gui.py:
# from api.routes_bitcoin_price import setup_price_routes
# app = Bottle()
# setup_price_routes(app)
