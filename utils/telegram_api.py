import requests
import logging
from typing import Dict, Any, Optional
from config.settings import Config

logger = logging.getLogger(__name__)

class TelegramAPIError(Exception):
    """Custom exception for Telegram API errors"""
    pass

def get_channel_info(bot_token: str, channel_username: str) -> Dict[str, Any]:
    """
    Get channel information from Telegram API
    
    Args:
        bot_token: Bot token for authentication
        channel_username: Channel username (with or without @)
    
    Returns:
        Dict containing success status and channel info or error
    """
    try:
        # Ensure channel username starts with @
        if not channel_username.startswith('@'):
            channel_username = f'@{channel_username}'
        
        url = f"{Config.TELEGRAM_API_BASE}/bot{bot_token}/getChat"
        params = {'chat_id': channel_username}
        
        response = requests.get(url, params=params, timeout=Config.VALIDATION_TIMEOUT)
        
        if response.ok:
            data = response.json()
            if data.get('ok'):
                channel_info = data['result']
                return {
                    'success': True,
                    'channel_info': {
                        'id': channel_info.get('id'),
                        'title': channel_info.get('title'),
                        'username': channel_info.get('username'),
                        'type': channel_info.get('type'),
                        'members_count': channel_info.get('members_count', 0)
                    }
                }
            else:
                return {
                    'success': False,
                    'error': data.get('description', 'Unknown Telegram API error')
                }
        else:
            return {
                'success': False,
                'error': f'HTTP {response.status_code}: Channel not found or not accessible'
            }
    
    except requests.Timeout:
        return {
            'success': False,
            'error': 'Telegram API request timeout'
        }
    except requests.RequestException as e:
        return {
            'success': False,
            'error': f'Network error: {str(e)}'
        }
    except Exception as e:
        logger.error(f"Unexpected error in get_channel_info: {str(e)}")
        return {
            'success': False,
            'error': f'Unexpected error: {str(e)}'
        }

def get_bot_member_info(bot_token: str, channel_id: int, bot_id: int) -> Dict[str, Any]:
    """
    Get bot member information in a channel
    
    Args:
        bot_token: Bot token for authentication
        channel_id: Channel ID (negative for channels/supergroups)
        bot_id: Bot user ID
    
    Returns:
        Dict containing success status and member info or error
    """
    try:
        url = f"{Config.TELEGRAM_API_BASE}/bot{bot_token}/getChatMember"
        params = {
            'chat_id': channel_id,
            'user_id': bot_id
        }
        
        response = requests.get(url, params=params, timeout=Config.VALIDATION_TIMEOUT)
        
        if response.ok:
            data = response.json()
            if data.get('ok'):
                member_info = data['result']
                return {
                    'success': True,
                    'member_info': {
                        'status': member_info.get('status'),
                        'can_post_messages': member_info.get('can_post_messages', False),
                        'can_edit_messages': member_info.get('can_edit_messages', False),
                        'can_send_media_messages': member_info.get('can_send_media_messages', False),
                        'can_delete_messages': member_info.get('can_delete_messages', False),
                        'can_pin_messages': member_info.get('can_pin_messages', False)
                    }
                }
            else:
                return {
                    'success': False,
                    'error': data.get('description', 'Unknown Telegram API error')
                }
        else:
            return {
                'success': False,
                'error': f'HTTP {response.status_code}: Unable to get member info'
            }
    
    except requests.Timeout:
        return {
            'success': False,
            'error': 'Telegram API request timeout'
        }
    except requests.RequestException as e:
        return {
            'success': False,
            'error': f'Network error: {str(e)}'
        }
    except Exception as e:
        logger.error(f"Unexpected error in get_bot_member_info: {str(e)}")
        return {
            'success': False,
            'error': f'Unexpected error: {str(e)}'
        }

def validate_channel_setup(bot_token: str, bot_id: int, channel_username: str) -> Dict[str, Any]:
    """
    Validate complete channel setup including permissions
    
    Args:
        bot_token: Bot token for authentication
        bot_id: Bot user ID
        channel_username: Channel username to validate
    
    Returns:
        Dict containing validation result with channel info and permissions
    """
    try:
        # Step 1: Get channel information
        channel_result = get_channel_info(bot_token, channel_username)
        if not channel_result['success']:
            return channel_result
        
        channel_info = channel_result['channel_info']
        channel_id = channel_info['id']
        
        # Step 2: Get bot member information
        member_result = get_bot_member_info(bot_token, channel_id, bot_id)
        if not member_result['success']:
            return member_result
        
        member_info = member_result['member_info']
        
        # Step 3: Check if bot is administrator
        if member_info['status'] != 'administrator':
            return {
                'success': False,
                'error': 'Bot is not an administrator in the channel'
            }
        
        # Step 4: Check required permissions
        missing_permissions = []
        permissions = member_info
        
        for required_perm in Config.REQUIRED_PERMISSIONS:
            if not permissions.get(required_perm, False):
                missing_permissions.append(required_perm)
        
        if missing_permissions:
            return {
                'success': False,
                'error': f'Bot lacks required permissions: {", ".join(missing_permissions)}'
            }
        
        # Step 5: Return successful validation
        return {
            'success': True,
            'channel_info': channel_info,
            'permissions': {
                'can_post_messages': permissions.get('can_post_messages', False),
                'can_edit_messages': permissions.get('can_edit_messages', False),
                'can_send_media_messages': permissions.get('can_send_media_messages', False),
                'can_delete_messages': permissions.get('can_delete_messages', False),
                'can_pin_messages': permissions.get('can_pin_messages', False)
            }
        }
    
    except Exception as e:
        logger.error(f"Unexpected error in validate_channel_setup: {str(e)}")
        return {
            'success': False,
            'error': f'Validation failed: {str(e)}'
        }

def get_bot_info(bot_token: str) -> Dict[str, Any]:
    """
    Get bot information from Telegram API
    
    Args:
        bot_token: Bot token for authentication
    
    Returns:
        Dict containing bot information or error
    """
    try:
        url = f"{Config.TELEGRAM_API_BASE}/bot{bot_token}/getMe"
        
        response = requests.get(url, timeout=Config.VALIDATION_TIMEOUT)
        
        if response.ok:
            data = response.json()
            if data.get('ok'):
                bot_info = data['result']
                return {
                    'success': True,
                    'bot_info': {
                        'id': bot_info.get('id'),
                        'username': bot_info.get('username'),
                        'first_name': bot_info.get('first_name'),
                        'is_bot': bot_info.get('is_bot', False)
                    }
                }
            else:
                return {
                    'success': False,
                    'error': data.get('description', 'Unknown Telegram API error')
                }
        else:
            return {
                'success': False,
                'error': f'HTTP {response.status_code}: Invalid bot token'
            }
    
    except requests.Timeout:
        return {
            'success': False,
            'error': 'Telegram API request timeout'
        }
    except requests.RequestException as e:
        return {
            'success': False,
            'error': f'Network error: {str(e)}'
        }
    except Exception as e:
        logger.error(f"Unexpected error in get_bot_info: {str(e)}")
        return {
            'success': False,
            'error': f'Unexpected error: {str(e)}'
        }

