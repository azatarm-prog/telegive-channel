#!/usr/bin/env python3
"""
Database migration script to create channel_configs table
This ensures the shared database has the correct schema for channel configurations
"""

import os
import sys
import logging
from datetime import datetime

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from models import db, ChannelConfig, ChannelValidationHistory
from config.settings import Config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_app():
    """Create Flask app for database operations"""
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    return app

def check_table_exists(table_name):
    """Check if a table exists in the database"""
    try:
        result = db.session.execute(db.text(f"""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = '{table_name}'
            );
        """))
        return result.scalar()
    except Exception as e:
        logger.error(f"Error checking if table {table_name} exists: {e}")
        return False

def get_table_schema(table_name):
    """Get the schema of a table"""
    try:
        result = db.session.execute(db.text(f"""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = '{table_name}'
            ORDER BY ordinal_position;
        """))
        return result.fetchall()
    except Exception as e:
        logger.error(f"Error getting schema for table {table_name}: {e}")
        return []

def run_migration():
    """Run the database migration"""
    try:
        logger.info("🗄️ Starting database migration for channel_configs table...")
        
        # Check if channel_configs table exists
        channel_configs_exists = check_table_exists('channel_configs')
        logger.info(f"📋 channel_configs table exists: {channel_configs_exists}")
        
        # Check if channel_validation_history table exists
        validation_history_exists = check_table_exists('channel_validation_history')
        logger.info(f"📋 channel_validation_history table exists: {validation_history_exists}")
        
        # Check if accounts table exists (should exist from Auth Service)
        accounts_exists = check_table_exists('accounts')
        logger.info(f"📋 accounts table exists: {accounts_exists}")
        
        if not accounts_exists:
            logger.error("❌ accounts table does not exist! This is required for foreign key relationship.")
            return False
        
        # Get accounts table schema to understand the structure
        accounts_schema = get_table_schema('accounts')
        logger.info(f"📋 accounts table schema:")
        for column in accounts_schema:
            logger.info(f"   - {column[0]}: {column[1]} (nullable: {column[2]})")
        
        # Create tables if they don't exist
        if not channel_configs_exists or not validation_history_exists:
            logger.info("🔧 Creating missing tables...")
            
            # Create all tables defined in models
            db.create_all()
            
            logger.info("✅ Tables created successfully")
            
            # Verify tables were created
            channel_configs_exists = check_table_exists('channel_configs')
            validation_history_exists = check_table_exists('channel_validation_history')
            
            logger.info(f"✅ channel_configs table now exists: {channel_configs_exists}")
            logger.info(f"✅ channel_validation_history table now exists: {validation_history_exists}")
            
            if channel_configs_exists:
                # Show the created schema
                schema = get_table_schema('channel_configs')
                logger.info("📋 channel_configs table schema:")
                for column in schema:
                    logger.info(f"   - {column[0]}: {column[1]} (nullable: {column[2]})")
        else:
            logger.info("✅ All required tables already exist")
        
        # Test database connectivity
        logger.info("🧪 Testing database operations...")
        
        # Test basic query
        result = db.session.execute(db.text("SELECT 1 as test"))
        test_value = result.scalar()
        logger.info(f"✅ Database connection test: {test_value}")
        
        # Test accounts table access
        accounts_count = db.session.execute(db.text("SELECT COUNT(*) FROM accounts")).scalar()
        logger.info(f"✅ Accounts table accessible, count: {accounts_count}")
        
        # Test channel_configs table access
        if channel_configs_exists:
            configs_count = db.session.execute(db.text("SELECT COUNT(*) FROM channel_configs")).scalar()
            logger.info(f"✅ Channel configs table accessible, count: {configs_count}")
        
        logger.info("🎉 Database migration completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Database migration failed: {str(e)}")
        logger.error(f"Error type: {type(e).__name__}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False

def main():
    """Main function"""
    print("🗄️ Channel Service Database Migration")
    print("=====================================")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()
    
    app = create_app()
    
    with app.app_context():
        success = run_migration()
        
        if success:
            print("\n✅ Migration completed successfully!")
            print("The channel_configs table is now ready for use.")
            return 0
        else:
            print("\n❌ Migration failed!")
            print("Please check the logs for details.")
            return 1

if __name__ == "__main__":
    exit(main())

