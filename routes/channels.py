from flask import Blueprint, request, jsonify
import logging
from datetime import datetime
from models import ChannelConfig, db
from utils import (
    setup_channel_configuration,
    validate_channel_permissions,
    revalidate_channel,
    get_channel_permission_status
)
from utils.account_lookup import get_bot_credentials_from_db, validate_account_exists
from services import ChannelValidatorService, PermissionCheckerService

logger = logging.getLogger(__name__)
channels_bp = Blueprint('channels', __name__, url_prefix='/api/channels')

# Rate limiting would be implemented here in production
# For now, we'll add basic request validation

def get_bot_credentials(account_id):
    """
    Get bot credentials for an account from the Auth Service
    
    Args:
        account_id: Account ID to get credentials for
        
    Returns:
        dict: Bot credentials with bot_token and bot_id
        
    Raises:
        Exception: If auth service is unavailable or account not found
    """
    import requests
    import os
    
    auth_service_url = os.getenv('TELEGIVE_AUTH_URL', 'https://web-production-ddd7e.up.railway.app')
    
    try:
        # First, get account information to verify account exists and get bot_id
        account_response = requests.get(
            f"{auth_service_url}/api/auth/account/{account_id}",
            timeout=10
        )
        
        if account_response.status_code == 404:
            raise Exception(f"Account {account_id} not found in auth service")
        elif account_response.status_code != 200:
            raise Exception(f"Auth service error: {account_response.status_code}")
            
        account_data = account_response.json()
        
        if not account_data.get('success'):
            raise Exception(f"Auth service error: {account_data.get('error', 'Unknown error')}")
            
        account_info = account_data['account']
        bot_id = account_info['bot_id']
        
        # Get the decrypted bot token
        token_response = requests.get(
            f"{auth_service_url}/api/auth/decrypt-token/{account_id}",
            timeout=10
        )
        
        if token_response.status_code == 404:
            raise Exception(f"Bot token not found for account {account_id}")
        elif token_response.status_code != 200:
            raise Exception(f"Token decryption error: {token_response.status_code}")
            
        token_data = token_response.json()
        
        if not token_data.get('success'):
            raise Exception(f"Token decryption error: {token_data.get('error', 'Unknown error')}")
            
        bot_token = token_data['bot_token']
        
        logger.info(f"Successfully retrieved bot credentials for account {account_id}")
        
        return {
            'bot_token': bot_token,
            'bot_id': bot_id,
            'account_info': account_info  # Include additional account info
        }
        
    except requests.exceptions.Timeout:
        logger.error(f"Timeout connecting to auth service for account {account_id}")
        raise Exception("Auth service timeout")
    except requests.exceptions.ConnectionError:
        logger.error(f"Connection error to auth service for account {account_id}")
        raise Exception("Auth service unavailable")
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error to auth service for account {account_id}: {str(e)}")
        raise Exception(f"Auth service error: {str(e)}")
    except Exception as e:
        logger.error(f"Error getting bot credentials for account {account_id}: {str(e)}")
        raise

