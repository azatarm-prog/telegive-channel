"""
Service API endpoints for inter-service communication
These endpoints are used by other Telegive services (Giveaway Service, etc.)
"""

import logging
from datetime import datetime
from flask import Blueprint, request, jsonify
from models import ChannelConfig, db
from utils.service_auth import require_service_token, require_service_permission, get_requesting_service
from utils.account_lookup import get_account_by_bot_id

logger = logging.getLogger(__name__)

service_api_bp = Blueprint('service_api', __name__, url_prefix='/api/service')

@service_api_bp.route('/channel/<int:bot_id>', methods=['GET'])
@require_service_token
@require_service_permission('read_channel_config')
def get_channel_config_for_service(bot_id):
    """
    Get channel configuration for a bot (service endpoint)
    
    GET /api/service/channel/{bot_id}
    
    Headers:
        X-Service-Token: Valid service token
    
    Returns:
        Channel configuration or error if not found
    """
    try:
        service_name = get_requesting_service()
        logger.info(f"Service {service_name} requesting channel config for bot_id {bot_id}")
        
        # Get account information
        account = get_account_by_bot_id(bot_id)
        if not account:
            return jsonify({
                'success': False,
                'error': 'Account not found',
                'code': 'ACCOUNT_NOT_FOUND',
                'bot_id': bot_id
            }), 404
        
        # Get channel configuration
        channel_config = ChannelConfig.query.filter_by(account_id=bot_id).first()
        
        if not channel_config:
            return jsonify({
                'success': False,
                'error': 'Channel not configured',
                'code': 'CHANNEL_NOT_CONFIGURED',
                'bot_id': bot_id,
                'account_id': account.get('id') if account else None
            }), 404
        
        # Return channel configuration
        return jsonify({
            'success': True,
            'bot_id': bot_id,
            'account_id': account.get('id') if account else None,
            'channel': {
                'id': channel_config.channel_id,
                'username': channel_config.channel_username,
                'title': channel_config.channel_title,
                'type': channel_config.channel_type,
                'member_count': channel_config.channel_member_count,
                'is_validated': channel_config.is_validated,
                'last_validation_at': channel_config.last_validation_at.isoformat() if channel_config.last_validation_at else None,
                'permissions': {
                    'can_post_messages': channel_config.can_post_messages,
                    'can_edit_messages': channel_config.can_edit_messages,
                    'can_send_media_messages': channel_config.can_send_media_messages,
                    'can_delete_messages': channel_config.can_delete_messages,
                    'can_pin_messages': channel_config.can_pin_messages
                },
                'created_at': channel_config.created_at.isoformat() if channel_config.created_at else None,
                'updated_at': channel_config.updated_at.isoformat() if channel_config.updated_at else None
            },
            'requested_by': service_name,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        })
        
    except Exception as e:
        logger.error(f"Error getting channel config for service: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'code': 'INTERNAL_ERROR'
        }), 500

@service_api_bp.route('/channel/<int:bot_id>/status', methods=['GET'])
@require_service_token
@require_service_permission('verify_channel_status')
def get_channel_status_for_service(bot_id):
    """
    Get channel status for a bot (service endpoint)
    
    GET /api/service/channel/{bot_id}/status
    
    Headers:
        X-Service-Token: Valid service token
    
    Returns:
        Channel status information
    """
    try:
        service_name = get_requesting_service()
        logger.info(f"Service {service_name} requesting channel status for bot_id {bot_id}")
        
        # Get account information
        account = get_account_by_bot_id(bot_id)
        if not account:
            return jsonify({
                'success': False,
                'error': 'Account not found',
                'code': 'ACCOUNT_NOT_FOUND',
                'bot_id': bot_id,
                'status': 'account_not_found'
            }), 404
        
        # Get channel configuration
        channel_config = ChannelConfig.query.filter_by(account_id=bot_id).first()
        
        if not channel_config:
            return jsonify({
                'success': True,
                'bot_id': bot_id,
                'account_id': account.get('id') if account else None,
                'status': 'not_configured',
                'message': 'Channel not configured for this bot',
                'next_steps': 'Bot owner needs to configure a channel first',
                'requested_by': service_name,
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            })
        
        # Determine status
        if not channel_config.is_validated:
            status = 'configured_not_validated'
            message = 'Channel configured but validation failed'
        elif channel_config.validation_error:
            status = 'validation_error'
            message = f'Channel validation error: {channel_config.validation_error}'
        else:
            status = 'active'
            message = 'Channel configured and validated'
        
        return jsonify({
            'success': True,
            'bot_id': bot_id,
            'account_id': account.get('id') if account else None,
            'status': status,
            'message': message,
            'channel': {
                'id': channel_config.channel_id,
                'username': channel_config.channel_username,
                'title': channel_config.channel_title,
                'is_validated': channel_config.is_validated,
                'last_validation_at': channel_config.last_validation_at.isoformat() if channel_config.last_validation_at else None,
                'validation_error': channel_config.validation_error
            },
            'requested_by': service_name,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        })
        
    except Exception as e:
        logger.error(f"Error getting channel status for service: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'code': 'INTERNAL_ERROR'
        }), 500

