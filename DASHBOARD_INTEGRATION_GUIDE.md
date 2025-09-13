# Dashboard Integration Guide - Channel Management Service

## 🚨 **IMPORTANT: `account_id` is now `bot_id`**

**Key Change:** The `{account_id}` parameter in all API endpoints now refers to the **Telegram bot ID** (e.g., `262662172`), not the database primary key.

This change was made to fix a critical database synchronization issue. Please update your frontend code accordingly.

## 📋 **API Endpoints Overview**

All channel-related operations should call the **Channel Management Service**.

### **Base URL**
```
https://telegive-channel-production.up.railway.app
```

### **Available Endpoints**
1. `GET /api/accounts/{bot_id}/channel` - Get channel configuration
2. `PUT /api/accounts/{bot_id}/channel` - Save/update channel configuration
3. `DELETE /api/accounts/{bot_id}/channel` - Delete channel configuration
4. `POST /api/channels/verify` - Verify channel and bot permissions

## 🔧 **Endpoint Details**

### **1. Get Channel Configuration**

**Endpoint:** `GET /api/accounts/{bot_id}/channel`

**Example Request:**
```bash
cURL -X GET https://telegive-channel-production.up.railway.app/api/accounts/262662172/channel
```

**Success Response (200):**
```json
{
  "success": true,
  "channel": {
    "id": 1,
    "account_id": 262662172, // This is the bot_id
    "channel_username": "@mychannel",
    "channel_title": "My Awesome Channel",
    "channel_id": -1001234567890,
    "is_verified": true,
    "verified_at": "2025-09-13T10:30:00Z"
  }
}
```

### **2. Save/Update Channel Configuration**

**Endpoint:** `PUT /api/accounts/{bot_id}/channel`

**Example Request:**
```bash
cURL -X PUT https://telegive-channel-production.up.railway.app/api/accounts/262662172/channel \
  -H "Content-Type: application/json" \
  -d '{
    "channel_username": "@mychannel",
    "channel_title": "My Awesome Channel",
    "is_verified": true
  }'
```

### **3. Delete Channel Configuration**

**Endpoint:** `DELETE /api/accounts/{bot_id}/channel`

**Example Request:**
```bash
cURL -X DELETE https://telegive-channel-production.up.railway.app/api/accounts/262662172/channel
```

### **4. Verify Channel and Bot Permissions**

**Endpoint:** `POST /api/channels/verify`

**Request Body:**
```json
{
  "channel_username": "@mychannel",
  "account_id": 262662172 // This is the bot_id
}
```

## 🔐 **Authentication**

The Channel Management Service no longer depends on the Auth Service for account lookups. It now uses a direct, shared database connection.

- **No API keys or tokens are needed** to call the Channel Service endpoints.
- The service validates the `bot_id` directly against the shared `accounts` table.

## 📝 **Frontend Integration Example**

### **JavaScript/TypeScript Example (Updated)**

```javascript
const CHANNEL_SERVICE_URL = 'https://telegive-channel-production.up.railway.app';

// Get channel configuration using bot_id
async function getChannelConfig(botId) {
  try {
    const response = await fetch(`${CHANNEL_SERVICE_URL}/api/accounts/${botId}/channel`);
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

// Verify channel using bot_id
async function verifyChannel(botId, channelUsername) {
  try {
    const response = await fetch(`${CHANNEL_SERVICE_URL}/api/channels/verify`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        account_id: botId, // Pass bot_id as account_id
        channel_username: channelUsername
      })
    });
    
    const data = await response.json();
    
    if (response.ok && data.success) {
      return { verified: true, channelInfo: data };
    } else {
      return { verified: false, error: data.error, code: data.code };
    }
  } catch (error) {
    console.error('Error verifying channel:', error);
    throw error;
  }
}

// Save channel configuration using bot_id
async function saveChannelConfig(botId, channelData) {
  try {
    const response = await fetch(`${CHANNEL_SERVICE_URL}/api/accounts/${botId}/channel`, {
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
```

## 🚀 **Deployment & Testing**

The updated service is deployed and ready for integration testing.

**Test with a valid `bot_id`:**
```bash
# Test with bot_id 262662172
curl https://telegive-channel-production.up.railway.app/api/accounts/262662172/channel
```

**Expected Response (if no channel configured):**
```json
{
  "success": false,
  "error": "No channel configuration found for bot_id 262662172",
  "code": "CHANNEL_NOT_CONFIGURED"
}
```

---

**Last Updated:** September 13, 2025  
**Service Version:** 1.1.0 (Database Sync Fix)


