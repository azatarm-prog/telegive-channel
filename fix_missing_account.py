#!/usr/bin/env python3
"""
Production Database Fix Script
Run this script in the production environment to create the missing account record
"""

import os
import sys
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_missing_account():
    """
    Create the missing account record for bot_id 262662172
    This script should be run in the production environment with database access
    """
    
    print("🔧 Production Database Fix - Creating Missing Account")
    print("=" * 60)
    
    try:
        import psycopg2
        from urllib.parse import urlparse
        
        # Get database URL from environment
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            print("❌ DATABASE_URL environment variable not found")
            print("   This script must be run in the production environment")
            return False
        
        print(f"✅ Found DATABASE_URL: {database_url[:50]}...")
        
        # Parse database URL
        url = urlparse(database_url)
        
        # Connect to database
        print("\n1. Connecting to database...")
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        print("   ✅ Database connection successful")
        
        # Check if account already exists
        print("\n2. Checking if account exists...")
        cursor.execute("""
            SELECT id, bot_id, bot_username, bot_name, is_active 
            FROM accounts 
            WHERE bot_id = %s
        """, (262662172,))
        
        existing_account = cursor.fetchone()
        
        if existing_account:
            print(f"   ✅ Account already exists:")
            print(f"      Database ID: {existing_account[0]}")
            print(f"      Bot ID: {existing_account[1]}")
            print(f"      Username: {existing_account[2]}")
            print(f"      Name: {existing_account[3]}")
            print(f"      Active: {existing_account[4]}")
            print(f"\n   No action needed - account exists!")
            return True
        
        print(f"   ❌ Account with bot_id 262662172 not found")
        
        # Show existing accounts for reference
        print("\n3. Showing existing accounts...")
        cursor.execute("""
            SELECT id, bot_id, bot_username, bot_name, is_active 
            FROM accounts 
            ORDER BY created_at DESC 
            LIMIT 5
        """)
        
        accounts = cursor.fetchall()
        if accounts:
            print(f"   Found {len(accounts)} recent accounts:")
            for acc in accounts:
                print(f"      ID: {acc[0]}, Bot ID: {acc[1]}, Username: {acc[2]}, Name: {acc[3]}, Active: {acc[4]}")
        else:
            print(f"   No accounts found in database")
        
        # Create the missing account
        print(f"\n4. Creating missing account...")
        cursor.execute("""
            INSERT INTO accounts (
                bot_id,
                bot_username,
                bot_name,
                bot_token,
                is_active,
                created_at,
                updated_at
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s
            )
            RETURNING id, bot_id, bot_username
        """, (
            262662172,
            'prohelpBot',
            'helper',
            '262662172:AAGyAYVzuFFe23GagWY-FnP2NlAQRy_JsRk',
            True,
            datetime.now(),
            datetime.now()
        ))
        
        new_account = cursor.fetchone()
        conn.commit()
        
        print(f"   ✅ Account created successfully:")
        print(f"      Database ID: {new_account[0]}")
        print(f"      Bot ID: {new_account[1]}")
        print(f"      Username: {new_account[2]}")
        
        # Verify the account was created
        print(f"\n5. Verifying account creation...")
        cursor.execute("""
            SELECT id, bot_id, bot_username, bot_name, is_active, created_at
            FROM accounts 
            WHERE bot_id = %s
        """, (262662172,))
        
        verified_account = cursor.fetchone()
        if verified_account:
            print(f"   ✅ Verification successful:")
            print(f"      Database ID: {verified_account[0]}")
            print(f"      Bot ID: {verified_account[1]}")
            print(f"      Username: {verified_account[2]}")
            print(f"      Name: {verified_account[3]}")
            print(f"      Active: {verified_account[4]}")
            print(f"      Created: {verified_account[5]}")
        else:
            print(f"   ❌ Verification failed - account not found after creation")
            return False
        
        cursor.close()
        conn.close()
        
        print(f"\n✅ Database fix completed successfully!")
        print(f"\n🧪 Next step: Test the Channel Service API")
        print(f"   curl https://telegive-channel-production.up.railway.app/api/accounts/262662172/channel")
        print(f"   Expected: 'CHANNEL_NOT_CONFIGURED' (not 'ACCOUNT_NOT_FOUND')")
        
        return True
        
    except ImportError:
        print("❌ psycopg2 not installed. Install with: pip install psycopg2-binary")
        return False
    except Exception as e:
        print(f"❌ Database error: {str(e)}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False

def test_channel_service_api():
    """Test the Channel Service API after database fix"""
    
    print(f"\n🧪 Testing Channel Service API")
    print("=" * 35)
    
    try:
        import requests
        
        # Test account lookup
        print(f"Testing: GET /api/accounts/262662172/channel")
        response = requests.get(
            "https://telegive-channel-production.up.railway.app/api/accounts/262662172/channel",
            timeout=10
        )
        
        print(f"Status Code: {response.status_code}")
        data = response.json()
        print(f"Response: {data}")
        
        if response.status_code == 404 and data.get('code') == 'CHANNEL_NOT_CONFIGURED':
            print(f"✅ SUCCESS: Account found, no channel configured (expected)")
            return True
        elif response.status_code == 404 and data.get('code') == 'ACCOUNT_NOT_FOUND':
            print(f"❌ FAILED: Account still not found - database fix didn't work")
            return False
        elif response.status_code == 200 and data.get('success'):
            print(f"✅ SUCCESS: Account found with existing channel configuration")
            return True
        else:
            print(f"❓ UNEXPECTED: {data}")
            return False
            
    except ImportError:
        print("❌ requests not installed. Install with: pip install requests")
        return False
    except Exception as e:
        print(f"❌ Error testing API: {str(e)}")
        return False

if __name__ == "__main__":
    print("🔧 Production Database Fix for bot_id 262662172")
    print("=" * 60)
    print("This script creates the missing account record in the shared database")
    print("Run this script in the production environment with DATABASE_URL access")
    print("=" * 60)
    
    # Fix the database
    success = fix_missing_account()
    
    if success:
        # Test the API
        print(f"\n" + "="*60)
        test_channel_service_api()
    
    print(f"\n🎯 Database fix script completed!")
    
    if success:
        print(f"\n✅ NEXT STEPS:")
        print(f"1. Test the Channel Service API manually")
        print(f"2. Test the frontend channel configuration")
        print(f"3. Verify end-to-end channel setup flow")
    else:
        print(f"\n❌ TROUBLESHOOTING:")
        print(f"1. Ensure this script runs in production environment")
        print(f"2. Verify DATABASE_URL environment variable is set")
        print(f"3. Check database connection and permissions")

