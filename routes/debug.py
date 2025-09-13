"""
Debug routes for Channel Service - REMOVE IN PRODUCTION
These endpoints help debug token retrieval and Telegram API integration
"""

from flask import Blueprint, jsonify, request
import logging
import requests
from utils.account_lookup import get_account_by_bot_id, get_bot_credentials_from_db

debug_bp = Blueprint('debug', __name__)
logger = logging.getLogger(__name__)

@debug_bp.route('/debug/token/<int:bot_id>', methods=['GET'])
def debug_token_retrieval(bot_id):
    """
    Debug endpoint to check token retrieval for a specific bot_id
    WARNING: This exposes sensitive information - REMOVE IN PRODUCTION
    """
    
    try:
        logger.info(f"🔍 Debug token retrieval for bot_id: {bot_id}")
        
        # Step 1: Account lookup
        account = get_account_by_bot_id(bot_id)
        
        if not account:
            return jsonify({
                'success': False,
                'error': 'Account not found',
                'bot_id': bot_id
            }), 404
        
        # Step 2: Check available fields
        available_fields = list(account.keys()) if isinstance(account, dict) else dir(account)
        
        # Step 3: Check token fields
        bot_token = account.get('bot_token')
        bot_token_encrypted = account.get('bot_token_encrypted')
        encrypted_token = account.get('encrypted_token')
        
        # Step 4: Try credentials retrieval
        credentials = None
        credentials_error = None
        
        try:
            credentials = get_bot_credentials_from_db(bot_id)
        except Exception as e:
            credentials_error = str(e)
        
        # Step 5: Test token with Telegram API (if available)
        telegram_test = None
        if credentials and credentials.get('bot_token'):
            test_token = credentials['bot_token']
            try:
                response = requests.get(f'https://api.telegram.org/bot{test_token}/getMe', timeout=5)
                telegram_test = {
                    'status_code': response.status_code,
                    'response': response.json(),
                    'token_format_valid': ':' in str(test_token),
                    'token_length': len(str(test_token)),
                    'starts_with_bot_id': str(test_token).startswith(str(bot_id))
                }
            except Exception as e:
                telegram_test = {'error': str(e)}
        
        return jsonify({
            'success': True,
            'bot_id': bot_id,
            'account_found': True,
            'database_id': account.get('id'),
            'available_fields': available_fields,
            'token_fields': {
                'bot_token': 'FOUND' if bot_token else 'MISSING',
                'bot_token_encrypted': 'FOUND' if bot_token_encrypted else 'MISSING',
                'encrypted_token': 'FOUND' if encrypted_token else 'MISSING'
            },
            'credentials_retrieval': {
                'success': credentials is not None,
                'error': credentials_error,
                'token_available': bool(credentials and credentials.get('bot_token')) if credentials else False
            },
            'telegram_api_test': telegram_test,
            'warning': 'This endpoint exposes sensitive information - REMOVE IN PRODUCTION'
        })
        
    except Exception as e:
        logger.error(f"Debug endpoint error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'bot_id': bot_id
        }), 500

@debug_bp.route('/debug/telegram-test', methods=['POST'])
def debug_telegram_test():
    """
    Test Telegram API with provided token
    WARNING: This accepts tokens in request - REMOVE IN PRODUCTION
    """
    
    try:
        data = request.get_json()
        test_token = data.get('token')
        
        if not test_token:
            return jsonify({
                'success': False,
                'error': 'Token required in request body'
            }), 400
        
        # Test getMe
        getme_response = requests.get(f'https://api.telegram.org/bot{test_token}/getMe', timeout=10)
        getme_data = getme_response.json()
        
        result = {
            'success': True,
            'token_format': {
                'length': len(str(test_token)),
                'has_colon': ':' in str(test_token),
                'format_valid': ':' in str(test_token) and len(str(test_token)) > 20
            },
            'getme_test': {
                'status_code': getme_response.status_code,
                'response': getme_data,
                'success': getme_data.get('ok', False)
            }
        }
        
        # If getMe works, test channel access
        if getme_data.get('ok'):
            try:
                channel_response = requests.get(
                    f'https://api.telegram.org/bot{test_token}/getChat',
                    params={'chat_id': '@dxstest'},
                    timeout=10
                )
                result['channel_test'] = {
                    'status_code': channel_response.status_code,
                    'response': channel_response.json(),
                    'success': channel_response.json().get('ok', False)
                }
            except Exception as e:
                result['channel_test'] = {'error': str(e)}
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@debug_bp.route('/debug/compare-tokens', methods=['POST'])
def debug_compare_tokens():
    """
    Compare retrieved token with expected working token
    WARNING: This exposes token information - REMOVE IN PRODUCTION
    """
    
    try:
        data = request.get_json()
        bot_id = data.get('bot_id', 262662172)
        
        # Get token from Channel Service
        try:
            credentials = get_bot_credentials_from_db(bot_id)
            retrieved_token = credentials.get('bot_token') if credentials else None
        except Exception as e:
            retrieved_token = None
            retrieval_error = str(e)
        
        # Expected working token (from manual tests)
        expected_token = "262662172:AAGyAYVzuFFe23GagWY-FnP2NlAQRy_JsRk"
        
        comparison = {
            'bot_id': bot_id,
            'retrieved_token': {
                'found': retrieved_token is not None,
                'length': len(str(retrieved_token)) if retrieved_token else 0,
                'format_valid': ':' in str(retrieved_token) if retrieved_token else False,
                'matches_expected': str(retrieved_token) == expected_token if retrieved_token else False
            },
            'expected_token': {
                'length': len(expected_token),
                'format_valid': ':' in expected_token
            },
            'tokens_match': str(retrieved_token) == expected_token if retrieved_token else False
        }
        
        # Test both tokens if available
        if retrieved_token:
            try:
                response = requests.get(f'https://api.telegram.org/bot{retrieved_token}/getMe', timeout=5)
                comparison['retrieved_token']['telegram_test'] = {
                    'success': response.json().get('ok', False),
                    'response': response.json()
                }
            except Exception as e:
                comparison['retrieved_token']['telegram_test'] = {'error': str(e)}
        
        return jsonify({
            'success': True,
            'comparison': comparison,
            'warning': 'This endpoint exposes token information - REMOVE IN PRODUCTION'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

