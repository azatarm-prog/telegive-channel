#!/usr/bin/env python3
"""
Debug script to test bot token retrieval from Channel Service
This will help identify if the issue is with token storage or retrieval
"""

import os
import sys
import logging
import requests
from datetime import datetime

# Add the project root to Python path
sys.path.insert(0, '/home/ubuntu/telegive-channel')

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_token_retrieval():
    """Test bot token retrieval from Channel Service database"""
    
    print("🔍 === TOKEN RETRIEVAL DEBUG TEST ===")
    print(f"📅 Test Time: {datetime.now()}")
    print(f"🎯 Testing bot_id: 262662172")
    print()
    
    try:
        # Import Channel Service modules
        from app import create_app
        from utils.account_lookup import get_account_by_bot_id, get_bot_credentials_from_db
        
        # Create Flask app context
        app = create_app()
        
        with app.app_context():
            print("1️⃣ Testing account lookup...")
            
            # Test account lookup
            account = get_account_by_bot_id(262662172)
            print(f"   Account found: {account is not None}")
            
            if account:
                print(f"   Database ID: {account.get('id')}")
                print(f"   Bot ID: {account.get('bot_id')}")
                print(f"   Bot username: {account.get('bot_username')}")
                
                # Check all token-related fields
                print("\n2️⃣ Checking token fields...")
                bot_token = account.get('bot_token')
                bot_token_encrypted = account.get('bot_token_encrypted')
                encrypted_token = account.get('encrypted_token')
                
                print(f"   bot_token field: {'FOUND' if bot_token else 'MISSING'}")
                print(f"   bot_token_encrypted field: {'FOUND' if bot_token_encrypted else 'MISSING'}")
                print(f"   encrypted_token field: {'FOUND' if encrypted_token else 'MISSING'}")
                
                if bot_token:
                    print(f"   bot_token length: {len(str(bot_token))}")
                    print(f"   bot_token format: {'VALID' if ':' in str(bot_token) else 'INVALID'}")
                    print(f"   bot_token starts with bot_id: {str(bot_token).startswith('262662172:')}")
                
                if bot_token_encrypted:
                    print(f"   bot_token_encrypted length: {len(str(bot_token_encrypted))}")
                
                # Test credentials retrieval
                print("\n3️⃣ Testing credentials retrieval...")
                try:
                    credentials = get_bot_credentials_from_db(262662172)
                    print(f"   Credentials retrieved: {credentials is not None}")
                    
                    if credentials:
                        retrieved_token = credentials.get('bot_token')
                        print(f"   Retrieved token: {'FOUND' if retrieved_token else 'MISSING'}")
                        
                        if retrieved_token:
                            print(f"   Retrieved token length: {len(str(retrieved_token))}")
                            print(f"   Retrieved token format: {'VALID' if ':' in str(retrieved_token) else 'INVALID'}")
                            print(f"   Retrieved token starts with bot_id: {str(retrieved_token).startswith('262662172:')}")
                            
                            # Test if this token works with Telegram API
                            print("\n4️⃣ Testing retrieved token with Telegram API...")
                            test_telegram_api(retrieved_token)
                        
                except Exception as e:
                    print(f"   ❌ Credentials retrieval failed: {str(e)}")
                
            else:
                print("   ❌ No account found for bot_id 262662172")
                
    except Exception as e:
        print(f"💥 CRITICAL ERROR: {str(e)}")
        import traceback
        traceback.print_exc()

def test_telegram_api(token):
    """Test if the retrieved token works with Telegram API"""
    
    if not token:
        print("   ❌ No token to test")
        return
    
    try:
        # Test getMe
        print("   🤖 Testing getMe with retrieved token...")
        response = requests.get(f'https://api.telegram.org/bot{token}/getMe', timeout=10)
        data = response.json()
        
        if data.get('ok'):
            print("   ✅ getMe SUCCESS - Token is valid")
            bot_info = data['result']
            print(f"      Bot ID: {bot_info['id']}")
            print(f"      Bot username: {bot_info.get('username')}")
            print(f"      Bot name: {bot_info.get('first_name')}")
            
            # Test channel access
            print("   📺 Testing channel access with retrieved token...")
            channel_response = requests.get(
                f'https://api.telegram.org/bot{token}/getChat',
                params={'chat_id': '@dxstest'},
                timeout=10
            )
            channel_data = channel_response.json()
            
            if channel_data.get('ok'):
                print("   ✅ Channel access SUCCESS")
                print(f"      Channel: {channel_data['result']['title']}")
            else:
                print(f"   ❌ Channel access FAILED: {channel_data}")
                
        else:
            print(f"   ❌ getMe FAILED: {data}")
            
    except Exception as e:
        print(f"   💥 Telegram API test error: {str(e)}")

def compare_with_known_working_token():
    """Compare with the known working token from manual tests"""
    
    print("\n🔬 === COMPARISON WITH KNOWN WORKING TOKEN ===")
    
    # Known working token from manual tests
    known_token = "262662172:AAGyAYVzuFFe23GagWY-FnP2NlAQRy_JsRk"
    
    print(f"Known working token: {known_token}")
    print(f"Known token length: {len(known_token)}")
    print(f"Known token format: {'VALID' if ':' in known_token else 'INVALID'}")
    
    # Test the known token (should work)
    print("\n🧪 Testing known working token...")
    test_telegram_api(known_token)

if __name__ == "__main__":
    print("🚀 Starting Channel Service Token Retrieval Debug")
    print("=" * 60)
    
    # Test token retrieval from Channel Service
    test_token_retrieval()
    
    # Compare with known working token
    compare_with_known_working_token()
    
    print("\n" + "=" * 60)
    print("🏁 Debug test completed")

