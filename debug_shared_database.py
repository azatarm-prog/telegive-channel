#!/usr/bin/env python3
"""
Debug script for shared database investigation
Since all services use the same database, let's find out what's in the accounts table
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

def debug_shared_database():
    """Debug the shared database to understand the account structure"""
    
    print("🔍 Debugging Shared Database - Account Investigation")
    print("=" * 60)
    
    # Create Flask app context for database access
    app = Flask(__name__)
    
    # Load configuration
    from config.settings import config
    app.config.from_object(config['production'])  # Use production config
    
    # Initialize database
    from models import db
    db.init_app(app)
    
    with app.app_context():
        try:
            print("\n1. Testing database connection...")
            result = db.session.execute(db.text("SELECT 1 as test"))
            row = result.fetchone()
            if row and row[0] == 1:
                print("   ✅ Database connection successful")
            else:
                print("   ❌ Database connection failed")
                return False
            
            print("\n2. Checking accounts table structure...")
            result = db.session.execute(db.text("""
                SELECT column_name, data_type, is_nullable 
                FROM information_schema.columns 
                WHERE table_name = 'accounts' 
                ORDER BY ordinal_position
            """))
            
            columns = result.fetchall()
            if columns:
                print("   ✅ Accounts table structure:")
                for col in columns:
                    print(f"      {col[0]} ({col[1]}) - {'NULL' if col[2] == 'YES' else 'NOT NULL'}")
            else:
                print("   ❌ Accounts table not found or no columns")
                return False
            
            print("\n3. Checking all accounts in database...")
            result = db.session.execute(db.text("SELECT COUNT(*) FROM accounts"))
            count = result.fetchone()[0]
            print(f"   Total accounts in database: {count}")
            
            if count > 0:
                print("\n4. Showing first 5 accounts...")
                result = db.session.execute(db.text("""
                    SELECT id, bot_id, bot_username, bot_name, is_active, created_at 
                    FROM accounts 
                    ORDER BY created_at DESC 
                    LIMIT 5
                """))
                
                accounts = result.fetchall()
                for account in accounts:
                    print(f"      ID: {account[0]}, Bot ID: {account[1]}, Username: {account[2]}, Name: {account[3]}, Active: {account[4]}")
            
            print(f"\n5. Searching for bot_id 262662172...")
            result = db.session.execute(db.text("""
                SELECT id, bot_id, bot_username, bot_name, bot_token, is_active, created_at 
                FROM accounts 
                WHERE bot_id = :bot_id
            """), {"bot_id": 262662172})
            
            account = result.fetchone()
            if account:
                print(f"   ✅ Found account:")
                print(f"      Database ID: {account[0]}")
                print(f"      Bot ID: {account[1]}")
                print(f"      Username: {account[2]}")
                print(f"      Name: {account[3]}")
                print(f"      Has Token: {'Yes' if account[4] else 'No'}")
                print(f"      Active: {account[5]}")
                print(f"      Created: {account[6]}")
                return True
            else:
                print(f"   ❌ Account with bot_id 262662172 NOT FOUND")
                
                # Check if there are any accounts with similar bot_id
                print(f"\n6. Searching for similar bot_ids...")
                result = db.session.execute(db.text("""
                    SELECT bot_id, bot_username, bot_name 
                    FROM accounts 
                    WHERE CAST(bot_id AS TEXT) LIKE '%262662172%' 
                    OR bot_username LIKE '%prohelpBot%'
                    OR bot_name LIKE '%helper%'
                """))
                
                similar = result.fetchall()
                if similar:
                    print(f"   Found similar accounts:")
                    for acc in similar:
                        print(f"      Bot ID: {acc[0]}, Username: {acc[1]}, Name: {acc[2]}")
                else:
                    print(f"   No similar accounts found")
                
                return False
                
        except Exception as e:
            print(f"\n❌ Database error: {str(e)}")
            return False

def create_missing_account():
    """Create the missing account record for bot_id 262662172"""
    
    print(f"\n🔧 Creating Missing Account Record")
    print("=" * 40)
    
    # Create Flask app context
    app = Flask(__name__)
    from config.settings import config
    app.config.from_object(config['production'])
    
    from models import db
    db.init_app(app)
    
    with app.app_context():
        try:
            # Insert the missing account
            result = db.session.execute(db.text("""
                INSERT INTO accounts (
                    bot_id,
                    bot_username,
                    bot_name,
                    bot_token,
                    is_active,
                    created_at,
                    updated_at
                ) VALUES (
                    :bot_id,
                    :bot_username,
                    :bot_name,
                    :bot_token,
                    :is_active,
                    NOW(),
                    NOW()
                )
                RETURNING id, bot_id, bot_username
            """), {
                "bot_id": 262662172,
                "bot_username": "prohelpBot",
                "bot_name": "helper",
                "bot_token": "262662172:AAGyAYVzuFFe23GagWY-FnP2NlAQRy_JsRk",
                "is_active": True
            })
            
            new_account = result.fetchone()
            db.session.commit()
            
            print(f"   ✅ Account created successfully:")
            print(f"      Database ID: {new_account[0]}")
            print(f"      Bot ID: {new_account[1]}")
            print(f"      Username: {new_account[2]}")
            
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"   ❌ Error creating account: {str(e)}")
            return False

def test_channel_service():
    """Test the Channel Service after account creation"""
    
    print(f"\n🧪 Testing Channel Service")
    print("=" * 30)
    
    import requests
    
    try:
        # Test account lookup
        response = requests.get(
            "https://telegive-channel-production.up.railway.app/api/accounts/262662172/channel",
            timeout=10
        )
        
        print(f"   API Response Status: {response.status_code}")
        data = response.json()
        print(f"   Response: {data}")
        
        if data.get('code') == 'CHANNEL_NOT_CONFIGURED':
            print(f"   ✅ SUCCESS: Account found, no channel configured (expected)")
            return True
        elif data.get('code') == 'ACCOUNT_NOT_FOUND':
            print(f"   ❌ FAILED: Account still not found")
            return False
        else:
            print(f"   ✅ SUCCESS: Account found with channel configuration")
            return True
            
    except Exception as e:
        print(f"   ❌ Error testing Channel Service: {str(e)}")
        return False

if __name__ == "__main__":
    print("🔍 Shared Database Investigation for bot_id 262662172")
    print("=" * 60)
    
    # Step 1: Debug the database
    account_exists = debug_shared_database()
    
    if not account_exists:
        print(f"\n🔧 Account missing - creating it now...")
        account_created = create_missing_account()
        
        if account_created:
            print(f"\n🧪 Testing Channel Service with new account...")
            test_channel_service()
        else:
            print(f"\n❌ Failed to create account")
    else:
        print(f"\n✅ Account exists - testing Channel Service...")
        test_channel_service()
    
    print(f"\n🎯 Investigation complete!")