@channels_bp.route('/setup', methods=['POST'])
def setup_channel():
    """
    Setup and validate channel configuration
    POST /api/channels/setup
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No JSON data provided'
            }), 400
        
        account_id = data.get('account_id')
        channel_username = data.get('channel_username')
        
        if not account_id:
            return jsonify({
                'success': False,
                'error': 'account_id is required'
            }), 400
        
        if not channel_username:
            return jsonify({
                'success': False,
                'error': 'channel_username is required'
            }), 400
        
        # Get bot credentials (would call auth service in production)
        credentials = get_bot_credentials(account_id)
        bot_token = credentials['bot_token']
        bot_id = credentials['bot_id']
        
        # Setup channel configuration
        result = setup_channel_configuration(
            account_id=account_id,
            channel_username=channel_username,
            bot_token=bot_token,
            bot_id=bot_id
        )
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    
    except Exception as e:
        logger.error(f"Error in setup_channel: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Internal server error: {str(e)}'
        }), 500

@channels_bp.route('/validate/<int:account_id>', methods=['GET'])
def validate_channel(account_id):
    """
    Validate existing channel configuration
    GET /api/channels/validate/{account_id}
    """
    try:
        # Get channel configuration
        channel_config = ChannelConfig.query.filter_by(account_id=account_id).first()
        
        if not channel_config:
            return jsonify({
                'valid': False,
                'error': 'No channel configuration found for account'
            }), 404
        
        # Get bot credentials
        credentials = get_bot_credentials(account_id)
        bot_token = credentials['bot_token']
        bot_id = credentials['bot_id']
        
        # Validate permissions
        validation_result = validate_channel_permissions(channel_config, bot_token, bot_id)
        
        response_data = {
            'valid': validation_result['valid'],
            'channel_info': {
                'id': channel_config.channel_id,
                'username': channel_config.channel_username,
                'title': channel_config.channel_title
            },
            'last_validated': channel_config.last_validation_at.isoformat() if channel_config.last_validation_at else None
        }
        
        if not validation_result['valid']:
            response_data['error'] = validation_result.get('error')
        
        if validation_result.get('permissions_changed'):
            response_data['permissions_changed'] = True
            response_data['current_permissions'] = validation_result.get('current_permissions')
        
        return jsonify(response_data), 200
    
    except Exception as e:
        logger.error(f"Error in validate_channel: {str(e)}")
        return jsonify({
            'valid': False,
            'error': f'Validation error: {str(e)}'
        }), 500

@channels_bp.route('/permissions/<int:account_id>', methods=['GET'])
def get_channel_permissions(account_id):
    """
    Get bot permissions in channel
    GET /api/channels/permissions/{account_id}
    """
    try:
        # Get channel configuration
        channel_config = ChannelConfig.query.filter_by(account_id=account_id).first()
        
        if not channel_config:
            return jsonify({
                'success': False,
                'error': 'No channel configuration found for account'
            }), 404
        
        permissions = channel_config.get_permissions_dict()
        
        return jsonify({
            'success': True,
            'permissions': permissions,
            'channel_info': {
                'id': channel_config.channel_id,
                'title': channel_config.channel_title
            }
        }), 200
    
    except Exception as e:
        logger.error(f"Error in get_channel_permissions: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Error retrieving permissions: {str(e)}'
        }), 500

@channels_bp.route('/update-permissions', methods=['PUT'])
def update_permissions():
    """
    Update permission status after validation
    PUT /api/channels/update-permissions
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No JSON data provided'
            }), 400
        
        account_id = data.get('account_id')
        permissions = data.get('permissions')
        validation_error = data.get('validation_error')
        
        if not account_id:
            return jsonify({
                'success': False,
                'error': 'account_id is required'
            }), 400
        
        if not permissions:
            return jsonify({
                'success': False,
                'error': 'permissions are required'
            }), 400
        
        # Get channel configuration
        channel_config = ChannelConfig.query.filter_by(account_id=account_id).first()
        
        if not channel_config:
            return jsonify({
                'success': False,
                'error': 'No channel configuration found for account'
            }), 404
        
        # Update permissions
        channel_config.update_permissions(permissions)
        
        if validation_error:
            channel_config.validation_error = validation_error
            channel_config.is_validated = False
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'updated_permissions': channel_config.get_permissions_dict()
        }), 200
    
    except Exception as e:
        logger.error(f"Error in update_permissions: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': f'Error updating permissions: {str(e)}'
        }), 500

