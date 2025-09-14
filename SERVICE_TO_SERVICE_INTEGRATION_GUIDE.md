# 🔗 Service-to-Service Integration Guide

## Channel Service ↔ Giveaway Service

This guide explains how the Giveaway Service can securely access Channel Service APIs to check channel configurations and status.

---

## 🔑 **Authentication**

### **Service Token**
```
Token: wk-HIYEuDdfm8lr05cW6Y-sxXkng8y2Ib7U7IVASHMcSCobknXRbhJgp60-fyxKF
Header: X-Service-Token
```

### **Environment Variable for Giveaway Service**
```bash
GIVEAWAY_SERVICE_TOKEN=wk-HIYEuDdfm8lr05cW6Y-sxXkng8y2Ib7U7IVASHMcSCobknXRbhJgp60-fyxKF
```

---

## 🛠️ **Available Endpoints**

### **1. Get Channel Configuration**
```
GET /api/service/channel/{bot_id}
```

**Headers:**
```
X-Service-Token: wk-HIYEuDdfm8lr05cW6Y-sxXkng8y2Ib7U7IVASHMcSCobknXRbhJgp60-fyxKF
Content-Type: application/json
```

**Response (Success):**
```json
{
  "success": true,
  "bot_id": 262662172,
  "account_id": 1,
  "channel": {
    "id": -1002741168040,
    "username": "@dxstest",
    "title": "DXS test channel",
    "type": "channel",
    "member_count": 0,
    "is_validated": true,
    "last_validation_at": "2025-09-14T14:30:00.000Z",
    "permissions": {
      "can_post_messages": true,
      "can_edit_messages": true,
      "can_send_media_messages": false,
      "can_delete_messages": true,
      "can_pin_messages": false
    },
    "created_at": "2025-09-14T14:30:00.000Z",
    "updated_at": "2025-09-14T14:30:00.000Z"
  },
  "requested_by": "giveaway_service",
  "timestamp": "2025-09-14T14:30:00.000Z"
}
```

**Response (Not Found):**
```json
{
  "success": false,
  "error": "Channel not configured",
  "code": "CHANNEL_NOT_CONFIGURED",
  "bot_id": 262662172,
  "account_id": 1
}
```

### **2. Get Channel Status**
```
GET /api/service/channel/{bot_id}/status
```

**Headers:**
```
X-Service-Token: wk-HIYEuDdfm8lr05cW6Y-sxXkng8y2Ib7U7IVASHMcSCobknXRbhJgp60-fyxKF
Content-Type: application/json
```

**Response:**
```json
{
  "success": true,
  "bot_id": 262662172,
  "account_id": 1,
  "status": "active",
  "message": "Channel configured and validated",
  "channel": {
    "id": -1002741168040,
    "username": "@dxstest",
    "title": "DXS test channel",
    "is_validated": true,
    "last_validation_at": "2025-09-14T14:30:00.000Z",
    "validation_error": null
  },
  "requested_by": "giveaway_service",
  "timestamp": "2025-09-14T14:30:00.000Z"
}
```

**Status Values:**
- `not_configured` - No channel configured
- `configured_not_validated` - Channel configured but validation failed
- `validation_error` - Channel has validation errors
- `active` - Channel configured and working

### **3. Batch Channel Lookup**
```
POST /api/service/channels/batch
```

**Headers:**
```
X-Service-Token: wk-HIYEuDdfm8lr05cW6Y-sxXkng8y2Ib7U7IVASHMcSCobknXRbhJgp60-fyxKF
Content-Type: application/json
```

**Request Body:**
```json
{
  "bot_ids": [262662172, 123456789, 987654321]
}
```

