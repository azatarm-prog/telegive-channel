"""
Enhanced error handling utilities for Channel Management Service
"""
import logging
from datetime import datetime
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class ChannelServiceError(Exception):
    """Base exception for Channel Service errors"""
    def __init__(self, message: str, code: str, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(self.message)

class AccountNotFoundError(ChannelServiceError):
    """Raised when account is not found in auth service"""
    def __init__(self, account_id: int, details: Optional[Dict[str, Any]] = None):
        message = f"Account ID {account_id} not found in database. Please contact support or try logging in again."
        code = "ACCOUNT_NOT_FOUND"
        
        default_details = {
            "account_id": account_id,
            "suggestion": "This usually indicates an account synchronization issue. Please try logging out and logging back in.",
            "support_action": "If the problem persists, contact support with this account ID.",
            "timestamp": datetime.utcnow().isoformat() + 'Z'
        }
        
        if details:
            default_details.update(details)
            
        super().__init__(message, code, default_details)

class ChannelNotConfiguredError(ChannelServiceError):
    """Raised when channel is not configured for account"""
    def __init__(self, account_id: int, details: Optional[Dict[str, Any]] = None):
        message = f"No channel configuration found for account {account_id}"
        code = "CHANNEL_NOT_CONFIGURED"
        
        default_details = {
            "account_id": account_id,
            "suggestion": "Configure your channel first using the channel verification process.",
            "next_steps": [
                "Use the channel verification endpoint to validate your channel",
                "Save the channel configuration after successful verification"
            ],
            "timestamp": datetime.utcnow().isoformat() + 'Z'
        }
        
        if details:
            default_details.update(details)
            
        super().__init__(message, code, default_details)

class TelegramAPIError(ChannelServiceError):
    """Raised when Telegram API calls fail"""
    def __init__(self, message: str, telegram_error: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        code = "TELEGRAM_API_ERROR"
        
        default_details = {
            "telegram_error": telegram_error,
            "suggestion": "This is usually a temporary issue. Please try again in a few moments.",
            "troubleshooting": [
                "Verify your bot token is correct",
                "Check that your bot has the required permissions",
                "Ensure the channel username is correct"
            ],
            "timestamp": datetime.utcnow().isoformat() + 'Z'
        }
        
        if details:
            default_details.update(details)
            
        super().__init__(message, code, default_details)

class ChannelVerificationError(ChannelServiceError):
    """Raised when channel verification fails"""
    def __init__(self, channel_username: str, reason: str, details: Optional[Dict[str, Any]] = None):
        message = f"Channel verification failed for {channel_username}: {reason}"
        code = "CHANNEL_VERIFICATION_FAILED"
        
        default_details = {
            "channel_username": channel_username,
            "reason": reason,
            "troubleshooting": [
                "Verify the channel username is correct (should start with @)",
                "Ensure your bot is added to the channel as an administrator",
                "Check that the bot has 'Post Messages' and 'Edit Messages' permissions",
                "Make sure the channel is public or your bot has access"
            ],
            "timestamp": datetime.utcnow().isoformat() + 'Z'
        }
        
        if details:
            default_details.update(details)
            
        super().__init__(message, code, default_details)

def create_error_response(error: ChannelServiceError, status_code: int = 400) -> tuple:
    """
    Create a standardized error response
    
    Args:
        error: ChannelServiceError instance
        status_code: HTTP status code
        
    Returns:
        tuple: (response_dict, status_code)
    """
    response = {
        "success": False,
        "error": error.message,
        "code": error.code
    }
    
    if error.details:
        response["details"] = error.details
    
    # Log the error
    logger.error(f"Error {error.code}: {error.message}", extra={
        "error_code": error.code,
        "error_details": error.details,
        "status_code": status_code
    })
    
    return response, status_code

def create_success_response(data: Dict[str, Any], message: Optional[str] = None) -> Dict[str, Any]:
    """
    Create a standardized success response
    
    Args:
        data: Response data
        message: Optional success message
        
    Returns:
        dict: Standardized success response
    """
    response = {
        "success": True,
        **data
    }
    
    if message:
        response["message"] = message
    
    return response

def log_account_lookup(account_id: int, found: bool, duration_ms: Optional[float] = None):
    """
    Log account lookup attempts for monitoring
    
    Args:
        account_id: Account ID that was looked up
        found: Whether the account was found
        duration_ms: Lookup duration in milliseconds
    """
    log_data = {
        "account_id": account_id,
        "found": found,
        "timestamp": datetime.utcnow().isoformat() + 'Z'
    }
    
    if duration_ms is not None:
        log_data["duration_ms"] = duration_ms
    
    if found:
        logger.info(f"Account lookup successful for {account_id}", extra=log_data)
    else:
        logger.warning(f"Account lookup failed for {account_id}", extra=log_data)

def log_channel_operation(operation: str, account_id: int, channel_username: Optional[str] = None, 
                         success: bool = True, error: Optional[str] = None):
    """
    Log channel operations for monitoring
    
    Args:
        operation: Operation type (verify, save, delete, etc.)
        account_id: Account ID
        channel_username: Channel username (if applicable)
        success: Whether operation was successful
        error: Error message (if failed)
    """
    log_data = {
        "operation": operation,
        "account_id": account_id,
        "success": success,
        "timestamp": datetime.utcnow().isoformat() + 'Z'
    }
    
    if channel_username:
        log_data["channel_username"] = channel_username
    
    if error:
        log_data["error"] = error
    
    if success:
        logger.info(f"Channel operation {operation} successful for account {account_id}", extra=log_data)
    else:
        logger.error(f"Channel operation {operation} failed for account {account_id}: {error}", extra=log_data)

def get_troubleshooting_response(account_id: int) -> Dict[str, Any]:
    """
    Get troubleshooting information for account issues
    
    Args:
        account_id: Account ID having issues
        
    Returns:
        dict: Troubleshooting information
    """
    return {
        "troubleshooting": {
            "steps": [
                "Try logging out and logging back in",
                "Clear your browser cache and cookies",
                "Verify your bot token is correct in the dashboard",
                "Contact support if the problem persists"
            ],
            "support_info": {
                "account_id": account_id,
                "timestamp": datetime.utcnow().isoformat() + 'Z',
                "service": "channel-management",
                "version": "1.0.0"
            },
            "common_causes": [
                "Account synchronization delay between services",
                "Recent account creation not yet propagated",
                "Database connectivity issues",
                "Auth service temporary unavailability"
            ]
        }
    }

