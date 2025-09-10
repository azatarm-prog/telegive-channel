from flask import Blueprint, jsonify
import requests
from config.settings import Config
from models import db

health_bp = Blueprint('health', __name__)

@health_bp.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint
    Returns service status and dependency checks
    """
    try:
        # Check database connection
        db_status = "connected"
        try:
            # Test database connection with a simple query
            result = db.session.execute(db.text('SELECT 1')).fetchone()
            if result is None:
                db_status = "disconnected"
        except Exception as e:
            db_status = "disconnected"
        
        # Check Telegram API accessibility
        telegram_status = "accessible"
        try:
            response = requests.get(f"{Config.TELEGRAM_API_BASE}/bot123:test/getMe", timeout=5)
            # We expect this to fail with 401 (unauthorized), but that means API is accessible
            if response.status_code in [401, 404]:
                telegram_status = "accessible"
            else:
                telegram_status = "unknown"
        except Exception:
            telegram_status = "inaccessible"
        
        # Determine overall status
        overall_status = "healthy"
        if db_status != "connected":
            overall_status = "unhealthy"
        elif telegram_status == "inaccessible":
            overall_status = "degraded"
        
        return jsonify({
            "status": overall_status,
            "service": Config.SERVICE_NAME,
            "version": "1.0.0",
            "database": db_status,
            "telegram_api": telegram_status
        }), 200 if overall_status == "healthy" else 503
    
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "service": Config.SERVICE_NAME,
            "version": "1.0.0",
            "error": str(e)
        }), 503

