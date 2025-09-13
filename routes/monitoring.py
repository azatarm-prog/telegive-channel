"""
Monitoring and account status endpoints for Channel Management Service
"""
from flask import Blueprint, request, jsonify
import logging
import time
from datetime import datetime, timedelta
from models import ChannelConfig, db
from utils.error_handling import (
    AccountNotFoundError, 
    create_error_response, 
    create_success_response,
    log_account_lookup
)

logger = logging.getLogger(__name__)
monitoring_bp = Blueprint('monitoring', __name__, url_prefix='/api/monitoring')

# In-memory metrics (in production, use Redis or proper metrics store)
account_metrics = {
    'lookups_total': 0,
    'lookups_failed': 0,
    'missing_accounts': set(),
    'last_reset': datetime.utcnow()
}

def get_bot_credentials(account_id):
    """
    Get bot credentials for an account from the Auth Service
    (Imported from accounts.py for consistency)
    """
    import os
    import requests
    
    auth_service_url = os.getenv('TELEGIVE_AUTH_URL', 'https://web-production-ddd7e.up.railway.app')
    
    try:
        # First, get account information to verify account exists and get bot_id
        account_response = requests.get(
            f"{auth_service_url}/api/auth/account/{account_id}",
            timeout=10
        )
        
        if account_response.status_code == 404:
            raise AccountNotFoundError(account_id, {
                "auth_service_response": "Account not found in auth service",
                "auth_service_url": auth_service_url
            })
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
            'account_info': account_info
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