@channels_bp.route('/info/<int:account_id>', methods=['GET'])
def get_channel_info(account_id):
    """
    Get complete channel information
    GET /api/channels/info/{account_id}
    """
    try:
        # Get channel configuration
        channel_config = ChannelConfig.query.filter_by(account_id=account_id).first()
        
        if not channel_config:
            return jsonify({
                'success': False,
                'error': 'No channel configuration found for account'
            }), 404
        
        channel_info = {
            'id': channel_config.channel_id,
            'username': channel_config.channel_username,
            'title': channel_config.channel_title,
            'member_count': channel_config.channel_member_count,
            'type': channel_config.channel_type,
            'is_validated': channel_config.is_validated,
            'last_validation': channel_config.last_validation_at.isoformat() if channel_config.last_validation_at else None
        }
        
        return jsonify({
            'success': True,
            'channel': channel_info
        }), 200
    
    except Exception as e:
        logger.error(f"Error in get_channel_info: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Error retrieving channel info: {str(e)}'
        }), 500

@channels_bp.route('/revalidate/<int:account_id>', methods=['POST'])
def revalidate_channel_endpoint(account_id):
    """
    Force revalidation of channel
    POST /api/channels/revalidate/{account_id}
    """
    try:
        # Get channel configuration
        channel_config = ChannelConfig.query.filter_by(account_id=account_id).first()
        
        if not channel_config:
            return jsonify({
                'success': False,
                'error': 'No channel configuration found for account'
            }), 404
        
        # Get bot credentials
        credentials = get_bot_credentials(account_id)
        bot_token = credentials['bot_token']
        bot_id = credentials['bot_id']
        
        # Perform revalidation
        result = revalidate_channel(channel_config, bot_token, bot_id)
        
        if result['success']:
            validation_result = result['validation_result']
            
            response_data = {
                'success': True,
                'validation_result': {
                    'valid': validation_result['valid'],
                    'permissions_changed': validation_result.get('permissions_changed', False)
                }
            }
            
            if result.get('channel_info_updated'):
                response_data['validation_result']['new_member_count'] = channel_config.channel_member_count
            
            return jsonify(response_data), 200
        else:
            return jsonify(result), 400
    
    except Exception as e:
        logger.error(f"Error in revalidate_channel: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Revalidation error: {str(e)}'
        }), 500

# Additional utility endpoints

@channels_bp.route('/status/<int:account_id>', methods=['GET'])
def get_channel_status(account_id):
    """
    Get comprehensive channel status
    GET /api/channels/status/{account_id}
    """
    try:
        # Get channel configuration
        channel_config = ChannelConfig.query.filter_by(account_id=account_id).first()
        
        if not channel_config:
            return jsonify({
                'success': False,
                'error': 'No channel configuration found for account'
            }), 404
        
        # Get comprehensive status
        status = get_channel_permission_status(channel_config)
        
        return jsonify({
            'success': True,
            'status': status
        }), 200
    
    except Exception as e:
        logger.error(f"Error in get_channel_status: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Error retrieving channel status: {str(e)}'
        }), 500

@channels_bp.route('/list', methods=['GET'])
def list_channels():
    """
    List all channel configurations (for admin/debugging)
    GET /api/channels/list
    """
    try:
        # In production, this would require admin authentication
        channels = ChannelConfig.query.all()
        
        channel_list = []
        for channel in channels:
            channel_list.append({
                'account_id': channel.account_id,
                'channel_id': channel.channel_id,
                'channel_username': channel.channel_username,
                'channel_title': channel.channel_title,
                'is_validated': channel.is_validated,
                'last_validation': channel.last_validation_at.isoformat() if channel.last_validation_at else None
            })
        
        return jsonify({
            'success': True,
            'channels': channel_list,
            'total': len(channel_list)
        }), 200
    
    except Exception as e:
        logger.error(f"Error in list_channels: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Error listing channels: {str(e)}'
        }), 500



# Dashboard Integration Endpoints

