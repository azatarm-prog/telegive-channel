#!/usr/bin/env python3
"""
Database debugging script to identify the account sync issue
"""
import os
import sys
import logging

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def debug_database():
    try:
        from app import create_app
        from models import db
        
        app = create_app()
        with app.app_context():
            print("🔍 DATABASE DEBUGGING REPORT")
            print("=" * 50)
            
            # 1. Check database connection
            try:
                result = db.session.execute(db.text("SELECT current_database(), current_user, version()"))
                row = result.fetchone()
                print(f"✅ Database Connection: SUCCESS")
                print(f"   Database: {row[0]}")
                print(f"   User: {row[1]}")
                print(f"   Version: {row[2][:50]}...")
            except Exception as e:
                print(f"❌ Database Connection: FAILED - {e}")
                return
            
            print("\n" + "=" * 50)
            
            # 2. List all tables
            try:
                result = db.session.execute(db.text("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_type = 'BASE TABLE'
                    ORDER BY table_name
                """))
                
                tables = [row[0] for row in result.fetchall()]
                print(f"📋 EXISTING TABLES ({len(tables)} total):")
                for table in tables:
                    print(f"   - {table}")
                
                # Identify account-related tables
                account_tables = [t for t in tables if any(keyword in t.lower() for keyword in ['account', 'user', 'bot', 'auth'])]
                print(f"\n🔍 ACCOUNT-RELATED TABLES ({len(account_tables)} found):")
                for table in account_tables:
                    print(f"   - {table}")
                    
            except Exception as e:
                print(f"❌ Table listing failed: {e}")
                return
            
            print("\n" + "=" * 50)
            
            # 3. Check each account-related table for account 262662172
            target_account = 262662172
            print(f"🎯 SEARCHING FOR ACCOUNT {target_account}:")
            
            found_account = False
            for table in account_tables:
                try:
                    # First check table structure
                    result = db.session.execute(db.text(f"""
                        SELECT column_name, data_type 
                        FROM information_schema.columns 
                        WHERE table_name = '{table}' 
                        AND table_schema = 'public'
                        ORDER BY ordinal_position
                    """))
                    
                    columns = [(row[0], row[1]) for row in result.fetchall()]
                    print(f"\n   📊 Table: {table}")
                    print(f"      Columns: {', '.join([f'{col[0]}({col[1]})' for col in columns[:5]])}{'...' if len(columns) > 5 else ''}")
                    
                    # Check if table has an 'id' column
                    if any(col[0] == 'id' for col in columns):
                        result = db.session.execute(db.text(f"SELECT * FROM {table} WHERE id = {target_account} LIMIT 1"))
                        row = result.fetchone()
                        
                        if row:
                            print(f"      ✅ FOUND ACCOUNT {target_account}!")
                            print(f"      Data: {dict(row._mapping)}")
                            found_account = True
                        else:
                            # Check total count in table
                            count_result = db.session.execute(db.text(f"SELECT COUNT(*) FROM {table}"))
                            count = count_result.fetchone()[0]
                            print(f"      ❌ Account {target_account} not found (table has {count} records)")
                    else:
                        print(f"      ⚠️  No 'id' column found")
                        
                except Exception as e:
                    print(f"      ❌ Error checking table {table}: {e}")
            
            print("\n" + "=" * 50)
            
            # 4. Check what Channel Service models expect
            print("🏗️  CHANNEL SERVICE MODEL EXPECTATIONS:")
            try:
                from models import ChannelConfig
                print(f"   - ChannelConfig table: {ChannelConfig.__tablename__}")
                
                # Check if ChannelConfig table exists and has data
                count_result = db.session.execute(db.text(f"SELECT COUNT(*) FROM {ChannelConfig.__tablename__}"))
                count = count_result.fetchone()[0]
                print(f"   - ChannelConfig records: {count}")
                
                # Check for account_id references
                if count > 0:
                    result = db.session.execute(db.text(f"SELECT DISTINCT account_id FROM {ChannelConfig.__tablename__} LIMIT 5"))
                    account_ids = [row[0] for row in result.fetchall()]
                    print(f"   - Sample account_ids in ChannelConfig: {account_ids}")
                
            except Exception as e:
                print(f"   ❌ Error checking ChannelConfig: {e}")
            
            print("\n" + "=" * 50)
            
            # 5. Summary and recommendations
            print("📋 SUMMARY:")
            if found_account:
                print(f"   ✅ Account {target_account} EXISTS in shared database")
                print("   🔧 Issue likely: Channel Service not looking in correct table")
            else:
                print(f"   ❌ Account {target_account} NOT FOUND in any table")
                print("   🔧 Issue likely: Account not synced to shared database")
            
            print(f"\n   📊 Total tables: {len(tables)}")
            print(f"   📊 Account-related tables: {len(account_tables)}")
            
            print("\n🎯 NEXT STEPS:")
            if found_account:
                print("   1. Update Channel Service to use correct table name")
                print("   2. Verify account lookup logic in routes/accounts.py")
                print("   3. Test account retrieval after fix")
            else:
                print("   1. Check Auth Service database connection")
                print("   2. Verify both services use same DATABASE_URL")
                print("   3. Implement account sync from Auth Service")
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("   Make sure you're in the correct directory and dependencies are installed")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    debug_database()

