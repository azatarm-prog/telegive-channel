import logging
from typing import Dict, Any, Optional
from datetime import datetime
from models import ChannelConfig, ChannelValidationHistory, db
from utils.telegram_api import validate_channel_setup, get_bot_member_info
from config.settings import Config

logger = logging.getLogger(__name__)

def validate_channel_permissions(channel_config: ChannelConfig, bot_token: str, bot_id: int) -> Dict[str, Any]:
    """
    Validate current permissions for a channel configuration
    
    Args:
        channel_config: ChannelConfig instance
        bot_token: Bot token for API calls
        bot_id: Bot user ID
    
    Returns:
        Dict containing validation result
    """
    try:
        # Get current bot member info from Telegram
        member_result = get_bot_member_info(bot_token, channel_config.channel_id, bot_id)
        
        if not member_result['success']:
            # Log validation failure
            validation_record = ChannelValidationHistory.create_validation_record(
                channel_config_id=channel_config.id,
                validation_type='permission_check',
                result=False,
                error_message=member_result['error']
            )
            db.session.add(validation_record)
            
            # Update channel config
            channel_config.is_validated = False
            channel_config.last_validation_at = datetime.utcnow()
            channel_config.validation_error = member_result['error']
            
            db.session.commit()
            
            return {
                'valid': False,
                'error': member_result['error'],
                'permissions_changed': False
            }
        
        member_info = member_result['member_info']
        
        # Check if bot is still administrator
        if member_info['status'] != 'administrator':
            error_msg = 'Bot is no longer an administrator in the channel'
            
            # Log validation failure
            validation_record = ChannelValidationHistory.create_validation_record(
                channel_config_id=channel_config.id,
                validation_type='permission_check',
                result=False,
                error_message=error_msg,
                permissions=member_info
            )
            db.session.add(validation_record)
            
            # Update channel config
            channel_config.is_validated = False
            channel_config.last_validation_at = datetime.utcnow()
            channel_config.validation_error = error_msg
            
            db.session.commit()
            
            return {
                'valid': False,
                'error': error_msg,
                'permissions_changed': False
            }
        
        # Compare current permissions with stored permissions
        current_permissions = {
            'can_post_messages': member_info.get('can_post_messages', False),
            'can_edit_messages': member_info.get('can_edit_messages', False),
            'can_send_media_messages': member_info.get('can_send_media_messages', False),
            'can_delete_messages': member_info.get('can_delete_messages', False),
            'can_pin_messages': member_info.get('can_pin_messages', False)
        }
        
        stored_permissions = channel_config.get_permissions_dict()
        permissions_changed = current_permissions != stored_permissions
        
        # Check if required permissions are still present
        missing_permissions = []
        for required_perm in Config.REQUIRED_PERMISSIONS:
            if not current_permissions.get(required_perm, False):
                missing_permissions.append(required_perm)
        
        validation_successful = len(missing_permissions) == 0
        
        # Update stored permissions if changed
        if permissions_changed:
            channel_config.update_permissions(current_permissions)
        
        # Update validation status
        channel_config.is_validated = validation_successful
        channel_config.last_validation_at = datetime.utcnow()
        
        if validation_successful:
            channel_config.validation_error = None
        else:
            channel_config.validation_error = f'Missing required permissions: {", ".join(missing_permissions)}'
        
        # Log validation result
        validation_record = ChannelValidationHistory.create_validation_record(
            channel_config_id=channel_config.id,
            validation_type='permission_check',
            result=validation_successful,
            error_message=channel_config.validation_error,
            permissions=current_permissions
        )
        db.session.add(validation_record)
        
        db.session.commit()
        
        return {
            'valid': validation_successful,
            'permissions_changed': permissions_changed,
            'current_permissions': current_permissions,
            'missing_permissions': missing_permissions if not validation_successful else []
        }
    
    except Exception as e:
        logger.error(f"Error validating channel permissions: {str(e)}")
        
        # Log validation error
        try:
            validation_record = ChannelValidationHistory.create_validation_record(
                channel_config_id=channel_config.id,
                validation_type='permission_check',
                result=False,
                error_message=f'Validation error: {str(e)}'
            )
            db.session.add(validation_record)
            
            channel_config.is_validated = False
            channel_config.last_validation_at = datetime.utcnow()
            channel_config.validation_error = f'Validation error: {str(e)}'
            
            db.session.commit()
        except Exception as db_error:
            logger.error(f"Error logging validation failure: {str(db_error)}")
        
        return {
            'valid': False,
            'error': f'Validation error: {str(e)}',
            'permissions_changed': False
        }

