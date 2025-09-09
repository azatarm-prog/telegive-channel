import logging
from typing import Dict, Any, List, Optional
from models import ChannelConfig
from utils import (
    check_required_permissions,
    get_permission_requirements,
    compare_permissions,
    validate_permission_update,
    format_permissions_for_display
)
from config.settings import Config

logger = logging.getLogger(__name__)

class PermissionCheckerService:
    """
    Service for checking and managing channel permissions
    """
    
    def __init__(self):
        self.required_permissions = Config.REQUIRED_PERMISSIONS
    
    def check_channel_permissions(self, channel_config: ChannelConfig) -> Dict[str, Any]:
        """
        Check permissions for a channel configuration
        
        Args:
            channel_config: ChannelConfig instance
        
        Returns:
            Dict containing permission check result
        """
        try:
            current_permissions = channel_config.get_permissions_dict()
            
            # Check required permissions
            requirement_check = check_required_permissions(current_permissions)
            
            # Get permission requirements info
            requirements = get_permission_requirements()
            
            # Format permissions for display
            formatted_permissions = format_permissions_for_display(current_permissions)
            
            return {
                'success': True,
                'channel_info': {
                    'id': channel_config.channel_id,
                    'username': channel_config.channel_username,
                    'title': channel_config.channel_title
                },
                'permissions': current_permissions,
                'requirement_check': requirement_check,
                'requirements': requirements,
                'formatted_permissions': formatted_permissions,
                'is_validated': channel_config.is_validated,
                'last_validation': channel_config.last_validation_at.isoformat() if channel_config.last_validation_at else None
            }
        
        except Exception as e:
            logger.error(f"Error checking channel permissions: {str(e)}")
            return {
                'success': False,
                'error': f'Permission check error: {str(e)}'
            }
    
    def validate_permission_changes(self, channel_config: ChannelConfig, new_permissions: Dict[str, bool]) -> Dict[str, Any]:
        """
        Validate proposed permission changes
        
        Args:
            channel_config: ChannelConfig instance
            new_permissions: Proposed new permissions
        
        Returns:
            Dict containing validation result
        """
        try:
            # Validate the permission update
            validation_result = validate_permission_update(channel_config, new_permissions)
            
            if validation_result['valid']:
                logger.info(f"Permission update validation successful for channel {channel_config.channel_username}")
            else:
                logger.warning(f"Permission update validation failed for channel {channel_config.channel_username}: {validation_result.get('error')}")
            
            return validation_result
        
        except Exception as e:
            logger.error(f"Error validating permission changes: {str(e)}")
            return {
                'valid': False,
                'error': f'Permission validation error: {str(e)}'
            }
    
    def get_permission_summary(self, channel_configs: List[ChannelConfig]) -> Dict[str, Any]:
        """
        Get permission summary for multiple channels
        
        Args:
            channel_configs: List of ChannelConfig instances
        
        Returns:
            Dict containing permission summary
        """
        try:
            summary = {
                'total_channels': len(channel_configs),
                'channels_with_all_required': 0,
                'channels_missing_required': 0,
                'permission_statistics': {},
                'common_issues': []
            }
            
            # Initialize permission statistics
            all_permissions = [
                'can_post_messages',
                'can_edit_messages', 
                'can_send_media_messages',
                'can_delete_messages',
                'can_pin_messages'
            ]
            
            for perm in all_permissions:
                summary['permission_statistics'][perm] = {
                    'granted': 0,
                    'denied': 0,
                    'percentage': 0
                }
            
            missing_required_channels = []
            
            # Analyze each channel
            for channel_config in channel_configs:
                permissions = channel_config.get_permissions_dict()
                requirement_check = check_required_permissions(permissions)
                
                if requirement_check['has_required_permissions']:
                    summary['channels_with_all_required'] += 1
                else:
                    summary['channels_missing_required'] += 1
                    missing_required_channels.append({
                        'channel_username': channel_config.channel_username,
                        'missing_permissions': requirement_check['missing_permissions']
                    })
                
                # Update permission statistics
                for perm in all_permissions:
                    if permissions.get(perm, False):
                        summary['permission_statistics'][perm]['granted'] += 1
                    else:
                        summary['permission_statistics'][perm]['denied'] += 1
            
            # Calculate percentages
            if summary['total_channels'] > 0:
                for perm in all_permissions:
                    granted = summary['permission_statistics'][perm]['granted']
                    summary['permission_statistics'][perm]['percentage'] = (granted / summary['total_channels']) * 100
            
            # Identify common issues
            if missing_required_channels:
                summary['channels_missing_required_details'] = missing_required_channels
                
                # Find most common missing permissions
                missing_perm_count = {}
                for channel in missing_required_channels:
                    for perm in channel['missing_permissions']:
                        missing_perm_count[perm] = missing_perm_count.get(perm, 0) + 1
                
                summary['common_missing_permissions'] = sorted(
                    missing_perm_count.items(),
                    key=lambda x: x[1],
                    reverse=True
                )
            
            return summary
        
        except Exception as e:
            logger.error(f"Error getting permission summary: {str(e)}")
            return {
                'error': f'Permission summary error: {str(e)}'
            }
    
    def get_permission_recommendations(self, channel_config: ChannelConfig) -> Dict[str, Any]:
        """
        Get permission recommendations for a channel
        
        Args:
            channel_config: ChannelConfig instance
        
        Returns:
            Dict containing permission recommendations
        """
        try:
            current_permissions = channel_config.get_permissions_dict()
            requirement_check = check_required_permissions(current_permissions)
            
            recommendations = {
                'channel_info': {
                    'username': channel_config.channel_username,
                    'title': channel_config.channel_title
                },
                'current_status': 'compliant' if requirement_check['has_required_permissions'] else 'non_compliant',
                'required_actions': [],
                'optional_improvements': [],
                'risk_assessment': 'low'
            }
            
            # Required actions
            if requirement_check['missing_permissions']:
                for perm in requirement_check['missing_permissions']:
                    recommendations['required_actions'].append({
                        'permission': perm,
                        'action': f'Grant {perm.replace("_", " ")} permission to the bot',
                        'priority': 'high',
                        'impact': 'Bot cannot function properly without this permission'
                    })
                recommendations['risk_assessment'] = 'high'
            
            # Optional improvements
            optional_perms = ['can_delete_messages', 'can_pin_messages']
            for perm in optional_perms:
                if not current_permissions.get(perm, False):
                    recommendations['optional_improvements'].append({
                        'permission': perm,
                        'action': f'Consider granting {perm.replace("_", " ")} permission',
                        'priority': 'low',
                        'benefit': f'Enables additional functionality: {perm.replace("_", " ")}'
                    })
            
            # Overall assessment
            if not requirement_check['has_required_permissions']:
                recommendations['overall_assessment'] = 'Channel permissions need immediate attention. Bot cannot function properly.'
            elif len(recommendations['optional_improvements']) > 0:
                recommendations['overall_assessment'] = 'Channel meets minimum requirements but could benefit from additional permissions.'
            else:
                recommendations['overall_assessment'] = 'Channel permissions are optimal for bot functionality.'
            
            return recommendations
        
        except Exception as e:
            logger.error(f"Error getting permission recommendations: {str(e)}")
            return {
                'error': f'Recommendation error: {str(e)}'
            }
    
    def audit_permissions(self, channel_configs: List[ChannelConfig]) -> Dict[str, Any]:
        """
        Perform a comprehensive permission audit
        
        Args:
            channel_configs: List of ChannelConfig instances
        
        Returns:
            Dict containing audit results
        """
        try:
            audit_results = {
                'audit_timestamp': logger.info(f"Starting permission audit for {len(channel_configs)} channels"),
                'total_channels': len(channel_configs),
                'compliant_channels': 0,
                'non_compliant_channels': 0,
                'channel_details': [],
                'summary': {},
                'recommendations': []
            }
            
            for channel_config in channel_configs:
                # Check permissions for this channel
                permission_check = self.check_channel_permissions(channel_config)
                
                if permission_check['success']:
                    requirement_check = permission_check['requirement_check']
                    
                    channel_detail = {
                        'account_id': channel_config.account_id,
                        'channel_username': channel_config.channel_username,
                        'channel_title': channel_config.channel_title,
                        'compliant': requirement_check['has_required_permissions'],
                        'missing_permissions': requirement_check['missing_permissions'],
                        'is_validated': channel_config.is_validated,
                        'last_validation': channel_config.last_validation_at.isoformat() if channel_config.last_validation_at else None
                    }
                    
                    audit_results['channel_details'].append(channel_detail)
                    
                    if requirement_check['has_required_permissions']:
                        audit_results['compliant_channels'] += 1
                    else:
                        audit_results['non_compliant_channels'] += 1
            
            # Generate summary and recommendations
            audit_results['summary'] = self.get_permission_summary(channel_configs)
            
            if audit_results['non_compliant_channels'] > 0:
                audit_results['recommendations'].append({
                    'priority': 'high',
                    'action': f'Fix permissions for {audit_results["non_compliant_channels"]} non-compliant channels',
                    'impact': 'Critical for bot functionality'
                })
            
            logger.info(f"Permission audit completed: {audit_results['compliant_channels']} compliant, {audit_results['non_compliant_channels']} non-compliant")
            
            return audit_results
        
        except Exception as e:
            logger.error(f"Error performing permission audit: {str(e)}")
            return {
                'error': f'Audit error: {str(e)}'
            }