@channels_bp.route('/accounts/<int:account_id>/channel', methods=['GET'])
def get_account_channel(account_id):
    """
    Get channel configuration for a specific account
    GET /api/channels/accounts/{account_id}/channel
    """
    try:
        # Get bot credentials for the account
        try:
            credentials = get_bot_credentials(account_id)
        except Exception as e:
            logger.error(f"Failed to get bot credentials for account {account_id}: {str(e)}")
            return jsonify({
                'success': False,
                'error': 'Account not found or invalid',
                'code': 'ACCOUNT_NOT_FOUND'
            }), 404
        
        # Get channel configuration from database
        channel_config = ChannelConfig.query.filter_by(account_id=account_id).first()
        
        if not channel_config:
            return jsonify({
                'success': False,
                'error': 'No channel configuration found',
                'code': 'CHANNEL_NOT_CONFIGURED'
            }), 404
        
        # Return channel configuration
        return jsonify({
            'success': True,
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
    
    except Exception as e:
        logger.error(f"Error in get_account_channel for account {account_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'code': 'INTERNAL_ERROR'
        }), 500

@channels_bp.route('/accounts/<int:account_id>/channel', methods=['PUT'])
def save_account_channel(account_id):
    """
    Save or update channel configuration for a specific account
    PUT /api/channels/accounts/{account_id}/channel
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No JSON data provided',
                'code': 'INVALID_REQUEST'
            }), 400
        
        # Get bot credentials for the account
        try:
            credentials = get_bot_credentials(account_id)
        except Exception as e:
            logger.error(f"Failed to get bot credentials for account {account_id}: {str(e)}")
            return jsonify({
                'success': False,
                'error': 'Account not found or invalid',
                'code': 'ACCOUNT_NOT_FOUND'
            }), 404
        
        # Validate required fields
        channel_username = data.get('channel_username')
        channel_title = data.get('channel_title')
        
        if not channel_username:
            return jsonify({
                'success': False,
                'error': 'Channel username is required',
                'code': 'MISSING_CHANNEL_USERNAME'
            }), 400
        
        # Validate channel username format
        if not channel_username.startswith('@'):
            channel_username = '@' + channel_username
        
        # Check if channel configuration already exists
        channel_config = ChannelConfig.query.filter_by(account_id=account_id).first()
        
        if channel_config:
            # Update existing configuration
            channel_config.channel_username = channel_username
            channel_config.channel_title = channel_title or channel_config.channel_title
            channel_config.is_validated = data.get('is_verified', False)
            channel_config.updated_at = datetime.utcnow()
        else:
            # Create new configuration
            channel_config = ChannelConfig(
                account_id=account_id,
                channel_username=channel_username,
                channel_title=channel_title or 'Unknown Channel',
                is_validated=data.get('is_verified', False),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.session.add(channel_config)
        
        # Save to database
        db.session.commit()
        
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
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error in save_account_channel for account {account_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'code': 'INTERNAL_ERROR'
        }), 500

@channels_bp.route('/accounts/<int:account_id>/channel', methods=['DELETE'])
def delete_account_channel(account_id):
    """
    Delete channel configuration for a specific account
    DELETE /api/channels/accounts/{account_id}/channel
    """
    try:
        # Get bot credentials for the account
        try:
            credentials = get_bot_credentials(account_id)
        except Exception as e:
            logger.error(f"Failed to get bot credentials for account {account_id}: {str(e)}")
            return jsonify({
                'success': False,
                'error': 'Account not found or invalid',
                'code': 'ACCOUNT_NOT_FOUND'
            }), 404
        
        # Find channel configuration
        channel_config = ChannelConfig.query.filter_by(account_id=account_id).first()
        
        if not channel_config:
            return jsonify({
                'success': False,
                'error': 'No channel configuration found to delete',
                'code': 'CHANNEL_NOT_CONFIGURED'
            }), 404
        
        # Delete the configuration
        db.session.delete(channel_config)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Channel configuration deleted successfully'
        }), 200
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error in delete_account_channel for account {account_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'code': 'INTERNAL_ERROR'
        }), 500

@channels_bp.route('/verify', methods=['POST'])
def verify_channel():
    """
    Verify that the bot has admin rights in the specified channel
    POST /api/channels/verify
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No JSON data provided',
                'code': 'INVALID_REQUEST'
            }), 400
        
        channel_username = data.get('channel_username')
        account_id = data.get('account_id')
        
        if not channel_username:
            return jsonify({
                'success': False,
                'error': 'Channel username is required',
                'code': 'MISSING_CHANNEL_USERNAME'
            }), 400
        
        if not account_id:
            return jsonify({
                'success': False,
                'error': 'Account ID is required',
                'code': 'MISSING_ACCOUNT_ID'
            }), 400
        
        # Ensure channel username starts with @
        if not channel_username.startswith('@'):
            channel_username = '@' + channel_username
        
        # Get bot credentials for the account
        try:
            credentials = get_bot_credentials(account_id)
            bot_token = credentials['bot_token']
            bot_id = credentials['bot_id']
        except Exception as e:
            logger.error(f"Failed to get bot credentials for account {account_id}: {str(e)}")
            return jsonify({
                'success': False,
                'error': 'Account not found or invalid bot credentials',
                'code': 'ACCOUNT_NOT_FOUND'
            }), 404
        
        # Verify channel with Telegram API
        import requests
        
        # Get chat information
        try:
            chat_response = requests.get(
                f'https://api.telegram.org/bot{bot_token}/getChat',
                params={'chat_id': channel_username},
                timeout=10
            )
            chat_data = chat_response.json()
            
            if not chat_data.get('ok'):
                return jsonify({
                    'success': False,
                    'channel_exists': False,
                    'error': 'Channel not found or is private',
                    'code': 'CHANNEL_NOT_FOUND'
                }), 400
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error calling Telegram API for chat info: {str(e)}")
            return jsonify({
                'success': False,
                'error': 'Failed to verify channel with Telegram',
                'code': 'TELEGRAM_API_ERROR'
            }), 500
        
        # Get bot member information
        try:
            member_response = requests.get(
                f'https://api.telegram.org/bot{bot_token}/getChatMember',
                params={
                    'chat_id': channel_username,
                    'user_id': bot_id
                },
                timeout=10
            )
            member_data = member_response.json()
            
            if not member_data.get('ok'):
                return jsonify({
                    'success': False,
                    'channel_exists': True,
                    'bot_is_admin': False,
                    'error': 'Bot is not a member of this channel',
                    'code': 'BOT_NOT_MEMBER'
                }), 400
            
            member_info = member_data['result']
            is_admin = member_info['status'] in ['administrator', 'creator']
            
            if not is_admin:
                return jsonify({
                    'success': False,
                    'channel_exists': True,
                    'bot_is_admin': False,
                    'error': 'Bot is not an administrator in this channel',
                    'code': 'BOT_NOT_ADMIN'
                }), 400
            
            # Check specific permissions
            can_post = member_info.get('can_post_messages', False)
            can_edit = member_info.get('can_edit_messages', False)
            
            if not can_post or not can_edit:
                return jsonify({
                    'success': False,
                    'channel_exists': True,
                    'bot_is_admin': True,
                    'bot_can_post_messages': can_post,
                    'bot_can_edit_messages': can_edit,
                    'error': 'Bot lacks required permissions (post_messages, edit_messages)',
                    'code': 'INSUFFICIENT_PERMISSIONS'
                }), 400
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error calling Telegram API for member info: {str(e)}")
            return jsonify({
                'success': False,
                'error': 'Failed to verify bot permissions with Telegram',
                'code': 'TELEGRAM_API_ERROR'
            }), 500
        
        # All checks passed - return success
        chat_info = chat_data['result']
        
        return jsonify({
            'success': True,
            'channel_exists': True,
            'bot_is_admin': True,
            'bot_can_post_messages': True,
            'bot_can_edit_messages': True,
            'channel_title': chat_info.get('title', 'Unknown Channel'),
            'channel_id': chat_info.get('id'),
            'member_count': chat_info.get('members_count', 0),
            'channel_type': chat_info.get('type', 'channel'),
            'verified_at': datetime.utcnow().isoformat() + 'Z'
        }), 200
    
    except Exception as e:
        logger.error(f"Error in verify_channel: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'code': 'INTERNAL_ERROR'
        }), 500

