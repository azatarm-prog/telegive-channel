from flask import Blueprint, request, jsonify
import logging
from datetime import datetime
from models import ChannelConfig, db
from utils.account_lookup import get_bot_credentials_from_db, validate_account_exists

logger = logging.getLogger(__name__)
accounts_bp = Blueprint('accounts', __name__, url_prefix='/api/accounts')

def get_bot_credentials(bot_id):
    """
    Get bot credentials for an account using direct database access
    
    Args:
        bot_id: Bot ID (e.g., 262662172) - this is the Telegram bot ID
        
    Returns:
        dict: Bot credentials with bot_token and bot_id
        
    Raises:
        Exception: If account not found or database error
    """
    try:
        # Use direct database lookup instead of Auth Service API
        # bot_id here is the Telegram bot ID (262662172)
        logger.info(f"Looking up bot credentials for bot_id {bot_id}")
        return get_bot_credentials_from_db(bot_id)
    except Exception as e:
        logger.error(f"Error getting bot credentials for bot_id {bot_id}: {str(e)}")
        raise

@accounts_bp.route('/<int:account_id>/channel', methods=['GET'])
def get_account_channel(account_id):
    """
    Get channel configuration for a specific account
    GET /api/accounts/{account_id}/channel
    
    Note: account_id is actually the bot_id (262662172)
    """
    try:
        logger.info(f"Getting channel config for bot_id {account_id}")
        
        # Validate account exists using bot_id
        if not validate_account_exists(account_id):
            logger.warning(f"Account with bot_id {account_id} not found in database")
            return jsonify({
                'success': False,
                'error': f'Account with bot_id {account_id} not found in database. Please contact support or try logging in again.',
                'code': 'ACCOUNT_NOT_FOUND',
                'details': {
                    'bot_id': account_id,
                    'suggestion': 'This usually indicates an account synchronization issue. Please try logging out and logging back in.',
                    'support_action': 'If the problem persists, contact support with this bot_id.',
                    'timestamp': datetime.utcnow().isoformat() + 'Z'
                }
            }), 404
        
        # Get channel configuration from database using bot_id as account_id
        # Note: In ChannelConfig, account_id stores the bot_id (262662172)
        channel_config = ChannelConfig.query.filter_by(account_id=account_id).first()
        
        if not channel_config:
            logger.info(f"No channel configuration found for bot_id {account_id}")
            return jsonify({
                'success': False,
                'error': 'No channel configuration found',
                'code': 'CHANNEL_NOT_CONFIGURED',
                'details': {
                    'bot_id': account_id,
                    'suggestion': 'Please configure your channel first using the channel setup process.',
                    'next_steps': 'Use the channel verification endpoint to set up your channel.',
                    'timestamp': datetime.utcnow().isoformat() + 'Z'
                }
            }), 404
        
        # Return channel configuration
        logger.info(f"Found channel configuration for bot_id {account_id}: {channel_config.channel_username}")
        return jsonify({
            'success': True,
            'channel': {
                'id': channel_config.id,
                'account_id': channel_config.account_id,  # This is the bot_id
                'channel_username': channel_config.channel_username,
                'channel_title': channel_config.channel_title,
                'channel_id': channel_config.channel_id,
                'is_verified': channel_config.is_validated,
                'verified_at': channel_config.last_validation_at.isoformat() + 'Z' if channel_config.last_validation_at else None,
                'created_at': channel_config.created_at.isoformat() + 'Z' if channel_config.created_at else None,
                'updated_at': channel_config.updated_at.isoformat() + 'Z' if channel_config.updated_at else None
            }
        }), 200
    
    except Exception as e:
        logger.error(f"Error in get_account_channel for bot_id {account_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'code': 'INTERNAL_ERROR',
            'details': {
                'bot_id': account_id,
                'error_message': str(e),
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            }
        }), 500

