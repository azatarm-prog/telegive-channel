#!/usr/bin/env python3
"""
Fix the channel_validation_history table schema to match the SQLAlchemy model
This script will rename columns to match what the model expects
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

def fix_validation_history_table():
    """Fix the validation history table schema"""
    try:
        logger.info("🔧 Fixing channel_validation_history table schema...")
        
        # Check if the table exists
        result = db.session.execute(db.text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'channel_validation_history'
            );
        """))
        
        if not result.scalar():
            logger.info("📋 Table doesn't exist, creating with correct schema...")
            # Create the table with correct schema
            db.session.execute(db.text("""
                CREATE TABLE channel_validation_history (
                    id BIGSERIAL PRIMARY KEY,
                    channel_config_id BIGINT NOT NULL,
                    validation_type VARCHAR(50) NOT NULL,
                    validation_result BOOLEAN NOT NULL,
                    error_message TEXT,
                    permissions_snapshot JSONB,
                    validated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                );
            """))
            
            db.session.execute(db.text("""
                CREATE INDEX idx_validation_history_config_id 
                ON channel_validation_history(channel_config_id);
            """))
            
            db.session.commit()
            logger.info("✅ Table created with correct schema")
            return True
        
        # Check current columns
        result = db.session.execute(db.text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'channel_validation_history'
            ORDER BY ordinal_position;
        """))
        
        columns = [row[0] for row in result.fetchall()]
        logger.info(f"📋 Current columns: {columns}")
        
        # Check if we need to rename columns
        needs_fix = False
        
        if 'result' in columns and 'validation_result' not in columns:
            logger.info("🔧 Renaming 'result' to 'validation_result'...")
            db.session.execute(db.text("""
                ALTER TABLE channel_validation_history 
                RENAME COLUMN result TO validation_result;
            """))
            needs_fix = True
        
        if 'permissions' in columns and 'permissions_snapshot' not in columns:
            logger.info("🔧 Renaming 'permissions' to 'permissions_snapshot'...")
            db.session.execute(db.text("""
                ALTER TABLE channel_validation_history 
                RENAME COLUMN permissions TO permissions_snapshot;
            """))
            needs_fix = True
        
        if 'created_at' in columns and 'validated_at' not in columns:
            logger.info("🔧 Renaming 'created_at' to 'validated_at'...")
            db.session.execute(db.text("""
                ALTER TABLE channel_validation_history 
                RENAME COLUMN created_at TO validated_at;
            """))
            needs_fix = True
        
        if needs_fix:
            db.session.commit()
            logger.info("✅ Table schema fixed successfully")
        else:
            logger.info("✅ Table schema already correct")
        
        # Verify the final schema
        result = db.session.execute(db.text("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'channel_validation_history'
            ORDER BY ordinal_position;
        """))
        
        logger.info("📋 Final schema:")
        for column_name, data_type in result.fetchall():
            logger.info(f"   - {column_name}: {data_type}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error fixing table schema: {str(e)}")
        db.session.rollback()
        return False

def main():
    """Main function"""
    print("🔧 Fix Channel Validation History Table Schema")
    print("==============================================")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()
    
    app = create_app()
    
    with app.app_context():
        success = fix_validation_history_table()
        
        if success:
            print("\n✅ Schema fix completed successfully!")
            return 0
        else:
            print("\n❌ Schema fix failed!")
            return 1

if __name__ == "__main__":
    exit(main())