@monitoring_bp.route('/accounts/<int:account_id>/status', methods=['GET'])
def get_account_status(account_id):
    """
    Get comprehensive status for an account
    GET /api/monitoring/accounts/{account_id}/status
    """
    start_time = time.time()
    
    try:
        # Track the lookup attempt
        account_metrics['lookups_total'] += 1
        
        # Check if account exists in auth service
        try:
            credentials = get_bot_credentials(account_id)
            account_found = True
            auth_service_error = None
            
            # Additional validations
            bot_token = credentials.get('bot_token', '')
            validations = {
                'has_bot_token': bool(bot_token),
                'token_format_valid': bool(bot_token and len(bot_token.split(':')) == 2),
                'auth_service_accessible': True
            }
            
            log_account_lookup(account_id, True, (time.time() - start_time) * 1000)
            
        except AccountNotFoundError as e:
            account_found = False
            auth_service_error = e.message
            validations = {
                'has_bot_token': False,
                'token_format_valid': False,
                'auth_service_accessible': True
            }
            
            # Track missing account
            account_metrics['lookups_failed'] += 1
            account_metrics['missing_accounts'].add(account_id)
            
            log_account_lookup(account_id, False, (time.time() - start_time) * 1000)
            
        except Exception as e:
            account_found = False
            auth_service_error = str(e)
            validations = {
                'has_bot_token': False,
                'token_format_valid': False,
                'auth_service_accessible': False
            }
            
            account_metrics['lookups_failed'] += 1
            log_account_lookup(account_id, False, (time.time() - start_time) * 1000)
        
        # Check channel configuration in database
        channel_config = ChannelConfig.query.filter_by(account_id=account_id).first()
        
        channel_status = {
            'has_channel_config': bool(channel_config),
            'channel_username': channel_config.channel_username if channel_config else None,
            'channel_verified': channel_config.is_validated if channel_config else False,
            'last_validation': channel_config.last_validation_at.isoformat() + 'Z' if channel_config and channel_config.last_validation_at else None
        }
        
        # Calculate response time
        response_time_ms = (time.time() - start_time) * 1000
        
        response_data = {
            'account_id': account_id,
            'account_found': account_found,
            'auth_service_error': auth_service_error,
            'validations': validations,
            'channel_status': channel_status,
            'response_time_ms': round(response_time_ms, 2),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
        
        if account_found:
            return jsonify(create_success_response(response_data)), 200
        else:
            return jsonify({
                'success': False,
                'code': 'ACCOUNT_NOT_FOUND',
                'error': f'Account {account_id} not found in auth service',
                **response_data
            }), 404
    
    except Exception as e:
        logger.error(f"Account status check failed for {account_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error during account status check',
            'code': 'INTERNAL_ERROR',
            'account_id': account_id,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 500

@monitoring_bp.route('/metrics', methods=['GET'])
def get_service_metrics():
    """
    Get service metrics and statistics
    GET /api/monitoring/metrics
    """
    try:
        # Calculate failure rate
        failure_rate = 0
        if account_metrics['lookups_total'] > 0:
            failure_rate = account_metrics['lookups_failed'] / account_metrics['lookups_total']
        
        # Get database statistics
        total_channels = ChannelConfig.query.count()
        verified_channels = ChannelConfig.query.filter_by(is_validated=True).count()
        
        # Recent activity (last 24 hours)
        yesterday = datetime.utcnow() - timedelta(days=1)
        recent_channels = ChannelConfig.query.filter(ChannelConfig.created_at >= yesterday).count()
        
        metrics = {
            'service': {
                'name': 'channel-service',
                'version': '1.0.0',
                'uptime_since': account_metrics['last_reset'].isoformat() + 'Z',
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            },
            'account_lookups': {
                'total': account_metrics['lookups_total'],
                'failed': account_metrics['lookups_failed'],
                'failure_rate': round(failure_rate, 4),
                'missing_accounts_count': len(account_metrics['missing_accounts'])
            },
            'channel_statistics': {
                'total_channels': total_channels,
                'verified_channels': verified_channels,
                'verification_rate': round(verified_channels / total_channels, 4) if total_channels > 0 else 0,
                'recent_channels_24h': recent_channels
            },
            'health_indicators': {
                'high_failure_rate': failure_rate > 0.1,  # More than 10% failures
                'many_missing_accounts': len(account_metrics['missing_accounts']) > 10,
                'low_verification_rate': (verified_channels / total_channels) < 0.5 if total_channels > 0 else False
            }
        }
        
        return jsonify(create_success_response(metrics)), 200
    
    except Exception as e:
        logger.error(f"Error getting service metrics: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve service metrics',
            'code': 'METRICS_ERROR',
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 500

@monitoring_bp.route('/metrics/reset', methods=['POST'])
def reset_metrics():
    """
    Reset service metrics (for testing/maintenance)
    POST /api/monitoring/metrics/reset
    """
    try:
        global account_metrics
        account_metrics = {
            'lookups_total': 0,
            'lookups_failed': 0,
            'missing_accounts': set(),
            'last_reset': datetime.utcnow()
        }
        
        logger.info("Service metrics reset")
        
        return jsonify(create_success_response({
            'message': 'Service metrics reset successfully',
            'reset_at': datetime.utcnow().isoformat() + 'Z'
        })), 200
    
    except Exception as e:
        logger.error(f"Error resetting metrics: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to reset metrics',
            'code': 'RESET_ERROR'
        }), 500

@monitoring_bp.route('/health/detailed', methods=['GET'])
def get_detailed_health():
    """
    Get detailed health check with comprehensive system status
    GET /api/monitoring/health/detailed
    """
    try:
        start_time = time.time()
        
        # Test database connection
        try:
            db.session.execute(db.text('SELECT 1')).fetchone()
            database_status = 'connected'
            database_error = None
        except Exception as e:
            database_status = 'disconnected'
            database_error = str(e)
        
        # Test auth service connection
        try:
            import requests
            import os
            auth_service_url = os.getenv('TELEGIVE_AUTH_URL', 'https://web-production-ddd7e.up.railway.app')
            auth_response = requests.get(f"{auth_service_url}/health", timeout=5)
            auth_service_status = 'accessible' if auth_response.status_code == 200 else 'error'
            auth_service_error = None if auth_response.status_code == 200 else f"HTTP {auth_response.status_code}"
        except Exception as e:
            auth_service_status = 'unreachable'
            auth_service_error = str(e)
        
        # Test Telegram API
        try:
            telegram_response = requests.get('https://api.telegram.org', timeout=5)
            telegram_status = 'accessible' if telegram_response.status_code in [200, 404] else 'error'
            telegram_error = None
        except Exception as e:
            telegram_status = 'unreachable'
            telegram_error = str(e)
        
        # Calculate overall health
        all_healthy = all([
            database_status == 'connected',
            auth_service_status == 'accessible',
            telegram_status == 'accessible'
        ])
        
        overall_status = 'healthy' if all_healthy else 'degraded'
        
        response_time_ms = (time.time() - start_time) * 1000
        
        health_data = {
            'service': 'channel-service',
            'version': '1.0.0',
            'status': overall_status,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'response_time_ms': round(response_time_ms, 2),
            'components': {
                'database': {
                    'status': database_status,
                    'error': database_error
                },
                'auth_service': {
                    'status': auth_service_status,
                    'error': auth_service_error,
                    'url': os.getenv('TELEGIVE_AUTH_URL', 'https://web-production-ddd7e.up.railway.app')
                },
                'telegram_api': {
                    'status': telegram_status,
                    'error': telegram_error
                }
            },
            'metrics_summary': {
                'total_lookups': account_metrics['lookups_total'],
                'failed_lookups': account_metrics['lookups_failed'],
                'missing_accounts': len(account_metrics['missing_accounts'])
            }
        }
        
        status_code = 200 if all_healthy else 503
        return jsonify(create_success_response(health_data)), status_code
    
    except Exception as e:
        logger.error(f"Detailed health check failed: {str(e)}")
        return jsonify({
            'success': False,
            'service': 'channel-service',
            'status': 'error',
            'error': 'Health check failed',
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 500

