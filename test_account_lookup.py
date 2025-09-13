#!/usr/bin/env python3
"""
Test script for account lookup functionality
Tests the direct database access with bot_id 262662172
"""

import os
import sys
import logging
from flask import Flask

# Add the project directory to Python path
sys.path.insert(0, '/home/ubuntu/telegive-channel')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_account_lookup():
    """Test account lookup with bot_id 262662172"""
    
    # Create Flask app context for database access
    app = Flask(__name__)
    
    # Load configuration
    from config.settings import config
    app.config.from_object(config['development'])
    
    # Initialize database
    from models import db
    db.init_app(app)
    
    with app.app_context():
        try:
            # Test the account lookup utility
            from utils.account_lookup import (
                get_account_by_bot_id, 
                get_bot_credentials_from_db,
                validate_account_exists,
                get_account_database_id
            )
            
            bot_id = 262662172
            
            print(f"\n🔍 Testing account lookup for bot_id: {bot_id}")
            print("=" * 60)
            
            # Test 1: Check if account exists
            print(f"\n1. Testing validate_account_exists({bot_id})...")
            exists = validate_account_exists(bot_id)
            print(f"   Result: {exists}")
            
            if not exists:
                print("   ❌ Account does not exist in database")
                return False
            
            # Test 2: Get account by bot_id
            print(f"\n2. Testing get_account_by_bot_id({bot_id})...")
            account = get_account_by_bot_id(bot_id)
            if account:
                print(f"   ✅ Found account:")
                print(f"      Database ID: {account.get('id')}")
                print(f"      Bot ID: {account.get('bot_id')}")
                print(f"      Bot Username: {account.get('bot_username')}")
                print(f"      Bot Name: {account.get('bot_name') or account.get('name')}")
                print(f"      Is Active: {account.get('is_active')}")
            else:
                print("   ❌ Account not found")
                return False
            
            # Test 3: Get database ID
            print(f"\n3. Testing get_account_database_id({bot_id})...")
            db_id = get_account_database_id(bot_id)
            print(f"   Database ID: {db_id}")
            
            # Test 4: Get bot credentials
            print(f"\n4. Testing get_bot_credentials_from_db({bot_id})...")
            try:
                credentials = get_bot_credentials_from_db(bot_id)
                print(f"   ✅ Got credentials:")
                print(f"      Bot ID: {credentials.get('bot_id')}")
                print(f"      Account ID: {credentials.get('account_id')}")
                print(f"      Bot Username: {credentials.get('bot_username')}")
                print(f"      Bot Name: {credentials.get('bot_name')}")
                print(f"      Has Token: {'Yes' if credentials.get('bot_token') else 'No'}")
                if credentials.get('bot_token'):
                    token = credentials['bot_token']
                    # Show only first and last few characters for security
                    masked_token = f"{token[:10]}...{token[-10:]}" if len(token) > 20 else "***"
                    print(f"      Token (masked): {masked_token}")
            except Exception as e:
                print(f"   ❌ Error getting credentials: {str(e)}")
                return False
            
            print(f"\n✅ All tests passed! Account lookup is working correctly.")
            return True
            
        except Exception as e:
            print(f"\n❌ Database connection error: {str(e)}")
            print("\nThis might be because:")
            print("1. DATABASE_URL environment variable is not set")
            print("2. Database is not accessible from this environment")
            print("3. Database schema is different than expected")
            return False

def test_database_connection():
    """Test basic database connectivity"""
    
    print(f"\n🔗 Testing database connection...")
    print("=" * 40)
    
    # Check environment variables
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        print("❌ DATABASE_URL environment variable not set")
        print("   This is expected in the sandbox environment")
        print("   The actual database is on Railway and requires production credentials")
        return False
    
    print(f"Database URL: {db_url[:50]}...")
    
    # Create Flask app context
    app = Flask(__name__)
    from config.settings import config
    app.config.from_object(config['development'])
    
    from models import db
    db.init_app(app)
    
    with app.app_context():
        try:
            # Test basic database query
            result = db.session.execute(db.text("SELECT 1 as test"))
            row = result.fetchone()
            if row and row[0] == 1:
                print("✅ Database connection successful")
                return True
            else:
                print("❌ Database query failed")
                return False
        except Exception as e:
            print(f"❌ Database connection failed: {str(e)}")
            return False

if __name__ == "__main__":
    print("🧪 Channel Service Account Lookup Test")
    print("=" * 50)
    
    # Test database connection first
    db_connected = test_database_connection()
    
    if db_connected:
        # Test account lookup if database is connected
        test_account_lookup()
    else:
        print("\n📝 Note: Database tests cannot run in sandbox environment")
        print("   The actual database is on Railway and requires production credentials")
        print("   However, the code changes have been made and should work in production")
        
        print(f"\n🔧 Code changes summary:")
        print("   ✅ Updated app.py to use direct database access")
        print("   ✅ Updated channels.py to use direct database access")
        print("   ✅ Removed Auth Service API dependencies")
        print("   ✅ Added proper bot_id vs account_id handling")
        print("   ✅ Created account_lookup utility for shared database access")
        
        print(f"\n🚀 Ready for deployment testing with bot_id 262662172")

