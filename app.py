import os
import logging
from flask import Flask
from flask_cors import CORS
from config.settings import config
from models import db
from routes import health_bp, channels_bp
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
    
    # Enable CORS for all routes
    CORS(app, origins="*")
    
    # Register blueprints
    app.register_blueprint(health_bp)
    app.register_blueprint(channels_bp)
    
    # Create database tables
    with app.app_context():
        try:
            db.create_all()
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Error creating database tables: {str(e)}")
    
    # Initialize periodic validation
    def get_bot_credentials(account_id):
        """
        Get bot credentials for an account
        TODO: Replace with actual auth service integration
        """
        # This is a placeholder - in production, this would call the auth service
        # For now, we'll return dummy credentials or use environment variables
        return {
            'bot_token': os.getenv('TELEGRAM_BOT_TOKEN', 'dummy_token'),
            'bot_id': int(os.getenv('TELEGRAM_BOT_ID', '123456789'))
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
            'version': '1.0.0',
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

