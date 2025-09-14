# 🔗 Service-to-Service Integration Guide (Updated)

## Channel Service ↔ Giveaway Service

This guide explains how the Giveaway Service can securely access Channel Service APIs to check channel configurations and status.

---

## 🔑 **Authentication (Updated)**

### **Service Token**
```
Token: ch4nn3l_s3rv1c3_t0k3n_2025_s3cur3_r4nd0m_str1ng
Header: X-Service-Token
```

### **Environment Variable for Giveaway Service**
```bash
CHANNEL_SERVICE_TOKEN=ch4nn3l_s3rv1c3_t0k3n_2025_s3cur3_r4nd0m_str1ng
```

---

## 🛠️ **Available Endpoints**

### **1. Get Channel Configuration**
```
GET /api/service/channel/{bot_id}
```

**Headers:**
```
X-Service-Token: ch4nn3l_s3rv1c3_t0k3n_2025_s3cur3_r4nd0m_str1ng
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

### **2. Get Channel Status**
```
GET /api/service/channel/{bot_id}/status
```

### **3. Batch Channel Lookup**
```
POST /api/service/channels/batch
```

### **4. Service Health Check**
```
GET /api/service/health
```

---

## 💻 **Implementation Examples (Updated)**

### **Node.js/JavaScript Example**
```javascript
const axios = require('axios');

class ChannelServiceClient {
  constructor() {
    this.baseURL = 'https://telegive-channel-production.up.railway.app';
    this.serviceToken = process.env.CHANNEL_SERVICE_TOKEN; // Updated
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
```

### **Python Example**
```python
import requests
import os

class ChannelServiceClient:
    def __init__(self):
        self.base_url = 'https://telegive-channel-production.up.railway.app'
        self.service_token = os.getenv('CHANNEL_SERVICE_TOKEN')  # Updated
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

# Usage
channel_service = ChannelServiceClient()
config = channel_service.get_channel_config(262662172)
```

---

## 🧪 **Testing the Integration (Updated)**

### **Test Service Token**
```bash
curl -X GET "https://telegive-channel-production.up.railway.app/api/service/health" \
  -H "X-Service-Token: ch4nn3l_s3rv1c3_t0k3n_2025_s3cur3_r4nd0m_str1ng" \
  -H "Content-Type: application/json"
```

### **Test Channel Lookup**
```bash
curl -X GET "https://telegive-channel-production.up.railway.app/api/service/channel/262662172" \
  -H "X-Service-Token: ch4nn3l_s3rv1c3_t0k3n_2025_s3cur3_r4nd0m_str1ng" \
  -H "Content-Type: application/json"
```

### **Test Batch Lookup**
```bash
curl -X POST "https://telegive-channel-production.up.railway.app/api/service/channels/batch" \
  -H "X-Service-Token: ch4nn3l_s3rv1c3_t0k3n_2025_s3cur3_r4nd0m_str1ng" \
  -H "Content-Type: application/json" \
  -d '{"bot_ids": [262662172, 999999999]}'
```

---

## 🚀 **Deployment Status (Updated)**

✅ **Service Token Updated:** `ch4nn3l_s3rv1c3_t0k3n_2025_s3cur3_r4nd0m_str1ng`  
✅ **Environment Variable:** `CHANNEL_SERVICE_TOKEN`  
✅ **Authentication Middleware:** Updated  
✅ **Service API Endpoints:** Ready  
✅ **Permissions System:** Configured  
✅ **Error Handling:** Complete  
✅ **Documentation:** Updated  

**The service-to-service integration is ready with the updated token!**

---

## 📋 **Summary of Changes**

**Previous Token:** `wk-HIYEuDdfm8lr05cW6Y-sxXkng8y2Ib7U7IVASHMcSCobknXRbhJgp60-fyxKF`  
**New Token:** `ch4nn3l_s3rv1c3_t0k3n_2025_s3cur3_r4nd0m_str1ng`  

**Previous Environment Variable:** `GIVEAWAY_SERVICE_TOKEN`  
**New Environment Variable:** `CHANNEL_SERVICE_TOKEN`  

**All endpoints and functionality remain the same - only the token has changed.**