**Response:**
```json
{
  "success": true,
  "results": [
    {
      "bot_id": 262662172,
      "account_id": 1,
      "success": true,
      "channel": {
        "id": -1002741168040,
        "username": "@dxstest",
        "title": "DXS test channel",
        "type": "channel",
        "is_validated": true,
        "permissions": {
          "can_post_messages": true,
          "can_edit_messages": true,
          "can_send_media_messages": false,
          "can_delete_messages": true,
          "can_pin_messages": false
        }
      }
    },
    {
      "bot_id": 123456789,
      "success": false,
      "error": "Account not found",
      "code": "ACCOUNT_NOT_FOUND"
    }
  ],
  "total_requested": 3,
  "total_processed": 3,
  "requested_by": "giveaway_service",
  "timestamp": "2025-09-14T14:30:00.000Z"
}
```

### **4. Service Health Check**
```
GET /api/service/health
```

**Headers:**
```
X-Service-Token: wk-HIYEuDdfm8lr05cW6Y-sxXkng8y2Ib7U7IVASHMcSCobknXRbhJgp60-fyxKF
```

**Response:**
```json
{
  "success": true,
  "service": "channel-service",
  "status": "healthy",
  "requested_by": "giveaway_service",
  "timestamp": "2025-09-14T14:30:00.000Z",
  "available_endpoints": [
    "GET /api/service/channel/{bot_id}",
    "GET /api/service/channel/{bot_id}/status",
    "POST /api/service/channels/batch",
    "GET /api/service/health"
  ]
}
```

---

## 💻 **Implementation Examples**

### **Node.js/JavaScript Example**
```javascript
const axios = require('axios');

class ChannelServiceClient {
  constructor() {
    this.baseURL = 'https://telegive-channel-production.up.railway.app';
    this.serviceToken = process.env.GIVEAWAY_SERVICE_TOKEN;
  }

  async getChannelConfig(botId) {
    try {
      const response = await axios.get(
        `${this.baseURL}/api/service/channel/${botId}`,
        {
          headers: {
            'X-Service-Token': this.serviceToken,
            'Content-Type': 'application/json'
          }
        }
      );
      return response.data;
    } catch (error) {
      if (error.response?.status === 404) {
        return { success: false, code: 'CHANNEL_NOT_CONFIGURED' };
      }
      throw error;
    }
  }

  async getChannelStatus(botId) {
    try {
      const response = await axios.get(
        `${this.baseURL}/api/service/channel/${botId}/status`,
        {
          headers: {
            'X-Service-Token': this.serviceToken,
            'Content-Type': 'application/json'
          }
        }
      );
      return response.data;
    } catch (error) {
      throw error;
    }
  }

  async getBatchChannelConfigs(botIds) {
    try {
      const response = await axios.post(
        `${this.baseURL}/api/service/channels/batch`,
        { bot_ids: botIds },
        {
          headers: {
            'X-Service-Token': this.serviceToken,
            'Content-Type': 'application/json'
          }
        }
      );
      return response.data;
    } catch (error) {
      throw error;
    }
  }
}

// Usage
const channelService = new ChannelServiceClient();

// Check if bot has channel configured
const config = await channelService.getChannelConfig(262662172);
if (config.success) {
  console.log('Channel configured:', config.channel.username);
} else {
  console.log('Channel not configured');
}

// Get channel status
const status = await channelService.getChannelStatus(262662172);
console.log('Channel status:', status.status);

// Batch lookup
const batchResults = await channelService.getBatchChannelConfigs([262662172, 123456789]);
console.log('Batch results:', batchResults.results);
```

