#!/usr/bin/env python3
"""
Check if the database migration worked
Tests if account 262662172 exists in the database
"""

import requests
import json

def check_migration_status():
    """Check if the migration created the account successfully"""
    
    print("🔍 Checking Database Migration Status")
    print("=" * 50)
    
    base_url = "https://telegive-channel-production.up.railway.app"
    bot_id = 262662172
    
    # Test both endpoints to see current status
    print(f"Testing both endpoints with bot_id: {bot_id}")
    
    # Test 1: GET endpoint
    print(f"\n1. GET /api/accounts/{bot_id}/channel")
    try:
        response1 = requests.get(f"{base_url}/api/accounts/{bot_id}/channel", timeout=10)
        data1 = response1.json()
        
        if response1.status_code == 404 and data1.get('code') == 'CHANNEL_NOT_CONFIGURED':
            print(f"   ✅ GET: Account found, no channel (migration worked)")
            get_works = True
        elif response1.status_code == 404 and data1.get('code') == 'ACCOUNT_NOT_FOUND':
            print(f"   ❌ GET: Account not found (migration failed)")
            get_works = False
        else:
            print(f"   ✅ GET: Account found with channel")
            get_works = True
            
    except Exception as e:
        print(f"   ❌ GET: Error - {str(e)}")
        get_works = False
    
    # Test 2: POST endpoint
    print(f"\n2. POST /api/channels/verify")
    try:
        payload = {"account_id": bot_id, "channel_username": "@dxstest"}
        response2 = requests.post(f"{base_url}/api/channels/verify", json=payload, timeout=10)
        data2 = response2.json()
        
        if response2.status_code == 404 and data2.get('code') == 'ACCOUNT_NOT_FOUND':
            print(f"   ❌ POST: Account not found (migration failed)")
            post_works = False
        elif response2.status_code in [200, 400]:  # 400 could be channel-related
            if data2.get('code') in ['CHANNEL_NOT_FOUND', 'BOT_NOT_ADMIN', 'BOT_NOT_MEMBER']:
                print(f"   ✅ POST: Account found, channel issue (migration worked)")
                post_works = True
            elif data2.get('success'):
                print(f"   ✅ POST: Account found, verification successful (migration worked)")
                post_works = True
            else:
                print(f"   ❓ POST: Unexpected response")
                post_works = False
        else:
            print(f"   ❓ POST: Status {response2.status_code}")
            post_works = False
            
    except Exception as e:
        print(f"   ❌ POST: Error - {str(e)}")
        post_works = False
    
    # Analysis
    print(f"\n📊 Migration Status Analysis")
    print("=" * 35)
    
    if get_works and post_works:
        print(f"✅ MIGRATION SUCCESSFUL")
        print(f"   Both endpoints find the account")
        print(f"   Database migration worked correctly")
        return True
    elif get_works and not post_works:
        print(f"❌ MIGRATION INCOMPLETE")
        print(f"   GET works but POST doesn't")
        print(f"   There's still an inconsistency issue")
        return False
    elif not get_works and not post_works:
        print(f"❌ MIGRATION FAILED")
        print(f"   Neither endpoint finds the account")
        print(f"   Account record was not created")
        return False
    else:
        print(f"❓ UNEXPECTED STATE")
        print(f"   POST works but GET doesn't")
        return False

def suggest_next_steps(migration_worked):
    """Suggest next steps based on migration status"""
    
    print(f"\n🎯 Next Steps")
    print("=" * 15)
    
    if migration_worked:
        print(f"✅ Ready for frontend testing!")
        print(f"   1. Test channel configuration in dashboard")
        print(f"   2. Verify end-to-end channel setup flow")
        print(f"   3. Test with real channel (@dxstest)")
    else:
        print(f"❌ Migration needs attention:")
        print(f"   1. Check Railway deployment logs")
        print(f"   2. Verify DATABASE_URL is accessible")
        print(f"   3. Run migration manually if needed")
        print(f"   4. Check for database connection issues")

if __name__ == "__main__":
    migration_worked = check_migration_status()
    suggest_next_steps(migration_worked)