def setup_channel_configuration(account_id: int, channel_username: str, bot_token: str, bot_id: int) -> Dict[str, Any]:
    """
    Setup and validate a new channel configuration
    
    Args:
        account_id: Account ID
        channel_username: Channel username
        bot_token: Bot token for API calls
        bot_id: Bot user ID
    
    Returns:
        Dict containing setup result
    """
    try:
        # Check if account already has a channel configured
        existing_config = ChannelConfig.query.filter_by(account_id=account_id).first()
        if existing_config:
            return {
                'success': False,
                'error': 'Account already has a channel configured'
            }
        
        # Validate channel setup with Telegram API
        validation_result = validate_channel_setup(bot_token, bot_id, channel_username)
        
        if not validation_result['success']:
            return validation_result
        
        channel_info = validation_result['channel_info']
        permissions = validation_result['permissions']
        
        # Create new channel configuration
        channel_config = ChannelConfig(
            account_id=account_id,
            channel_id=channel_info['id'],
            channel_username=channel_info.get('username', channel_username.lstrip('@')),
            channel_title=channel_info['title'],
            channel_type=channel_info.get('type', 'channel'),
            channel_member_count=channel_info.get('members_count', 0),
            can_post_messages=permissions['can_post_messages'],
            can_edit_messages=permissions['can_edit_messages'],
            can_send_media_messages=permissions['can_send_media_messages'],
            can_delete_messages=permissions['can_delete_messages'],
            can_pin_messages=permissions['can_pin_messages'],
            is_validated=True,
            last_validation_at=datetime.utcnow()
        )
        
        db.session.add(channel_config)
        db.session.flush()  # Get the ID
        
        # Log successful setup
        validation_record = ChannelValidationHistory.create_validation_record(
            channel_config_id=channel_config.id,
            validation_type='setup',
            result=True,
            permissions=permissions
        )
        db.session.add(validation_record)
        
        db.session.commit()
        
        return {
            'success': True,
            'channel_info': channel_info,
            'permissions': permissions,
            'channel_config': channel_config.to_dict()
        }
    
    except Exception as e:
        logger.error(f"Error setting up channel configuration: {str(e)}")
        db.session.rollback()
        return {
            'success': False,
            'error': f'Setup error: {str(e)}'
        }

def revalidate_channel(channel_config: ChannelConfig, bot_token: str, bot_id: int) -> Dict[str, Any]:
    """
    Force revalidation of a channel configuration
    
    Args:
        channel_config: ChannelConfig instance
        bot_token: Bot token for API calls
        bot_id: Bot user ID
    
    Returns:
        Dict containing revalidation result
    """
    try:
        # Perform full validation
        validation_result = validate_channel_permissions(channel_config, bot_token, bot_id)
        
        # Also update channel info if possible
        from utils.telegram_api import get_channel_info
        channel_info_result = get_channel_info(bot_token, f"@{channel_config.channel_username}")
        
        if channel_info_result['success']:
            channel_info = channel_info_result['channel_info']
            channel_config.channel_title = channel_info['title']
            channel_config.channel_member_count = channel_info.get('members_count', 0)
            db.session.commit()
        
        return {
            'success': True,
            'validation_result': validation_result,
            'channel_info_updated': channel_info_result['success']
        }
    
    except Exception as e:
        logger.error(f"Error revalidating channel: {str(e)}")
        return {
            'success': False,
            'error': f'Revalidation error: {str(e)}'
        }

