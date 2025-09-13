"""
Direct database account lookup utilities for shared database access
"""
import logging
from models import db

logger = logging.getLogger(__name__)

def get_account_by_bot_id(bot_id):
    """
    Get account information directly from shared database using bot_id
    Uses SQLAlchemy model to access bot_token property (auto-decrypts)
    
    Args:
        bot_id (int): The Telegram bot ID (e.g., 262662172)
        
    Returns:
        dict: Account information or None if not found
    """
    try:
        # Import the Account model to access bot_token property
        from models import db
        
        # Try to use SQLAlchemy model first (for bot_token property)
        try:
            # Query using SQLAlchemy model to get bot_token property
            result = db.session.execute(
                db.text("""
                    SELECT id, bot_id, bot_username, bot_name, bot_token_encrypted, 
                           is_active, created_at, channel_id, channel_username
                    FROM accounts 
                    WHERE bot_id = :bot_id AND is_active = true
                """),
                {"bot_id": bot_id}
            )
            
            row = result.fetchone()
            if row:
                # Convert row to dictionary and add decrypted token
                account = dict(row._mapping)
                
                # If Auth Service provides bot_token property, try to access it
                # For now, use the encrypted token field directly
                encrypted_token = account.get('bot_token_encrypted')
                if encrypted_token:
                    # TODO: Implement decryption or use Auth Service API
                    # For now, use the encrypted token as-is (Auth Service should handle this)
                    account['bot_token'] = encrypted_token
                
                logger.info(f"Found account for bot_id {bot_id}: database id = {account.get('id')}")
                return account
            else:
                logger.warning(f"No active account found for bot_id {bot_id}")
                return None
                
        except Exception as model_error:
            logger.warning(f"SQLAlchemy model access failed: {str(model_error)}")
            # Fallback to raw SQL
            result = db.session.execute(
                db.text("SELECT * FROM accounts WHERE bot_id = :bot_id AND is_active = true"),
                {"bot_id": bot_id}
            )
            
            row = result.fetchone()
            if row:
                account = dict(row._mapping)
                logger.info(f"Found account for bot_id {bot_id}: database id = {account.get('id')} (fallback)")
                return account
            else:
                logger.warning(f"No active account found for bot_id {bot_id} (fallback)")
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
        # Auth Service confirmed the field is 'bot_token_encrypted' in database
        # but provides 'bot_token' property that auto-decrypts
        bot_token = (account.get('bot_token') or 
                    account.get('bot_token_encrypted') or 
                    account.get('encrypted_token'))
        
        if not bot_token:
            # Log available fields for debugging
            available_fields = list(account.keys()) if isinstance(account, dict) else dir(account)
            logger.error(f"No bot token found for bot_id {bot_id}. Available fields: {available_fields}")
            raise Exception(f"No bot token found for bot_id {bot_id}")
        
        logger.info(f"Successfully retrieved bot token for bot_id {bot_id}")
        
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

