#!/usr/bin/env python3
"""
Direct database debug script to check bot token storage
This bypasses the Flask app to directly query the database
"""

import os
import sys
import logging
import requests
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_database_token():
    """Test bot token directly from database"""
    
    print("🔍 === DIRECT DATABASE TOKEN DEBUG ===")
    print(f"📅 Test Time: {datetime.now()}")
    print(f"🎯 Testing bot_id: 262662172")
    print()
    
    try:
        # Try to connect to database directly
        import psycopg2
        from urllib.parse import urlparse
        
        # Get DATABASE_URL from environment
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            print("❌ DATABASE_URL not found in environment")
            return
            
        print(f"🔗 Database URL found: {database_url[:50]}...")
        
        # Parse DATABASE_URL
        parsed = urlparse(database_url)
        
        # Connect to database
        conn = psycopg2.connect(
            host=parsed.hostname,
            port=parsed.port,
            database=parsed.path[1:],  # Remove leading slash
            user=parsed.username,
            password=parsed.password
        )
        
        cursor = conn.cursor()
        
        print("✅ Database connection successful")
        
        # Query account information
        print("\n1️⃣ Querying account information...")
        cursor.execute("""
            SELECT id, bot_id, bot_username, bot_name, bot_token, bot_token_encrypted, 
                   encrypted_token, is_active, created_at
            FROM accounts 
            WHERE bot_id = %s
        """, (262662172,))
        
        row = cursor.fetchone()
        
        if row:
            print("✅ Account found in database")
            
            # Get column names
            columns = [desc[0] for desc in cursor.description]
            account = dict(zip(columns, row))
            
            print(f"   Database ID: {account['id']}")
            print(f"   Bot ID: {account['bot_id']}")
            print(f"   Bot username: {account['bot_username']}")
            print(f"   Bot name: {account['bot_name']}")
            print(f"   Is active: {account['is_active']}")
            print(f"   Created: {account['created_at']}")
            
            # Check token fields
            print("\n2️⃣ Checking token fields...")
            
            bot_token = account['bot_token']
            bot_token_encrypted = account['bot_token_encrypted']
            encrypted_token = account.get('encrypted_token')
            
            print(f"   bot_token: {'FOUND' if bot_token else 'NULL/EMPTY'}")
            print(f"   bot_token_encrypted: {'FOUND' if bot_token_encrypted else 'NULL/EMPTY'}")
            print(f"   encrypted_token: {'FOUND' if encrypted_token else 'NULL/EMPTY'}")
            
            # Test each token field
            if bot_token:
                print(f"\n   📋 bot_token details:")
                print(f"      Value: {bot_token}")
                print(f"      Length: {len(str(bot_token))}")
                print(f"      Format: {'VALID' if ':' in str(bot_token) else 'INVALID'}")
                print(f"      Starts with bot_id: {str(bot_token).startswith('262662172:')}")
                test_token_with_telegram(bot_token, "bot_token")
            
            if bot_token_encrypted:
                print(f"\n   🔐 bot_token_encrypted details:")
                print(f"      Value: {bot_token_encrypted}")
                print(f"      Length: {len(str(bot_token_encrypted))}")
                print(f"      Format: {'VALID' if ':' in str(bot_token_encrypted) else 'ENCRYPTED/INVALID'}")
                if ':' in str(bot_token_encrypted):
                    test_token_with_telegram(bot_token_encrypted, "bot_token_encrypted")
                else:
                    print("      ⚠️  Appears to be encrypted - cannot test directly")
            
            if encrypted_token:
                print(f"\n   🔒 encrypted_token details:")
                print(f"      Value: {encrypted_token}")
                print(f"      Length: {len(str(encrypted_token))}")
                print(f"      Format: {'VALID' if ':' in str(encrypted_token) else 'ENCRYPTED/INVALID'}")
                if ':' in str(encrypted_token):
                    test_token_with_telegram(encrypted_token, "encrypted_token")
                else:
                    print("      ⚠️  Appears to be encrypted - cannot test directly")
            
        else:
            print("❌ No account found for bot_id 262662172")
        
        cursor.close()
        conn.close()
        
    except ImportError:
        print("❌ psycopg2 not available - cannot test database directly")
        print("   This is expected in sandbox environment")
        
    except Exception as e:
        print(f"💥 Database error: {str(e)}")

def test_token_with_telegram(token, field_name):
    """Test a token with Telegram API"""
    
    if not token or not isinstance(token, str):
        print(f"      ❌ Invalid token format for {field_name}")
        return
    
    try:
        print(f"      🧪 Testing {field_name} with Telegram API...")
        response = requests.get(f'https://api.telegram.org/bot{token}/getMe', timeout=5)
        data = response.json()
        
        if data.get('ok'):
            print(f"      ✅ {field_name} works with Telegram API")
            bot_info = data['result']
            print(f"         Bot ID: {bot_info['id']}")
            print(f"         Bot username: {bot_info.get('username')}")
        else:
            print(f"      ❌ {field_name} failed Telegram API test: {data}")
            
    except Exception as e:
        print(f"      💥 Error testing {field_name}: {str(e)}")

def compare_tokens():
    """Compare what we expect vs what might be stored"""
    
    print("\n🔬 === TOKEN COMPARISON ===")
    
    expected_token = "262662172:AAGyAYVzuFFe23GagWY-FnP2NlAQRy_JsRk"
    
    print(f"Expected working token: {expected_token}")
    print(f"Expected length: {len(expected_token)}")
    print(f"Expected format: bot_id:hash")
    
    print("\n🧪 Confirming expected token works...")
    test_token_with_telegram(expected_token, "expected_token")

if __name__ == "__main__":
    print("🚀 Starting Direct Database Token Debug")
    print("=" * 60)
    
    # Test database token storage
    test_database_token()
    
    # Compare with expected token
    compare_tokens()
    
    print("\n" + "=" * 60)
    print("🏁 Database debug completed")
    print("\n💡 If database connection fails, this means the Channel Service")
    print("   needs to be debugged in the production environment where")
    print("   DATABASE_URL is accessible.")

