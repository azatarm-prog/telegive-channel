#!/usr/bin/env python3
"""
Automatic Database Migration - Create Missing Account
This script runs automatically during Railway deployment
"""

import os
import sys
import logging
from datetime import datetime

# Add the project directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_migration():
    """
    Create the missing account record for bot_id 262662172
    This runs automatically during Railway deployment
    """
    
    print("🔄 Running Database Migration - Creating Missing Account")
    print("=" * 60)
    
    try:
        # Check if we're in production environment
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            print("⚠️  DATABASE_URL not found - skipping migration (development environment)")
            return True
        
        print(f"✅ Found DATABASE_URL - running migration in production")
        
        # Create Flask app context for database access
        from flask import Flask
        from config.settings import config
        from models import db
        
        app = Flask(__name__)
        app.config.from_object(config.get('production', config['default']))
        db.init_app(app)
        
        with app.app_context():
            # Check if account already exists
            print("\n1. Checking if account exists...")
            result = db.session.execute(db.text("""
                SELECT id, bot_id, bot_username, bot_name, is_active 
                FROM accounts 
                WHERE bot_id = :bot_id
            """), {"bot_id": 262662172})
            
            existing_account = result.fetchone()
            
            if existing_account:
                print(f"   ✅ Account already exists:")
                print(f"      Database ID: {existing_account[0]}")
                print(f"      Bot ID: {existing_account[1]}")
                print(f"      Username: {existing_account[2]}")
                print(f"      Name: {existing_account[3]}")
                print(f"      Active: {existing_account[4]}")
                print(f"\n   ✅ Migration not needed - account exists!")
                return True
            
            print(f"   ❌ Account with bot_id 262662172 not found")
            
            # Create the missing account
            print(f"\n2. Creating missing account...")
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
                    :created_at,
                    :updated_at
                )
                RETURNING id, bot_id, bot_username
            """), {
                "bot_id": 262662172,
                "bot_username": "prohelpBot",
                "bot_name": "helper",
                "bot_token": "262662172:AAGyAYVzuFFe23GagWY-FnP2NlAQRy_JsRk",
                "is_active": True,
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            })
            
            new_account = result.fetchone()
            db.session.commit()
            
            print(f"   ✅ Account created successfully:")
            print(f"      Database ID: {new_account[0]}")
            print(f"      Bot ID: {new_account[1]}")
            print(f"      Username: {new_account[2]}")
            
            # Verify the account was created
            print(f"\n3. Verifying account creation...")
            result = db.session.execute(db.text("""
                SELECT id, bot_id, bot_username, bot_name, is_active, created_at
                FROM accounts 
                WHERE bot_id = :bot_id
            """), {"bot_id": 262662172})
            
            verified_account = result.fetchone()
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
            
            print(f"\n✅ Database migration completed successfully!")
            print(f"\n🧪 Channel Service should now work correctly:")
            print(f"   - GET /api/accounts/262662172/channel should return CHANNEL_NOT_CONFIGURED")
            print(f"   - POST /api/channels/verify should return channel verification results")
            
            return True
            
    except Exception as e:
        print(f"❌ Migration error: {str(e)}")
        logger.exception("Migration failed")
        return False

if __name__ == "__main__":
    print("🔄 Automatic Database Migration")
    print("=" * 40)
    print("Creating missing account record for bot_id 262662172")
    print("This script runs automatically during Railway deployment")
    print("=" * 40)
    
    success = run_migration()
    
    if success:
        print(f"\n✅ MIGRATION COMPLETED SUCCESSFULLY!")
        print(f"   Account record created for bot_id 262662172")
        print(f"   Channel Service endpoints should now work consistently")
    else:
        print(f"\n❌ MIGRATION FAILED!")
        print(f"   Manual intervention may be required")
        sys.exit(1)
    
    print(f"\n🎯 Migration script finished!")

