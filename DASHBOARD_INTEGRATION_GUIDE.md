# Dashboard Integration Guide - Channel Management Service

## 🚨 **IMPORTANT: Correct Service URL**

**❌ WRONG URL (Don't use):**
```
https://telegive-giveaway-production.up.railway.app
```

**✅ CORRECT URL (Use this):**
```
https://telegive-channel-production.up.railway.app
```

## 📋 **API Endpoints Overview**

All channel-related operations should call the **Channel Management Service**, not the Giveaway Service.

### **Base URL**
```
https://telegive-channel-production.up.railway.app
```

### **Available Endpoints**
1. `GET /api/accounts/{account_id}/channel` - Get channel configuration
2. `PUT /api/accounts/{account_id}/channel` - Save/update channel configuration
3. `DELETE /api/accounts/{account_id}/channel` - Delete channel configuration
4. `POST /api/channels/verify` - Verify channel and bot permissions

## 🔧 **Endpoint Details**

### **1. Get Channel Configuration**

**Endpoint:** `GET /api/accounts/{account_id}/channel`

**Example Request:**
```bash
curl -X GET https://telegive-channel-production.up.railway.app/api/accounts/262662172/channel
```

**Success Response (200):**
```json
{
  "success": true,
  "channel": {
    "id": 1,
    "account_id": 262662172,
    "channel_username": "@mychannel",
    "channel_title": "My Awesome Channel",
    "channel_id": -1001234567890,
    "is_verified": true,
    "verified_at": "2025-09-13T10:30:00Z",
    "created_at": "2025-09-13T09:00:00Z",
    "updated_at": "2025-09-13T10:30:00Z"
  }
}
```

**No Configuration Response (404):**
```json
{
  "success": false,
  "error": "No channel configuration found",
  "code": "CHANNEL_NOT_CONFIGURED"
}
```

**Account Not Found Response (404):**
```json
{
  "success": false,
  "error": "Account not found or invalid",
  "code": "ACCOUNT_NOT_FOUND"
}
```

### **2. Save/Update Channel Configuration**

**Endpoint:** `PUT /api/accounts/{account_id}/channel`

**Example Request:**
```bash
curl -X PUT https://telegive-channel-production.up.railway.app/api/accounts/262662172/channel \
  -H "Content-Type: application/json" \
  -d '{
    "channel_username": "@mychannel",
    "channel_title": "My Awesome Channel",
    "is_verified": true
  }'
```

**Request Body:**
```json
{
  "channel_username": "@mychannel",
  "channel_title": "My Awesome Channel",
  "is_verified": true
}
```

**Success Response (200):**
```json
{
  "success": true,
  "message": "Channel configuration saved successfully",
  "channel": {
    "id": 1,
    "account_id": 262662172,
    "channel_username": "@mychannel",
    "channel_title": "My Awesome Channel",
    "channel_id": -1001234567890,
    "is_verified": true,
    "verified_at": "2025-09-13T10:30:00Z",
    "created_at": "2025-09-13T09:00:00Z",
    "updated_at": "2025-09-13T10:30:00Z"
  }
}
```

**Validation Error Response (400):**
```json
{
  "success": false,
  "error": "Channel username is required",
  "code": "MISSING_CHANNEL_USERNAME"
}
```

### **3. Delete Channel Configuration**

**Endpoint:** `DELETE /api/accounts/{account_id}/channel`

**Example Request:**
```bash
curl -X DELETE https://telegive-channel-production.up.railway.app/api/accounts/262662172/channel
```

**Success Response (200):**
```json
{
  "success": true,
  "message": "Channel configuration deleted successfully"
}
```

**No Configuration Response (404):**
```json
{
  "success": false,
  "error": "No channel configuration found to delete",
  "code": "CHANNEL_NOT_CONFIGURED"
}
```

### **4. Verify Channel and Bot Permissions**

**Endpoint:** `POST /api/channels/verify`

**Example Request:**
```bash
curl -X POST https://telegive-channel-production.up.railway.app/api/channels/verify \
  -H "Content-Type: application/json" \
  -d '{
    "channel_username": "@mychannel",
    "account_id": 262662172
  }'
```

**Request Body:**
```json
{
  "channel_username": "@mychannel",
  "account_id": 262662172
}
```

**Success Response (200):**
```json
{
  "success": true,
  "channel_exists": true,
  "bot_is_admin": true,
  "bot_can_post_messages": true,
  "bot_can_edit_messages": true,
  "channel_title": "My Awesome Channel",
  "channel_id": -1001234567890,
  "member_count": 1234,
  "channel_type": "channel",
  "verified_at": "2025-09-13T10:30:00Z"
}
```

**Channel Not Found Response (400):**
```json
{
  "success": false,
  "channel_exists": false,
  "error": "Channel not found or is private",
  "code": "CHANNEL_NOT_FOUND"
}
```

**Bot Not Admin Response (400):**
```json
{
  "success": false,
  "channel_exists": true,
  "bot_is_admin": false,
  "error": "Bot is not an administrator in this channel",
  "code": "BOT_NOT_ADMIN"
}
```

**Insufficient Permissions Response (400):**
```json
{
  "success": false,
  "channel_exists": true,
  "bot_is_admin": true,
  "bot_can_post_messages": false,
  "bot_can_edit_messages": false,
  "error": "Bot lacks required permissions (post_messages, edit_messages)",
  "code": "INSUFFICIENT_PERMISSIONS"
}
```

## 🔐 **Authentication**

The Channel Management Service integrates with the Auth Service to validate accounts. No additional authentication headers are required - the service will validate the account ID internally.

## 🌐 **CORS Configuration**

The service is configured with proper CORS headers for dashboard integration:

**Allowed Origins:**
- `https://telegive-dashboard-production.up.railway.app`
- `http://localhost:5173` (for development)
- `http://localhost:3000` (for development)

**Allowed Methods:**
- `GET`, `POST`, `PUT`, `DELETE`, `OPTIONS`

**Allowed Headers:**
- `Content-Type`, `Authorization`, `Accept`, `X-Requested-With`

## 🧪 **Testing the Integration**

### **1. Test Service Health**
```bash
curl https://telegive-channel-production.up.railway.app/health
```

**Expected Response:**
```json
{
  "database": "connected",
  "service": "channel-service",
  "status": "healthy",
  "telegram_api": "accessible",
  "version": "1.0.0"
}
```

### **2. Test CORS Preflight**
```bash
curl -X OPTIONS \
  -H "Origin: https://telegive-dashboard-production.up.railway.app" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: Content-Type" \
  https://telegive-channel-production.up.railway.app/api/channels/verify
```

**Expected Response:**
```
HTTP/2 200
access-control-allow-origin: https://telegive-dashboard-production.up.railway.app
access-control-allow-methods: GET,POST,PUT,DELETE,OPTIONS
access-control-allow-headers: Content-Type,Authorization,Accept,X-Requested-With
access-control-allow-credentials: true
```

### **3. Test Channel Configuration (Account 1)**
```bash
curl https://telegive-channel-production.up.railway.app/api/accounts/1/channel
```

**Expected Response (if no channel configured):**
```json
{
  "success": false,
  "error": "No channel configuration found",
  "code": "CHANNEL_NOT_CONFIGURED"
}
```

## 📝 **Frontend Integration Example**

### **JavaScript/TypeScript Example**

```javascript
const CHANNEL_SERVICE_URL = 'https://telegive-channel-production.up.railway.app';

// Get channel configuration
async function getChannelConfig(accountId) {
  try {
    const response = await fetch(`${CHANNEL_SERVICE_URL}/api/accounts/${accountId}/channel`);
    const data = await response.json();
    
    if (response.ok && data.success) {
      return data.channel;
    } else if (data.code === 'CHANNEL_NOT_CONFIGURED') {
      return null; // No channel configured
    } else {
      throw new Error(data.error || 'Failed to get channel configuration');
    }
  } catch (error) {
    console.error('Error getting channel config:', error);
    throw error;
  }
}

// Verify channel
async function verifyChannel(accountId, channelUsername) {
  try {
    const response = await fetch(`${CHANNEL_SERVICE_URL}/api/channels/verify`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        account_id: accountId,
        channel_username: channelUsername
      })
    });
    
    const data = await response.json();
    
    if (response.ok && data.success) {
      return {
        verified: true,
        channelInfo: data
      };
    } else {
      return {
        verified: false,
        error: data.error,
        code: data.code
      };
    }
  } catch (error) {
    console.error('Error verifying channel:', error);
    throw error;
  }
}

// Save channel configuration
async function saveChannelConfig(accountId, channelData) {
  try {
    const response = await fetch(`${CHANNEL_SERVICE_URL}/api/accounts/${accountId}/channel`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(channelData)
    });
    
    const data = await response.json();
    
    if (response.ok && data.success) {
      return data.channel;
    } else {
      throw new Error(data.error || 'Failed to save channel configuration');
    }
  } catch (error) {
    console.error('Error saving channel config:', error);
    throw error;
  }
}

// Delete channel configuration
async function deleteChannelConfig(accountId) {
  try {
    const response = await fetch(`${CHANNEL_SERVICE_URL}/api/accounts/${accountId}/channel`, {
      method: 'DELETE'
    });
    
    const data = await response.json();
    
    if (response.ok && data.success) {
      return true;
    } else {
      throw new Error(data.error || 'Failed to delete channel configuration');
    }
  } catch (error) {
    console.error('Error deleting channel config:', error);
    throw error;
  }
}
```

## 🚀 **Environment Configuration**

Update your dashboard environment variables:

```env
# Channel Management Service
TELEGIVE_CHANNEL_URL=https://telegive-channel-production.up.railway.app

# Other services (for reference)
TELEGIVE_AUTH_URL=https://web-production-ddd7e.up.railway.app
TELEGIVE_GIVEAWAY_URL=https://telegive-giveaway-production.up.railway.app
```

## 🔍 **Troubleshooting**

### **Common Issues**

1. **404 Not Found**
   - ✅ Verify you're using the correct base URL: `https://telegive-channel-production.up.railway.app`
   - ❌ Don't use: `https://telegive-giveaway-production.up.railway.app`

2. **CORS Errors**
   - Ensure your dashboard origin is in the allowed list
   - Check that preflight OPTIONS requests are working

3. **Account Not Found**
   - Verify the account ID exists in the auth service
   - Check that the auth service is accessible

4. **Channel Not Configured**
   - This is expected for new accounts
   - Use the verify endpoint first, then save configuration

### **Debug Commands**

```bash
# Check service health
curl https://telegive-channel-production.up.railway.app/health

# Test CORS
curl -X OPTIONS -H "Origin: https://telegive-dashboard-production.up.railway.app" \
  https://telegive-channel-production.up.railway.app/api/channels/verify

# Test account endpoint
curl https://telegive-channel-production.up.railway.app/api/accounts/1/channel
```

## 📞 **Support**

If you encounter any issues:

1. **Verify the correct service URL** is being used
2. **Check the service health** endpoint
3. **Test with curl commands** provided above
4. **Check browser console** for CORS or network errors

**The Channel Management Service is fully operational and ready for dashboard integration!** 🎉

---

**Last Updated:** September 13, 2025  
**Service Version:** 1.0.0  
**Service URL:** https://telegive-channel-production.up.railway.app