@accounts_bp.route('/<int:account_id>/channel', methods=['PUT'])
def save_account_channel(account_id):
    """
    Save or update channel configuration for a specific account
    PUT /api/accounts/{account_id}/channel
    
    Note: account_id is actually the bot_id (262662172)
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No JSON data provided',
                'code': 'INVALID_REQUEST'
            }), 400
        
        logger.info(f"Saving channel config for bot_id {account_id}: {data}")
        
        # Validate account exists using bot_id
        if not validate_account_exists(account_id):
            logger.warning(f"Account with bot_id {account_id} not found in database")
            return jsonify({
                'success': False,
                'error': f'Account with bot_id {account_id} not found in database',
                'code': 'ACCOUNT_NOT_FOUND'
            }), 404
        
        # Get or create channel configuration
        channel_config = ChannelConfig.query.filter_by(account_id=account_id).first()
        
        if not channel_config:
            # Create new channel configuration
            channel_config = ChannelConfig(
                account_id=account_id,  # Store bot_id as account_id
                created_at=datetime.utcnow()
            )
            db.session.add(channel_config)
            logger.info(f"Created new channel config for bot_id {account_id}")
        else:
            logger.info(f"Updating existing channel config for bot_id {account_id}")
        
        # Update channel configuration fields
        if 'channel_username' in data:
            channel_config.channel_username = data['channel_username']
        if 'channel_title' in data:
            channel_config.channel_title = data['channel_title']
        if 'channel_id' in data:
            channel_config.channel_id = data['channel_id']
        if 'is_verified' in data:
            channel_config.is_validated = data['is_verified']
        if 'channel_type' in data:
            channel_config.channel_type = data['channel_type']
        if 'channel_member_count' in data:
            channel_config.channel_member_count = data['channel_member_count']
        
        # Update permissions if provided
        if 'permissions' in data:
            permissions = data['permissions']
            channel_config.can_post_messages = permissions.get('can_post_messages', False)
            channel_config.can_edit_messages = permissions.get('can_edit_messages', False)
            channel_config.can_send_media_messages = permissions.get('can_send_media_messages', False)
            channel_config.can_delete_messages = permissions.get('can_delete_messages', False)
            channel_config.can_pin_messages = permissions.get('can_pin_messages', False)
        
        # Update timestamps
        channel_config.updated_at = datetime.utcnow()
        if data.get('is_verified'):
            channel_config.last_validation_at = datetime.utcnow()
        
        # Save to database
        try:
            db.session.commit()
            logger.info(f"Successfully saved channel config for bot_id {account_id}")
            
            return jsonify({
                'success': True,
                'message': 'Channel configuration saved successfully',
                'channel': {
                    'id': channel_config.id,
                    'account_id': channel_config.account_id,
                    'channel_username': channel_config.channel_username,
                    'channel_title': channel_config.channel_title,
                    'channel_id': channel_config.channel_id,
                    'is_verified': channel_config.is_validated,
                    'verified_at': channel_config.last_validation_at.isoformat() + 'Z' if channel_config.last_validation_at else None,
                    'created_at': channel_config.created_at.isoformat() + 'Z' if channel_config.created_at else None,
                    'updated_at': channel_config.updated_at.isoformat() + 'Z' if channel_config.updated_at else None
                }
            }), 200
            
        except Exception as db_error:
            db.session.rollback()
            logger.error(f"Database error saving channel config for bot_id {account_id}: {str(db_error)}")
            return jsonify({
                'success': False,
                'error': 'Database error while saving channel configuration',
                'code': 'DATABASE_ERROR'
            }), 500
    
    except Exception as e:
        logger.error(f"Error in save_account_channel for bot_id {account_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'code': 'INTERNAL_ERROR'
        }), 500

@accounts_bp.route('/<int:account_id>/channel', methods=['DELETE'])
def delete_account_channel(account_id):
    """
    Delete channel configuration for a specific account
    DELETE /api/accounts/{account_id}/channel
    
    Note: account_id is actually the bot_id (262662172)
    """
    try:
        logger.info(f"Deleting channel config for bot_id {account_id}")
        
        # Validate account exists using bot_id
        if not validate_account_exists(account_id):
            logger.warning(f"Account with bot_id {account_id} not found in database")
            return jsonify({
                'success': False,
                'error': f'Account with bot_id {account_id} not found in database',
                'code': 'ACCOUNT_NOT_FOUND'
            }), 404
        
        # Find channel configuration
        channel_config = ChannelConfig.query.filter_by(account_id=account_id).first()
        
        if not channel_config:
            logger.info(f"No channel configuration found to delete for bot_id {account_id}")
            return jsonify({
                'success': False,
                'error': 'No channel configuration found to delete',
                'code': 'CHANNEL_NOT_CONFIGURED'
            }), 404
        
        # Delete channel configuration
        try:
            db.session.delete(channel_config)
            db.session.commit()
            logger.info(f"Successfully deleted channel config for bot_id {account_id}")
            
            return jsonify({
                'success': True,
                'message': 'Channel configuration deleted successfully'
            }), 200
            
        except Exception as db_error:
            db.session.rollback()
            logger.error(f"Database error deleting channel config for bot_id {account_id}: {str(db_error)}")
            return jsonify({
                'success': False,
                'error': 'Database error while deleting channel configuration',
                'code': 'DATABASE_ERROR'
            }), 500
    
    except Exception as e:
        logger.error(f"Error in delete_account_channel for bot_id {account_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'code': 'INTERNAL_ERROR'
        }), 500

