from flask import Blueprint, request, jsonify
import logging
import requests
from datetime import datetime
from models import ChannelConfig, db

logger = logging.getLogger(__name__)
accounts_bp = Blueprint('accounts', __name__, url_prefix='/api/accounts')

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

@accounts_bp.route('/<int:account_id>/channel', methods=['GET'])
def get_account_channel(account_id):
    """
    Get channel configuration for a specific account
    GET /api/accounts/{account_id}/channel
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

@accounts_bp.route('/<int:account_id>/channel', methods=['PUT'])
def save_account_channel(account_id):
    """
    Save or update channel configuration for a specific account
    PUT /api/accounts/{account_id}/channel
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

@accounts_bp.route('/<int:account_id>/channel', methods=['DELETE'])
def delete_account_channel(account_id):
    """
    Delete channel configuration for a specific account
    DELETE /api/accounts/{account_id}/channel
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

