from flask import Blueprint, request, jsonify
import logging
from models import ChannelConfig, db
from utils import (
    setup_channel_configuration,
    validate_channel_permissions,
    revalidate_channel,
    get_channel_permission_status
)
from services import ChannelValidatorService, PermissionCheckerService

logger = logging.getLogger(__name__)
channels_bp = Blueprint('channels', __name__, url_prefix='/api/channels')

# Rate limiting would be implemented here in production
# For now, we'll add basic request validation

def get_bot_credentials(account_id):
    """
    Get bot credentials for an account
    In production, this would call the Auth Service
    For now, we'll use dummy data or environment variables
    """
    # TODO: Implement actual auth service integration
    # This is a placeholder - in production, call auth service
    return {
        'bot_token': 'dummy_token',  # Would be fetched from auth service
        'bot_id': 123456789  # Would be fetched from auth service
    }

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

