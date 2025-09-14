import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Database
    DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://user:password@localhost:5432/telegive')
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Security
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # Service Configuration
    SERVICE_NAME = os.getenv('SERVICE_NAME', 'channel-service')
    SERVICE_PORT = int(os.getenv('SERVICE_PORT', 8002))
    
    # External APIs
    TELEGRAM_API_BASE = os.getenv('TELEGRAM_API_BASE', 'https://api.telegram.org')
    
    # Other Services
    TELEGIVE_AUTH_URL = os.getenv('TELEGIVE_AUTH_URL', 'http://localhost:8001')
    TELEGIVE_GIVEAWAY_URL = os.getenv('TELEGIVE_GIVEAWAY_URL', 'http://localhost:8003')
    
    # Validation Settings
    VALIDATION_TIMEOUT = int(os.getenv('VALIDATION_TIMEOUT', 10))
    PERIODIC_VALIDATION_INTERVAL = int(os.getenv('PERIODIC_VALIDATION_INTERVAL', 3600))
    
    # Required permissions for bot in channels (based on actual Telegram API fields)
    REQUIRED_PERMISSIONS = [
        'can_post_messages',
        'can_edit_messages'
        # Removed 'can_send_media_messages' - not a separate field in Telegram API
        # Media sending is included in can_post_messages for administrators
    ]

class DevelopmentConfig(Config):
    DEBUG = True
    TESTING = False

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.getenv('TEST_DATABASE_URL', 'postgresql://test:test@localhost/test_telegive')

class ProductionConfig(Config):
    DEBUG = False
    TESTING = False

config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

