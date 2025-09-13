#!/usr/bin/env python3
"""
Test script to verify endpoint consistency
Tests both GET /api/accounts/{bot_id}/channel and POST /api/channels/verify
"""

import requests
import json

def test_endpoint_consistency():
    """Test both endpoints with the same bot_id to verify consistency"""
    
    print("🧪 Testing Channel Service Endpoint Consistency")
    print("=" * 60)
    
    base_url = "https://telegive-channel-production.up.railway.app"
    bot_id = 262662172
    test_channel = "@dxstest"
    
    print(f"Testing with bot_id: {bot_id}")
    print(f"Testing with channel: {test_channel}")
    
    # Test 1: GET channel config
    print(f"\n1. Testing GET /api/accounts/{bot_id}/channel")
    print("-" * 50)
    
    try:
        response1 = requests.get(f"{base_url}/api/accounts/{bot_id}/channel", timeout=10)
        print(f"   Status Code: {response1.status_code}")
        data1 = response1.json()
        print(f"   Response: {json.dumps(data1, indent=2)}")
        
        if response1.status_code == 404 and data1.get('code') == 'CHANNEL_NOT_CONFIGURED':
            print(f"   ✅ GET endpoint: Account found, no channel configured (expected)")
            get_success = True
        elif response1.status_code == 404 and data1.get('code') == 'ACCOUNT_NOT_FOUND':
            print(f"   ❌ GET endpoint: Account not found")
            get_success = False
        else:
            print(f"   ✅ GET endpoint: Account found with channel configuration")
            get_success = True
            
    except Exception as e:
        print(f"   ❌ GET endpoint error: {str(e)}")
        get_success = False
    
    # Test 2: POST channel verify
    print(f"\n2. Testing POST /api/channels/verify")
    print("-" * 50)
    
    try:
        payload = {
            "account_id": bot_id,
            "channel_username": test_channel
        }
        
        response2 = requests.post(
            f"{base_url}/api/channels/verify",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print(f"   Status Code: {response2.status_code}")
        data2 = response2.json()
        print(f"   Response: {json.dumps(data2, indent=2)}")
        
        if response2.status_code == 404 and data2.get('code') == 'ACCOUNT_NOT_FOUND':
            print(f"   ❌ POST endpoint: Account not found")
            post_success = False
        elif response2.status_code in [200, 400]:  # 400 might be channel-related, not account-related
            if data2.get('code') in ['CHANNEL_NOT_FOUND', 'BOT_NOT_ADMIN', 'BOT_NOT_MEMBER']:
                print(f"   ✅ POST endpoint: Account found, channel verification result")
                post_success = True
            elif data2.get('success'):
                print(f"   ✅ POST endpoint: Account found, channel verification successful")
                post_success = True
            else:
                print(f"   ❓ POST endpoint: Unexpected response")
                post_success = False
        else:
            print(f"   ❓ POST endpoint: Unexpected status code")
            post_success = False
            
    except Exception as e:
        print(f"   ❌ POST endpoint error: {str(e)}")
        post_success = False
    
    # Summary
    print(f"\n📊 Consistency Test Results")
    print("=" * 30)
    print(f"GET /api/accounts/{bot_id}/channel: {'✅ PASS' if get_success else '❌ FAIL'}")
    print(f"POST /api/channels/verify: {'✅ PASS' if post_success else '❌ FAIL'}")
    
    if get_success and post_success:
        print(f"\n✅ CONSISTENCY CHECK PASSED")
        print(f"   Both endpoints correctly find the account")
        print(f"   Channel verification can proceed normally")
    elif get_success and not post_success:
        print(f"\n❌ INCONSISTENCY DETECTED")
        print(f"   GET endpoint finds account, POST endpoint doesn't")
        print(f"   This is the exact issue reported by dashboard developer")
    elif not get_success and not post_success:
        print(f"\n❌ ACCOUNT NOT FOUND")
        print(f"   Neither endpoint finds the account")
        print(f"   Database fix still needed")
    else:
        print(f"\n❓ UNEXPECTED RESULT")
        print(f"   POST works but GET doesn't (unusual)")
    
    return get_success and post_success

if __name__ == "__main__":
    test_endpoint_consistency()

