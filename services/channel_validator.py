import logging
from typing import Dict, Any, List
from datetime import datetime, timedelta
from models import ChannelConfig, ChannelValidationHistory, db
from utils import validate_channel_permissions, get_bot_info
from config.settings import Config

logger = logging.getLogger(__name__)

class ChannelValidatorService:
    """
    Service for validating channel configurations and permissions
    """
    
    def __init__(self):
        self.validation_timeout = Config.VALIDATION_TIMEOUT
    
    def validate_single_channel(self, channel_config: ChannelConfig, bot_token: str, bot_id: int) -> Dict[str, Any]:
        """
        Validate a single channel configuration
        
        Args:
            channel_config: ChannelConfig instance
            bot_token: Bot token for API calls
            bot_id: Bot user ID
        
        Returns:
            Dict containing validation result
        """
        try:
            logger.info(f"Validating channel {channel_config.channel_username} for account {channel_config.account_id}")
            
            # Perform validation
            result = validate_channel_permissions(channel_config, bot_token, bot_id)
            
            # Log result
            if result['valid']:
                logger.info(f"Channel {channel_config.channel_username} validation successful")
            else:
                logger.warning(f"Channel {channel_config.channel_username} validation failed: {result.get('error')}")
            
            return result
        
        except Exception as e:
            logger.error(f"Error validating channel {channel_config.channel_username}: {str(e)}")
            return {
                'valid': False,
                'error': f'Validation service error: {str(e)}'
            }
    
    def validate_multiple_channels(self, channel_configs: List[ChannelConfig], get_credentials_func) -> Dict[str, Any]:
        """
        Validate multiple channel configurations
        
        Args:
            channel_configs: List of ChannelConfig instances
            get_credentials_func: Function to get bot credentials for an account
        
        Returns:
            Dict containing validation results
        """
        results = {
            'total_channels': len(channel_configs),
            'successful_validations': 0,
            'failed_validations': 0,
            'validation_results': []
        }
        
        for channel_config in channel_configs:
            try:
                # Get credentials for this account
                credentials = get_credentials_func(channel_config.account_id)
                bot_token = credentials['bot_token']
                bot_id = credentials['bot_id']
                
                # Validate channel
                validation_result = self.validate_single_channel(channel_config, bot_token, bot_id)
                
                result_entry = {
                    'account_id': channel_config.account_id,
                    'channel_username': channel_config.channel_username,
                    'validation_result': validation_result
                }
                
                results['validation_results'].append(result_entry)
                
                if validation_result['valid']:
                    results['successful_validations'] += 1
                else:
                    results['failed_validations'] += 1
            
            except Exception as e:
                logger.error(f"Error validating channel {channel_config.channel_username}: {str(e)}")
                
                result_entry = {
                    'account_id': channel_config.account_id,
                    'channel_username': channel_config.channel_username,
                    'validation_result': {
                        'valid': False,
                        'error': f'Service error: {str(e)}'
                    }
                }
                
                results['validation_results'].append(result_entry)
                results['failed_validations'] += 1
        
        return results
    
    def get_channels_needing_validation(self, max_age_hours: int = 24) -> List[ChannelConfig]:
        """
        Get channels that need validation based on age
        
        Args:
            max_age_hours: Maximum hours since last validation
        
        Returns:
            List of ChannelConfig instances needing validation
        """
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
            
            # Get channels that haven't been validated recently or never validated
            channels = ChannelConfig.query.filter(
                db.or_(
                    ChannelConfig.last_validation_at.is_(None),
                    ChannelConfig.last_validation_at < cutoff_time
                )
            ).all()
            
            logger.info(f"Found {len(channels)} channels needing validation")
            return channels
        
        except Exception as e:
            logger.error(f"Error getting channels needing validation: {str(e)}")
            return []
    
    def get_validation_statistics(self, days: int = 7) -> Dict[str, Any]:
        """
        Get validation statistics for the past N days
        
        Args:
            days: Number of days to look back
        
        Returns:
            Dict containing validation statistics
        """
        try:
            cutoff_time = datetime.utcnow() - timedelta(days=days)
            
            # Get validation history
            validations = ChannelValidationHistory.query.filter(
                ChannelValidationHistory.validated_at >= cutoff_time
            ).all()
            
            stats = {
                'total_validations': len(validations),
                'successful_validations': 0,
                'failed_validations': 0,
                'validation_types': {},
                'error_summary': {}
            }
            
            for validation in validations:
                if validation.validation_result:
                    stats['successful_validations'] += 1
                else:
                    stats['failed_validations'] += 1
                
                # Count validation types
                val_type = validation.validation_type
                stats['validation_types'][val_type] = stats['validation_types'].get(val_type, 0) + 1
                
                # Count errors
                if validation.error_message:
                    error_key = validation.error_message[:50] + '...' if len(validation.error_message) > 50 else validation.error_message
                    stats['error_summary'][error_key] = stats['error_summary'].get(error_key, 0) + 1
            
            # Calculate success rate
            if stats['total_validations'] > 0:
                stats['success_rate'] = (stats['successful_validations'] / stats['total_validations']) * 100
            else:
                stats['success_rate'] = 0
            
            return stats
        
        except Exception as e:
            logger.error(f"Error getting validation statistics: {str(e)}")
            return {
                'error': f'Statistics error: {str(e)}'
            }
    
    def cleanup_old_validation_history(self, days_to_keep: int = 30) -> Dict[str, Any]:
        """
        Clean up old validation history records
        
        Args:
            days_to_keep: Number of days of history to keep
        
        Returns:
            Dict containing cleanup result
        """
        try:
            cutoff_time = datetime.utcnow() - timedelta(days=days_to_keep)
            
            # Count records to be deleted
            old_records = ChannelValidationHistory.query.filter(
                ChannelValidationHistory.validated_at < cutoff_time
            )
            
            count_to_delete = old_records.count()
            
            # Delete old records
            old_records.delete()
            db.session.commit()
            
            logger.info(f"Cleaned up {count_to_delete} old validation history records")
            
            return {
                'success': True,
                'deleted_records': count_to_delete,
                'cutoff_date': cutoff_time.isoformat()
            }
        
        except Exception as e:
            logger.error(f"Error cleaning up validation history: {str(e)}")
            db.session.rollback()
            return {
                'success': False,
                'error': f'Cleanup error: {str(e)}'
            }

