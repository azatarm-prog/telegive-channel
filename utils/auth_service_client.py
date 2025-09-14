"""
Auth Service API client for Channel Service
Handles authentication and communication with Auth Service
"""

import os
import logging
import requests
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class AuthServiceClient:
    """Client for communicating with Auth Service API"""
    
    def __init__(self):
        self.base_url = os.getenv('AUTH_SERVICE_URL', 'https://web-production-ddd7e.up.railway.app')
        self.service_token = os.getenv('AUTH_SERVICE_SECRET', 'ch4nn3l_s3rv1c3_t0k3n_2025_s3cur3_r4nd0m_str1ng')
        self.headers = {
            'Content-Type': 'application/json',
            'X-Service-Token': self.service_token
        }
        
    def get_account_by_bot_id(self, bot_id: int) -> Optional[Dict]:
        """
        Get account information from Auth Service
        
        Args:
            bot_id (int): The Telegram bot ID
            
        Returns:
            dict: Account information or None if not found
        """
        try:
            logger.info(f"🔍 Getting account from Auth Service for bot_id: {bot_id}")
            
            url = f"{self.base_url}/api/accounts/{bot_id}"
            logger.info(f"📡 Auth Service URL: {url}")
            
            response = requests.get(url, headers=self.headers, timeout=10)
            logger.info(f"📡 Auth Service response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ Account found in Auth Service for bot_id: {bot_id}")
                return data
            elif response.status_code == 404:
                logger.warning(f"❌ Account not found in Auth Service for bot_id: {bot_id}")
                return None
            else:
                logger.error(f"❌ Auth Service error: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Auth Service request failed: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"❌ Unexpected error calling Auth Service: {str(e)}")
            return None
    
    def get_bot_credentials(self, bot_id: int) -> Optional[Dict]:
        """
        Get bot credentials from Auth Service
        
        Args:
            bot_id (int): The Telegram bot ID
            
        Returns:
            dict: Bot credentials with bot_token, or None if not found
        """
        try:
            logger.info(f"🔑 Getting bot credentials from Auth Service for bot_id: {bot_id}")
            
            account = self.get_account_by_bot_id(bot_id)
            
            if not account:
                logger.error(f"❌ No account found for bot_id: {bot_id}")
                return None
            
            # Extract bot token from account
            bot_token = account.get('bot_token')
            
            if not bot_token:
                logger.error(f"❌ No bot_token found in account for bot_id: {bot_id}")
                logger.info(f"📋 Available fields: {list(account.keys())}")
                return None
            
            logger.info(f"✅ Bot token retrieved successfully for bot_id: {bot_id}")
            logger.info(f"🔑 Token format: {'VALID' if ':' in str(bot_token) else 'INVALID'}")
            logger.info(f"🔑 Token length: {len(str(bot_token))}")
            
            return {
                'bot_token': bot_token,
                'bot_id': bot_id,
                'account_id': account.get('id'),
                'bot_username': account.get('bot_username'),
                'bot_name': account.get('bot_name')
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting bot credentials: {str(e)}")
            return None
    
    def validate_account_exists(self, bot_id: int) -> bool:
        """
        Validate that an account exists for the given bot_id
        
        Args:
            bot_id (int): The Telegram bot ID
            
        Returns:
            bool: True if account exists and is active
        """
        try:
            account = self.get_account_by_bot_id(bot_id)
            return account is not None and account.get('is_active', False)
        except Exception as e:
            logger.error(f"❌ Error validating account existence for bot_id {bot_id}: {str(e)}")
            return False

# Global client instance
auth_client = AuthServiceClient()

# Convenience functions for backward compatibility
def get_account_by_bot_id(bot_id: int) -> Optional[Dict]:
    """Get account by bot_id using Auth Service"""
    return auth_client.get_account_by_bot_id(bot_id)

def get_bot_credentials_from_auth_service(bot_id: int) -> Optional[Dict]:
    """Get bot credentials using Auth Service"""
    return auth_client.get_bot_credentials(bot_id)

def validate_account_exists(bot_id: int) -> bool:
    """Validate account exists using Auth Service"""
    return auth_client.validate_account_exists(bot_id)

