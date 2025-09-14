import os
import logging
from flask import Flask, request, make_response
from flask_cors import CORS
from config.settings import config
from models import db
from routes import health_bp, channels_bp, accounts_bp, monitoring_bp
from tasks import initialize_periodic_validation, start_periodic_validation

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_app(config_name=None):
    """
    Create and configure the Flask application
    
    Args:
        config_name: Configuration name to use (development, testing, production)
    
    Returns:
        Flask application instance
    """
    app = Flask(__name__)
    
    # Load configuration
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')
    
    app.config.from_object(config.get(config_name, config['default']))
    
    # Initialize extensions
    db.init_app(app)
    
    # Enable CORS for dashboard integration
    CORS(app, 
         origins=[
             'https://telegive-dashboard-production.up.railway.app',
             'http://localhost:5173',  # For development
             'http://localhost:3000',  # Alternative dev port
             'https://telegive-dashboard-*.up.railway.app'  # For staging environments
         ],
         methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
         allow_headers=['Content-Type', 'Authorization', 'Accept', 'X-Requested-With'],
         supports_credentials=True,
         max_age=86400)
    
    # Register blueprints
    app.register_blueprint(health_bp)
    app.register_blueprint(channels_bp)
    app.register_blueprint(accounts_bp)
    app.register_blueprint(monitoring_bp)
    
    # Add explicit OPTIONS handler for CORS preflight requests
    @app.before_request
    def handle_preflight():
        if request.method == "OPTIONS":
            response = make_response()
            response.headers.add("Access-Control-Allow-Origin", request.headers.get('Origin', '*'))
            response.headers.add('Access-Control-Allow-Headers', "Content-Type,Authorization,Accept,X-Requested-With")
            response.headers.add('Access-Control-Allow-Methods', "GET,POST,PUT,DELETE,OPTIONS")
            response.headers.add('Access-Control-Allow-Credentials', 'true')
            response.headers.add('Access-Control-Max-Age', '86400')
            return response
    
    # Create database tables
    with app.app_context():
        try:
            db.create_all()
            logger.info("Database tables created successfully")
            
            # Database migration no longer needed - using Auth Service API
            logger.info("Using Auth Service API - no database migration required")
            
        except Exception as e:
            logger.error(f"Error creating database tables: {str(e)}")
    
    # Initialize periodic validation
    def get_bot_credentials(bot_id):
        """
        Get bot credentials for an account using direct database access
        
        Args:
            bot_id: Bot ID (e.g., 262662172) - this is the Telegram bot ID
            
        Returns:
            dict: Bot credentials with bot_token and bot_id
        """
        from utils.account_lookup import get_bot_credentials_from_db
        try:
            # Use direct database lookup instead of Auth Service API
            logger.info(f"Getting bot credentials for bot_id {bot_id}")
            return get_bot_credentials_from_db(bot_id)
        except Exception as e:
            logger.error(f"Error getting bot credentials for bot_id {bot_id}: {str(e)}")
            # Fallback to environment variables for development
            return {
                'bot_token': os.getenv('TELEGRAM_BOT_TOKEN', 'dummy_token'),
                'bot_id': int(os.getenv('TELEGRAM_BOT_ID', bot_id))
            }
    
    # Initialize and start periodic validation
    try:
        initialize_periodic_validation(get_bot_credentials)
        start_periodic_validation()
        logger.info("Periodic validation initialized and started")
    except Exception as e:
        logger.error(f"Error initializing periodic validation: {str(e)}")
    
    # Add error handlers
    @app.errorhandler(404)
    def not_found(error):
        return {
            'success': False,
            'error': 'Endpoint not found',
            'error_code': 'NOT_FOUND'
        }, 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return {
            'success': False,
            'error': 'Internal server error',
            'error_code': 'INTERNAL_ERROR'
        }, 500
    
    @app.errorhandler(400)
    def bad_request(error):
        return {
            'success': False,
            'error': 'Bad request',
            'error_code': 'BAD_REQUEST'
        }, 400
    
    # Add a root endpoint
    @app.route('/')
    def root():
        return {
            'service': app.config['SERVICE_NAME'],
            'version': '1.1.0',  # Updated version after bot_token fix
            'status': 'running',
            'endpoints': {
                'health': '/health',
                'channels': '/api/channels/*'
            }
        }
    
    # Add shutdown handler
    @app.teardown_appcontext
    def shutdown_session(exception=None):
        db.session.remove()
    
    logger.info(f"Flask application created with config: {config_name}")
    return app

# Create the application instance
app = create_app()

if __name__ == '__main__':
    # Get configuration from environment
    port = int(os.getenv('PORT', app.config['SERVICE_PORT']))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    logger.info(f"Starting Channel Management Service on port {port}")
    
    # Run the application
    app.run(
        host='0.0.0.0',  # Listen on all interfaces for deployment
        port=port,
        debug=debug,
        threaded=True
    )

