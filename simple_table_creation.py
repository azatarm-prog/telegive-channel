#!/usr/bin/env python3
"""
Simple table creation script for channel_configs
This creates the table without foreign key constraints to avoid dependency issues
"""

import os
import sys
import logging
from datetime import datetime

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from models import db
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

def create_tables_simple():
    """Create tables using simple SQL without foreign key constraints"""
    try:
        logger.info("🗄️ Creating channel_configs table with simple SQL...")
        
        # Create channel_configs table
        db.session.execute(db.text("""
            CREATE TABLE IF NOT EXISTS channel_configs (
                id BIGSERIAL PRIMARY KEY,
                account_id BIGINT NOT NULL,
                channel_id BIGINT NOT NULL,
                channel_username VARCHAR(100) NOT NULL,
                channel_title VARCHAR(255) NOT NULL,
                channel_type VARCHAR(20) DEFAULT 'channel',
                channel_member_count INTEGER DEFAULT 0,
                can_post_messages BOOLEAN DEFAULT FALSE,
                can_edit_messages BOOLEAN DEFAULT FALSE,
                can_send_media_messages BOOLEAN DEFAULT FALSE,
                can_delete_messages BOOLEAN DEFAULT FALSE,
                can_pin_messages BOOLEAN DEFAULT FALSE,
                is_validated BOOLEAN DEFAULT FALSE,
                last_validation_at TIMESTAMP WITH TIME ZONE,
                validation_error TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
        """))
        
        # Create unique constraint
        db.session.execute(db.text("""
            CREATE UNIQUE INDEX IF NOT EXISTS uq_channel_configs_account_id 
            ON channel_configs(account_id);
        """))
        
        # Create indexes for performance
        db.session.execute(db.text("""
            CREATE INDEX IF NOT EXISTS idx_channel_configs_channel_id 
            ON channel_configs(channel_id);
        """))
        
        # Create channel_validation_history table
        db.session.execute(db.text("""
            CREATE TABLE IF NOT EXISTS channel_validation_history (
                id BIGSERIAL PRIMARY KEY,
                channel_config_id BIGINT NOT NULL,
                validation_type VARCHAR(50) NOT NULL,
                result BOOLEAN NOT NULL,
                error_message TEXT,
                permissions JSONB,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
        """))
        
        # Create index for validation history
        db.session.execute(db.text("""
            CREATE INDEX IF NOT EXISTS idx_validation_history_config_id 
            ON channel_validation_history(channel_config_id);
        """))
        
        db.session.commit()
        
        logger.info("✅ Tables created successfully!")
        
        # Test the tables
        result = db.session.execute(db.text("SELECT COUNT(*) FROM channel_configs")).scalar()
        logger.info(f"✅ channel_configs table accessible, count: {result}")
        
        result = db.session.execute(db.text("SELECT COUNT(*) FROM channel_validation_history")).scalar()
        logger.info(f"✅ channel_validation_history table accessible, count: {result}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error creating tables: {str(e)}")
        db.session.rollback()
        return False

def run_simple_migration():
    """Run the simple migration"""
    try:
        logger.info("🗄️ Starting simple table creation...")
        
        # Test database connection first
        result = db.session.execute(db.text("SELECT 1 as test")).scalar()
        logger.info(f"✅ Database connection test: {result}")
        
        # Create tables
        success = create_tables_simple()
        
        if success:
            logger.info("🎉 Simple migration completed successfully!")
            return True
        else:
            logger.error("❌ Simple migration failed!")
            return False
            
    except Exception as e:
        logger.error(f"❌ Migration error: {str(e)}")
        return False

def main():
    """Main function"""
    print("🗄️ Simple Channel Service Table Creation")
    print("========================================")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()
    
    app = create_app()
    
    with app.app_context():
        success = run_simple_migration()
        
        if success:
            print("\n✅ Table creation completed successfully!")
            return 0
        else:
            print("\n❌ Table creation failed!")
            return 1

if __name__ == "__main__":
    exit(main())

