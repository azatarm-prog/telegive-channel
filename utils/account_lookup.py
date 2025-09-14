"""
Account lookup utilities - Updated to use Auth Service API
"""
import logging
from utils.auth_service_client import auth_client

logger = logging.getLogger(__name__)

def get_account_by_bot_id(bot_id):
    """
    Get account information using Auth Service API
    
    Args:
        bot_id (int): The Telegram bot ID (e.g., 262662172)
        
    Returns:
        dict: Account information or None if not found
    """
    logger.info(f"🔍 Looking up account for bot_id: {bot_id} via Auth Service")
    return auth_client.get_account_by_bot_id(bot_id)

def get_bot_credentials_from_db(bot_id):
    """
    Get bot credentials using Auth Service API
    
    Args:
        bot_id (int): The Telegram bot ID
        
    Returns:
        dict: Bot credentials including bot_token
        
    Raises:
        Exception: If account not found or credentials unavailable
    """
    logger.info(f"🔑 Getting bot credentials for bot_id: {bot_id} via Auth Service")
    
    credentials = auth_client.get_bot_credentials(bot_id)
    
    if not credentials:
        raise Exception(f"No bot credentials found for bot_id {bot_id}")
    
    return credentials

def validate_account_exists(bot_id):
    """
    Validate that an account exists for the given bot_id
    
    Args:
        bot_id (int): The Telegram bot ID
        
    Returns:
        bool: True if account exists and is active
    """
    logger.info(f"✅ Validating account exists for bot_id: {bot_id} via Auth Service")
    return auth_client.validate_account_exists(bot_id)

def get_account_database_id(bot_id):
    """
    Get the database primary key ID for a bot_id
    
    Args:
        bot_id (int): The Telegram bot ID
        
    Returns:
        int: Database primary key ID or None if not found
    """
    account = get_account_by_bot_id(bot_id)
    return account.get('id') if account else None