### **Python Example**
```python
import requests
import os

class ChannelServiceClient:
    def __init__(self):
        self.base_url = 'https://telegive-channel-production.up.railway.app'
        self.service_token = os.getenv('GIVEAWAY_SERVICE_TOKEN')
        self.headers = {
            'X-Service-Token': self.service_token,
            'Content-Type': 'application/json'
        }
    
    def get_channel_config(self, bot_id):
        try:
            response = requests.get(
                f'{self.base_url}/api/service/channel/{bot_id}',
                headers=self.headers
            )
            return response.json()
        except requests.exceptions.RequestException as e:
            return {'success': False, 'error': str(e)}
    
    def get_channel_status(self, bot_id):
        try:
            response = requests.get(
                f'{self.base_url}/api/service/channel/{bot_id}/status',
                headers=self.headers
            )
            return response.json()
        except requests.exceptions.RequestException as e:
            return {'success': False, 'error': str(e)}
    
    def get_batch_channel_configs(self, bot_ids):
        try:
            response = requests.post(
                f'{self.base_url}/api/service/channels/batch',
                json={'bot_ids': bot_ids},
                headers=self.headers
            )
            return response.json()
        except requests.exceptions.RequestException as e:
            return {'success': False, 'error': str(e)}

# Usage
channel_service = ChannelServiceClient()

# Check channel config
config = channel_service.get_channel_config(262662172)
if config['success']:
    print(f"Channel configured: {config['channel']['username']}")
else:
    print("Channel not configured")

# Get status
status = channel_service.get_channel_status(262662172)
print(f"Channel status: {status['status']}")
```

---

## 🔒 **Security Features**

### **Token Validation**
- All endpoints require valid `X-Service-Token` header
- Invalid tokens return 403 Forbidden
- Missing tokens return 401 Unauthorized

### **Service Permissions**
- Giveaway Service has `read_channel_config` permission
- Giveaway Service has `verify_channel_status` permission
- Giveaway Service has `check_bot_permissions` permission

### **Request Logging**
- All service requests are logged with service name
- Failed authentication attempts are logged
- Request/response data is logged for debugging

---

## 🧪 **Testing the Integration**

### **Test Service Token**
```bash
curl -X GET "https://telegive-channel-production.up.railway.app/api/service/health" \
  -H "X-Service-Token: wk-HIYEuDdfm8lr05cW6Y-sxXkng8y2Ib7U7IVASHMcSCobknXRbhJgp60-fyxKF" \
  -H "Content-Type: application/json"
```

### **Test Channel Lookup**
```bash
curl -X GET "https://telegive-channel-production.up.railway.app/api/service/channel/262662172" \
  -H "X-Service-Token: wk-HIYEuDdfm8lr05cW6Y-sxXkng8y2Ib7U7IVASHMcSCobknXRbhJgp60-fyxKF" \
  -H "Content-Type: application/json"
```

### **Test Batch Lookup**
```bash
curl -X POST "https://telegive-channel-production.up.railway.app/api/service/channels/batch" \
  -H "X-Service-Token: wk-HIYEuDdfm8lr05cW6Y-sxXkng8y2Ib7U7IVASHMcSCobknXRbhJgp60-fyxKF" \
  -H "Content-Type: application/json" \
  -d '{"bot_ids": [262662172, 999999999]}'
```

---

## 📋 **Error Codes**

| Code | Description | HTTP Status |
|------|-------------|-------------|
| `MISSING_SERVICE_TOKEN` | X-Service-Token header missing | 401 |
| `INVALID_SERVICE_TOKEN` | Service token is invalid | 403 |
| `SERVICE_AUTH_REQUIRED` | Service authentication required | 401 |
| `INSUFFICIENT_PERMISSIONS` | Service lacks required permission | 403 |
| `ACCOUNT_NOT_FOUND` | Bot account not found | 404 |
| `CHANNEL_NOT_CONFIGURED` | Channel not configured for bot | 404 |
| `MISSING_BOT_IDS` | bot_ids array missing in request | 400 |
| `INVALID_BOT_IDS` | bot_ids must be an array | 400 |
| `PROCESSING_ERROR` | Error processing specific bot_id | 500 |
| `INTERNAL_ERROR` | Internal server error | 500 |

---

## 🚀 **Deployment Status**

✅ **Service Token Generated:** `wk-HIYEuDdfm8lr05cW6Y-sxXkng8y2Ib7U7IVASHMcSCobknXRbhJgp60-fyxKF`  
✅ **Authentication Middleware:** Implemented  
✅ **Service API Endpoints:** Created  
✅ **Permissions System:** Configured  
✅ **Error Handling:** Complete  
✅ **Documentation:** Ready  

**The service-to-service integration is ready for use!**

---

**Questions?** Contact the Channel Service team for support.

