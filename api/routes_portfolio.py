"""
Oracle Knots - Portfolio API Routes

Bottle.py routes for portfolio tracking endpoints.

Endpoints:
- GET  /api/portfolio/snapshot      - Current portfolio value across all wallets
- GET  /api/portfolio/history       - Historical snapshots for charting
- GET  /api/portfolio/pl            - P&L vs yesterday
- GET  /api/portfolio/export/csv    - Download history as CSV
- POST /api/portfolio/snapshot/record - Manually trigger a snapshot
- GET  /api/portfolio/status        - DB stats
"""

from bottle import Bottle, request, response
from api.portfolio import SUPPORTED_CURRENCIES


def setup_portfolio_routes(app: Bottle, portfolio_manager) -> Bottle:
    """Register portfolio routes on the given Bottle app instance."""

    @app.route('/api/portfolio/snapshot', method='GET')
    def get_portfolio_snapshot():
        currency = request.query.get('currency', 'usd').lower().strip()
        if currency not in SUPPORTED_CURRENCIES:
            response.status = 400
            return {'success': False, 'error': f"Unsupported currency '{currency}'. Use one of: {', '.join(SUPPORTED_CURRENCIES)}"}
        try:
            return portfolio_manager.get_portfolio_snapshot(currency)
        except Exception as e:
            response.status = 500
            return {'success': False, 'error': str(e)}

    @app.route('/api/portfolio/history', method='GET')
    def get_portfolio_history():
        currency = request.query.get('currency', 'usd').lower().strip()
        if currency not in SUPPORTED_CURRENCIES:
            response.status = 400
            return {'success': False, 'error': f"Unsupported currency '{currency}'."}
        try:
            days = int(request.query.get('days', 30))
            days = max(1, min(days, 3650))
        except (ValueError, TypeError):
            days = 30
        try:
            return portfolio_manager.get_portfolio_history(days, currency)
        except Exception as e:
            response.status = 500
            return {'success': False, 'error': str(e)}

    @app.route('/api/portfolio/pl', method='GET')
    def get_portfolio_pl():
        currency = request.query.get('currency', 'usd').lower().strip()
        if currency not in SUPPORTED_CURRENCIES:
            response.status = 400
            return {'success': False, 'error': f"Unsupported currency '{currency}'."}
        try:
            return portfolio_manager.calculate_pl(currency)
        except Exception as e:
            response.status = 500
            return {'success': False, 'error': str(e)}

    @app.route('/api/portfolio/export/csv', method='GET')
    def export_portfolio_csv():
        try:
            days = int(request.query.get('days', 365))
            days = max(1, min(days, 3650))
        except (ValueError, TypeError):
            days = 365
        try:
            csv_data = portfolio_manager.export_csv(days)
            response.content_type = 'text/csv; charset=utf-8'
            response.headers['Content-Disposition'] = 'attachment; filename="oracle-knots-portfolio.csv"'
            return csv_data
        except Exception as e:
            response.status = 500
            return {'success': False, 'error': str(e)}

    @app.route('/api/portfolio/snapshot/record', method='POST')
    def record_portfolio_snapshot():
        from datetime import datetime
        try:
            inserted = portfolio_manager.record_daily_snapshot()
            return {
                'success': True,
                'recorded': inserted,
                'date': datetime.now().strftime('%Y-%m-%d'),
                'message': 'Snapshot recorded.' if inserted else 'Snapshot for today already exists.',
            }
        except Exception as e:
            response.status = 500
            return {'success': False, 'error': str(e)}

    @app.route('/api/portfolio/status', method='GET')
    def get_portfolio_status():
        try:
            return portfolio_manager.get_stats()
        except Exception as e:
            response.status = 500
            return {'success': False, 'error': str(e)}

    return app
