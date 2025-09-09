import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Callable
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from models import ChannelConfig, db
from services import ChannelValidatorService
from config.settings import Config

logger = logging.getLogger(__name__)

class PeriodicValidationTask:
    """
    Handles periodic validation of all channel configurations
    """
    
    def __init__(self, get_credentials_func: Callable[[int], Dict[str, Any]]):
        """
        Initialize the periodic validation task
        
        Args:
            get_credentials_func: Function to get bot credentials for an account
        """
        self.scheduler = BackgroundScheduler()
        self.validator_service = ChannelValidatorService()
        self.get_credentials_func = get_credentials_func
        self.validation_interval = Config.PERIODIC_VALIDATION_INTERVAL
        self.is_running = False
    
    def start_scheduler(self):
        """Start the periodic validation scheduler"""
        try:
            if not self.is_running:
                # Add the periodic validation job
                self.scheduler.add_job(
                    func=self.run_periodic_validation,
                    trigger=IntervalTrigger(seconds=self.validation_interval),
                    id='periodic_channel_validation',
                    name='Periodic Channel Validation',
                    replace_existing=True,
                    max_instances=1  # Prevent overlapping executions
                )
                
                # Add cleanup job (runs daily)
                self.scheduler.add_job(
                    func=self.cleanup_old_validation_history,
                    trigger=IntervalTrigger(hours=24),
                    id='validation_history_cleanup',
                    name='Validation History Cleanup',
                    replace_existing=True,
                    max_instances=1
                )
                
                self.scheduler.start()
                self.is_running = True
                logger.info(f"Periodic validation scheduler started with {self.validation_interval}s interval")
            else:
                logger.warning("Scheduler is already running")
        
        except Exception as e:
            logger.error(f"Error starting periodic validation scheduler: {str(e)}")
    
    def stop_scheduler(self):
        """Stop the periodic validation scheduler"""
        try:
            if self.is_running:
                self.scheduler.shutdown(wait=False)
                self.is_running = False
                logger.info("Periodic validation scheduler stopped")
            else:
                logger.warning("Scheduler is not running")
        
        except Exception as e:
            logger.error(f"Error stopping periodic validation scheduler: {str(e)}")
    
    def run_periodic_validation(self):
        """
        Run periodic validation for all channels
        This method is called by the scheduler
        """
        try:
            logger.info("Starting periodic channel validation")
            start_time = datetime.utcnow()
            
            # Get channels that need validation (older than 1 hour)
            channels_to_validate = self.validator_service.get_channels_needing_validation(max_age_hours=1)
            
            if not channels_to_validate:
                logger.info("No channels need validation at this time")
                return
            
            logger.info(f"Validating {len(channels_to_validate)} channels")
            
            # Run validation for all channels
            validation_results = self.validator_service.validate_multiple_channels(
                channel_configs=channels_to_validate,
                get_credentials_func=self.get_credentials_func
            )
            
            # Log results
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()
            
            logger.info(f"Periodic validation completed in {duration:.2f}s")
            logger.info(f"Results: {validation_results['successful_validations']} successful, {validation_results['failed_validations']} failed")
            
            # Log any failures
            for result in validation_results['validation_results']:
                if not result['validation_result']['valid']:
                    logger.warning(f"Validation failed for {result['channel_username']}: {result['validation_result'].get('error')}")
        
        except Exception as e:
            logger.error(f"Error in periodic validation: {str(e)}")
    
    def cleanup_old_validation_history(self):
        """
        Clean up old validation history records
        This method is called by the scheduler daily
        """
        try:
            logger.info("Starting validation history cleanup")
            
            cleanup_result = self.validator_service.cleanup_old_validation_history(days_to_keep=30)
            
            if cleanup_result['success']:
                logger.info(f"Cleaned up {cleanup_result['deleted_records']} old validation records")
            else:
                logger.error(f"Validation history cleanup failed: {cleanup_result['error']}")
        
        except Exception as e:
            logger.error(f"Error in validation history cleanup: {str(e)}")
    
    def run_immediate_validation(self, account_id: int = None) -> Dict[str, Any]:
        """
        Run immediate validation for a specific account or all accounts
        
        Args:
            account_id: Optional account ID to validate, if None validates all
        
        Returns:
            Dict containing validation results
        """
        try:
            logger.info(f"Starting immediate validation for account {account_id if account_id else 'all'}")
            
            # Get channels to validate
            if account_id:
                channels_to_validate = ChannelConfig.query.filter_by(account_id=account_id).all()
            else:
                channels_to_validate = ChannelConfig.query.all()
            
            if not channels_to_validate:
                return {
                    'success': True,
                    'message': 'No channels found to validate',
                    'validation_results': {
                        'total_channels': 0,
                        'successful_validations': 0,
                        'failed_validations': 0
                    }
                }
            
            # Run validation
            validation_results = self.validator_service.validate_multiple_channels(
                channel_configs=channels_to_validate,
                get_credentials_func=self.get_credentials_func
            )
            
            logger.info(f"Immediate validation completed: {validation_results['successful_validations']} successful, {validation_results['failed_validations']} failed")
            
            return {
                'success': True,
                'validation_results': validation_results
            }
        
        except Exception as e:
            logger.error(f"Error in immediate validation: {str(e)}")
            return {
                'success': False,
                'error': f'Immediate validation error: {str(e)}'
            }
    
    def get_scheduler_status(self) -> Dict[str, Any]:
        """
        Get the current status of the scheduler
        
        Returns:
            Dict containing scheduler status
        """
        try:
            jobs = []
            if self.is_running:
                for job in self.scheduler.get_jobs():
                    jobs.append({
                        'id': job.id,
                        'name': job.name,
                        'next_run': job.next_run_time.isoformat() if job.next_run_time else None,
                        'trigger': str(job.trigger)
                    })
            
            return {
                'is_running': self.is_running,
                'validation_interval': self.validation_interval,
                'jobs': jobs,
                'scheduler_state': self.scheduler.state if hasattr(self.scheduler, 'state') else 'unknown'
            }
        
        except Exception as e:
            logger.error(f"Error getting scheduler status: {str(e)}")
            return {
                'is_running': self.is_running,
                'error': f'Status error: {str(e)}'
            }
    
    def update_validation_interval(self, new_interval: int):
        """
        Update the validation interval
        
        Args:
            new_interval: New interval in seconds
        """
        try:
            self.validation_interval = new_interval
            
            if self.is_running:
                # Remove existing job
                self.scheduler.remove_job('periodic_channel_validation')
                
                # Add job with new interval
                self.scheduler.add_job(
                    func=self.run_periodic_validation,
                    trigger=IntervalTrigger(seconds=new_interval),
                    id='periodic_channel_validation',
                    name='Periodic Channel Validation',
                    replace_existing=True,
                    max_instances=1
                )
                
                logger.info(f"Updated validation interval to {new_interval}s")
        
        except Exception as e:
            logger.error(f"Error updating validation interval: {str(e)}")

# Global instance for the application
periodic_validator = None

def initialize_periodic_validation(get_credentials_func: Callable[[int], Dict[str, Any]]):
    """
    Initialize the global periodic validation instance
    
    Args:
        get_credentials_func: Function to get bot credentials
    """
    global periodic_validator
    if periodic_validator is None:
        periodic_validator = PeriodicValidationTask(get_credentials_func)
        logger.info("Periodic validation task initialized")

def start_periodic_validation():
    """Start the periodic validation scheduler"""
    global periodic_validator
    if periodic_validator:
        periodic_validator.start_scheduler()
    else:
        logger.error("Periodic validator not initialized")

def stop_periodic_validation():
    """Stop the periodic validation scheduler"""
    global periodic_validator
    if periodic_validator:
        periodic_validator.stop_scheduler()

def get_periodic_validation_status() -> Dict[str, Any]:
    """Get the status of periodic validation"""
    global periodic_validator
    if periodic_validator:
        return periodic_validator.get_scheduler_status()
    else:
        return {
            'is_running': False,
            'error': 'Periodic validator not initialized'
        }