@service_api_bp.route('/channels/batch', methods=['POST'])
@require_service_token
@require_service_permission('read_channel_config')
def get_multiple_channel_configs(bot_ids):
    """
    Get channel configurations for multiple bots (batch endpoint)
    
    POST /api/service/channels/batch
    
    Headers:
        X-Service-Token: Valid service token
    
    Body:
        {
            "bot_ids": [262662172, 123456789, ...]
        }
    
    Returns:
        Channel configurations for all requested bots
    """
    try:
        service_name = get_requesting_service()
        data = request.get_json()
        
        if not data or 'bot_ids' not in data:
            return jsonify({
                'success': False,
                'error': 'bot_ids array required',
                'code': 'MISSING_BOT_IDS'
            }), 400
        
        bot_ids = data['bot_ids']
        if not isinstance(bot_ids, list):
            return jsonify({
                'success': False,
                'error': 'bot_ids must be an array',
                'code': 'INVALID_BOT_IDS'
            }), 400
        
        logger.info(f"Service {service_name} requesting batch channel configs for {len(bot_ids)} bots")
        
        results = []
        
        for bot_id in bot_ids:
            try:
                # Get account information
                account = get_account_by_bot_id(bot_id)
                if not account:
                    results.append({
                        'bot_id': bot_id,
                        'success': False,
                        'error': 'Account not found',
                        'code': 'ACCOUNT_NOT_FOUND'
                    })
                    continue
                
                # Get channel configuration
                channel_config = ChannelConfig.query.filter_by(account_id=bot_id).first()
                
                if not channel_config:
                    results.append({
                        'bot_id': bot_id,
                        'account_id': account.get('id') if account else None,
                        'success': False,
                        'error': 'Channel not configured',
                        'code': 'CHANNEL_NOT_CONFIGURED'
                    })
                    continue
                
                # Add successful result
                results.append({
                    'bot_id': bot_id,
                    'account_id': account.get('id') if account else None,
                    'success': True,
                    'channel': {
                        'id': channel_config.channel_id,
                        'username': channel_config.channel_username,
                        'title': channel_config.channel_title,
                        'type': channel_config.channel_type,
                        'is_validated': channel_config.is_validated,
                        'permissions': {
                            'can_post_messages': channel_config.can_post_messages,
                            'can_edit_messages': channel_config.can_edit_messages,
                            'can_send_media_messages': channel_config.can_send_media_messages,
                            'can_delete_messages': channel_config.can_delete_messages,
                            'can_pin_messages': channel_config.can_pin_messages
                        }
                    }
                })
                
            except Exception as e:
                logger.error(f"Error processing bot_id {bot_id}: {str(e)}")
                results.append({
                    'bot_id': bot_id,
                    'success': False,
                    'error': 'Processing error',
                    'code': 'PROCESSING_ERROR'
                })
        
        return jsonify({
            'success': True,
            'results': results,
            'total_requested': len(bot_ids),
            'total_processed': len(results),
            'requested_by': service_name,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        })
        
    except Exception as e:
        logger.error(f"Error in batch channel config request: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'code': 'INTERNAL_ERROR'
        }), 500

@service_api_bp.route('/health', methods=['GET'])
@require_service_token
def service_health():
    """
    Health check endpoint for services
    
    GET /api/service/health
    
    Headers:
        X-Service-Token: Valid service token
    """
    service_name = get_requesting_service()
    
    return jsonify({
        'success': True,
        'service': 'channel-service',
        'status': 'healthy',
        'requested_by': service_name,
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'available_endpoints': [
            'GET /api/service/channel/{bot_id}',
            'GET /api/service/channel/{bot_id}/status',
            'POST /api/service/channels/batch',
            'GET /api/service/health'
        ]
    })

