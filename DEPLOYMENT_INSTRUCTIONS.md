# Deployment Instructions - Channel Management Service

## 🚀 **Deployment to Railway**

This service is configured for automatic deployment to Railway. Follow these steps to deploy the latest changes:

### **1. Push to GitHub**

Commit and push all changes to the main branch of your GitHub repository.

```bash
git add .
git commit -m "Fix: Use bot_id for account lookup and direct DB access"
git push origin main
```

### **2. Railway Automatic Deployment**

Railway is configured to automatically build and deploy the service when changes are pushed to the `main` branch. You can monitor the deployment progress in your Railway project dashboard.

### **3. Environment Variables**

Ensure the following environment variables are set in your Railway project:

- `DATABASE_URL`: The connection string for your shared PostgreSQL database.
- `SECRET_KEY`: A unique secret key for Flask sessions.
- `FLASK_ENV`: Set to `production`.
- `SERVICE_NAME`: `channel-service`
- `SERVICE_PORT`: `8002`

**Note:** The `TELEGIVE_AUTH_URL` is no longer required as the service now uses direct database access.

## 🧪 **Post-Deployment Verification**

After deployment, verify that the service is running correctly:

### **1. Check Service Health**

```bash
cURL https://telegive-channel-production.up.railway.app/health
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

### **2. Test Account Lookup with `bot_id`**

Test the fixed account lookup functionality with a known `bot_id`:

```bash
# Test with bot_id 262662172
cURL https://telegive-channel-production.up.railway.app/api/accounts/262662172/channel
```

**Expected Response (if no channel is configured):**
```json
{
  "success": false,
  "error": "No channel configuration found for bot_id 262662172",
  "code": "CHANNEL_NOT_CONFIGURED"
}
```

This confirms that the service is correctly using the `bot_id` for lookups.

## 롤백 **Rollback Plan**

If the deployment introduces issues, you can roll back to a previous version through the Railway dashboard. Select a previous successful deployment and redeploy it.

---

**Last Updated:** September 13, 2025

025

