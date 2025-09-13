"""
Direct database account lookup utilities for shared database access
"""
import logging
from models import db

logger = logging.getLogger(__name__)

def get_account_by_bot_id(bot_id):
    """
    Get account information directly from shared database using bot_id
    
    Args:
        bot_id (int): The Telegram bot ID (e.g., 262662172)
        
    Returns:
        dict: Account information or None if not found
    """
    try:
        # Query the accounts table using bot_id instead of id
        result = db.session.execute(
            db.text("SELECT * FROM accounts WHERE bot_id = :bot_id AND is_active = true"),
            {"bot_id": bot_id}
        )
        
        row = result.fetchone()
        if row:
            # Convert row to dictionary
            account = dict(row._mapping)
            logger.info(f"Found account for bot_id {bot_id}: database id = {account.get('id')}")
            return account
        else:
            logger.warning(f"No active account found for bot_id {bot_id}")
            return None
            
    except Exception as e:
        logger.error(f"Database error looking up bot_id {bot_id}: {str(e)}")
        return None

def get_bot_credentials_from_db(bot_id):
    """
    Get bot credentials directly from shared database
    
    Args:
        bot_id (int): The Telegram bot ID
        
    Returns:
        dict: Bot credentials with bot_token and bot_id
        
    Raises:
        Exception: If account not found or database error
    """
    try:
        account = get_account_by_bot_id(bot_id)
        
        if not account:
            raise Exception(f"Account with bot_id {bot_id} not found in database")
        
        # Extract bot credentials from account record
        bot_token = account.get('bot_token') or account.get('encrypted_token')
        
        if not bot_token:
            raise Exception(f"No bot token found for bot_id {bot_id}")
        
        return {
            'bot_token': bot_token,
            'bot_id': bot_id,
            'account_id': account.get('id'),  # Database primary key
            'bot_username': account.get('bot_username'),
            'bot_name': account.get('bot_name') or account.get('name')
        }
        
    except Exception as e:
        logger.error(f"Error getting bot credentials for bot_id {bot_id}: {str(e)}")
        raise

def validate_account_exists(bot_id):
    """
    Validate that an account exists for the given bot_id
    
    Args:
        bot_id (int): The Telegram bot ID
        
    Returns:
        bool: True if account exists and is active
    """
    try:
        account = get_account_by_bot_id(bot_id)
        return account is not None
    except Exception as e:
        logger.error(f"Error validating account existence for bot_id {bot_id}: {str(e)}")
        return False

def get_account_database_id(bot_id):
    """
    Get the database primary key ID for a bot_id
    
    Args:
        bot_id (int): The Telegram bot ID
        
    Returns:
        int: Database primary key ID or None if not found
    """
    try:
        account = get_account_by_bot_id(bot_id)
        return account.get('id') if account else None
    except Exception as e:
        logger.error(f"Error getting database ID for bot_id {bot_id}: {str(e)}")
        return None

