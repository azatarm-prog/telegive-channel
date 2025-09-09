import logging
from typing import Dict, List, Any, Optional
from models import ChannelConfig
from config.settings import Config

logger = logging.getLogger(__name__)

def check_required_permissions(permissions: Dict[str, bool]) -> Dict[str, Any]:
    """
    Check if permissions meet the required criteria
    
    Args:
        permissions: Dict of permission names to boolean values
    
    Returns:
        Dict containing check result
    """
    missing_permissions = []
    
    for required_perm in Config.REQUIRED_PERMISSIONS:
        if not permissions.get(required_perm, False):
            missing_permissions.append(required_perm)
    
    return {
        'has_required_permissions': len(missing_permissions) == 0,
        'missing_permissions': missing_permissions,
        'all_permissions': permissions
    }

def get_permission_requirements() -> Dict[str, Any]:
    """
    Get the list of required permissions and their descriptions
    
    Returns:
        Dict containing permission requirements
    """
    permission_descriptions = {
        'can_post_messages': 'Required to post giveaway announcements',
        'can_edit_messages': 'Required to update giveaway posts',
        'can_send_media_messages': 'Required to send images and media in posts',
        'can_delete_messages': 'Optional: Allows deleting old posts',
        'can_pin_messages': 'Optional: Allows pinning important announcements'
    }
    
    required_permissions = []
    optional_permissions = []
    
    for perm, description in permission_descriptions.items():
        perm_info = {
            'permission': perm,
            'description': description
        }
        
        if perm in Config.REQUIRED_PERMISSIONS:
            required_permissions.append(perm_info)
        else:
            optional_permissions.append(perm_info)
    
    return {
        'required_permissions': required_permissions,
        'optional_permissions': optional_permissions,
        'total_permissions': len(permission_descriptions)
    }

def compare_permissions(old_permissions: Dict[str, bool], new_permissions: Dict[str, bool]) -> Dict[str, Any]:
    """
    Compare two sets of permissions and identify changes
    
    Args:
        old_permissions: Previous permission set
        new_permissions: Current permission set
    
    Returns:
        Dict containing permission comparison
    """
    changes = {}
    gained_permissions = []
    lost_permissions = []
    
    all_permissions = set(old_permissions.keys()) | set(new_permissions.keys())
    
    for perm in all_permissions:
        old_value = old_permissions.get(perm, False)
        new_value = new_permissions.get(perm, False)
        
        if old_value != new_value:
            changes[perm] = {
                'old': old_value,
                'new': new_value
            }
            
            if new_value and not old_value:
                gained_permissions.append(perm)
            elif old_value and not new_value:
                lost_permissions.append(perm)
    
    # Check if any required permissions were lost
    lost_required = [perm for perm in lost_permissions if perm in Config.REQUIRED_PERMISSIONS]
    
    return {
        'has_changes': len(changes) > 0,
        'changes': changes,
        'gained_permissions': gained_permissions,
        'lost_permissions': lost_permissions,
        'lost_required_permissions': lost_required,
        'critical_loss': len(lost_required) > 0
    }

def validate_permission_update(channel_config: ChannelConfig, new_permissions: Dict[str, bool]) -> Dict[str, Any]:
    """
    Validate a permission update for a channel configuration
    
    Args:
        channel_config: ChannelConfig instance
        new_permissions: New permissions to validate
    
    Returns:
        Dict containing validation result
    """
    try:
        current_permissions = channel_config.get_permissions_dict()
        
        # Compare permissions
        comparison = compare_permissions(current_permissions, new_permissions)
        
        # Check if new permissions meet requirements
        requirement_check = check_required_permissions(new_permissions)
        
        # Determine if update is valid
        is_valid = requirement_check['has_required_permissions']
        
        result = {
            'valid': is_valid,
            'comparison': comparison,
            'requirement_check': requirement_check
        }
        
        if not is_valid:
            result['error'] = f"Missing required permissions: {', '.join(requirement_check['missing_permissions'])}"
        
        if comparison['critical_loss']:
            result['warning'] = f"Critical permissions lost: {', '.join(comparison['lost_required_permissions'])}"
        
        return result
    
    except Exception as e:
        logger.error(f"Error validating permission update: {str(e)}")
        return {
            'valid': False,
            'error': f'Validation error: {str(e)}'
        }

def get_channel_permission_status(channel_config: ChannelConfig) -> Dict[str, Any]:
    """
    Get comprehensive permission status for a channel
    
    Args:
        channel_config: ChannelConfig instance
    
    Returns:
        Dict containing permission status
    """
    try:
        current_permissions = channel_config.get_permissions_dict()
        requirement_check = check_required_permissions(current_permissions)
        requirements = get_permission_requirements()
        
        # Calculate permission score
        total_possible = len(requirements['required_permissions']) + len(requirements['optional_permissions'])
        current_count = sum(1 for perm in current_permissions.values() if perm)
        permission_score = (current_count / total_possible) * 100 if total_possible > 0 else 0
        
        return {
            'channel_id': channel_config.channel_id,
            'channel_username': channel_config.channel_username,
            'channel_title': channel_config.channel_title,
            'is_validated': channel_config.is_validated,
            'last_validation': channel_config.last_validation_at.isoformat() if channel_config.last_validation_at else None,
            'permissions': current_permissions,
            'requirement_check': requirement_check,
            'permission_score': round(permission_score, 1),
            'requirements': requirements,
            'validation_error': channel_config.validation_error
        }
    
    except Exception as e:
        logger.error(f"Error getting channel permission status: {str(e)}")
        return {
            'error': f'Status error: {str(e)}'
        }

def format_permissions_for_display(permissions: Dict[str, bool]) -> List[Dict[str, Any]]:
    """
    Format permissions for user-friendly display
    
    Args:
        permissions: Dict of permission names to boolean values
    
    Returns:
        List of formatted permission info
    """
    permission_labels = {
        'can_post_messages': 'Post Messages',
        'can_edit_messages': 'Edit Messages',
        'can_send_media_messages': 'Send Media',
        'can_delete_messages': 'Delete Messages',
        'can_pin_messages': 'Pin Messages'
    }
    
    formatted_permissions = []
    
    for perm, value in permissions.items():
        formatted_permissions.append({
            'permission': perm,
            'label': permission_labels.get(perm, perm.replace('_', ' ').title()),
            'enabled': value,
            'required': perm in Config.REQUIRED_PERMISSIONS,
            'status': 'granted' if value else 'denied'
        })
    
    # Sort by required first, then alphabetically
    formatted_permissions.sort(key=lambda x: (not x['required'], x['label']))
    
    return formatted_permissions

