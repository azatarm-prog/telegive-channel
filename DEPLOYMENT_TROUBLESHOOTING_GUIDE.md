# Telegive Channel Management Service - Deployment Troubleshooting Guide

This document contains all deployment and build errors encountered during the development and deployment of the Channel Management Service, along with their solutions.

## Table of Contents

1. [Build Errors](#build-errors)
2. [Deployment Errors](#deployment-errors)
3. [Database Connection Errors](#database-connection-errors)
4. [Service Integration Errors](#service-integration-errors)
5. [Runtime Errors](#runtime-errors)
6. [Environment Configuration Issues](#environment-configuration-issues)
7. [Port and Networking Issues](#port-and-networking-issues)
8. [Prevention Best Practices](#prevention-best-practices)

---

## Build Errors

### 1. Python Package Compatibility Error

**Error:**
```
error: 'PyLongObject' {aka 'struct _longobject'} has no member named 'ob_digit'
Building wheel for aiohttp (pyproject.toml) ... error
```

**Root Cause:**
- aiohttp 3.8.5 is incompatible with Python 3.12
- Uses deprecated Python C API features removed in Python 3.12

**Solution:**
```bash
# Update requirements.txt
aiohttp==3.9.5  # Instead of aiohttp==3.8.5
```

**Prevention:**
- Always check package compatibility with Python version
- Use latest stable versions of packages
- Test builds locally before deployment

### 2. Missing Dependencies

**Error:**
```
ModuleNotFoundError: No module named 'package_name'
```

**Solution:**
```bash
# Add missing package to requirements.txt
pip freeze > requirements.txt  # Capture all dependencies
```

**Prevention:**
- Maintain accurate requirements.txt
- Use virtual environments for development
- Test with clean environment before deployment

---

## Deployment Errors

### 1. Application Failed to Respond (502 Bad Gateway)

**Error:**
```
502 Bad Gateway
Application failed to respond
```

**Root Cause:**
- Service not listening on correct port
- Application crashed during startup
- Port mismatch between service and Railway configuration

**Solution:**
```bash
# Check logs for actual error
railway logs

# Ensure correct port configuration
PORT=8080  # Match Railway domain configuration
```

**Diagnosis Steps:**
1. Check Railway deployment logs
2. Verify port configuration
3. Test health endpoint
4. Check environment variables

### 2. Build Timeout

**Error:**
```
Build timed out after 10 minutes
```

**Solution:**
```bash
# Optimize requirements.txt - remove unnecessary packages
# Use specific versions to avoid resolution conflicts
# Consider using Docker for faster builds
```

### 3. Memory Limit Exceeded

**Error:**
```
Process killed due to memory limit
```

**Solution:**
```bash
# Upgrade Railway plan for more memory
# Optimize application memory usage
# Use gunicorn with appropriate worker count
```

---

## Database Connection Errors

### 1. Database Connection Refused

**Error:**
```
psycopg2.OperationalError: could not connect to server: Connection refused
```

**Root Cause:**
- Incorrect DATABASE_URL format
- Database service not connected in Railway
- Network connectivity issues

**Solution:**
```bash
# Correct DATABASE_URL format
DATABASE_URL=${{Postgres.DATABASE_PUBLIC_URL}}

# Or with SSL mode
DATABASE_URL=${{Postgres.DATABASE_PUBLIC_URL}}?sslmode=require
```

**Railway Connection Steps:**
1. Go to service Variables tab
2. Connect to Postgres service
3. Verify solid connection line (not dashed)
4. Restart service

### 2. SSL Connection Error

**Error:**
```
SSL SYSCALL error: EOF detected
psycopg2.OperationalError: SSL connection has been closed unexpectedly
```

**Root Cause:**
- SSL configuration mismatch
- Network interruption during SSL handshake
- Database connection pool issues

**Solutions:**
```bash
# Try different SSL modes
DATABASE_URL=${{Postgres.DATABASE_PUBLIC_URL}}?sslmode=prefer
DATABASE_URL=${{Postgres.DATABASE_PUBLIC_URL}}?sslmode=require
DATABASE_URL=${{Postgres.DATABASE_PUBLIC_URL}}?sslmode=disable

# Add connection pool settings
DATABASE_URL=${{Postgres.DATABASE_PUBLIC_URL}}?sslmode=require&pool_size=5&max_overflow=10
```

### 3. Database Tables Not Created

**Error:**
```
relation "table_name" does not exist
```

**Solution:**
```python
# Ensure database initialization in app.py
with app.app_context():
    db.create_all()
    logger.info("Database tables created successfully")
```

### 4. Health Check Shows Database Disconnected

**Error:**
```json
{"database": "disconnected", "status": "unhealthy"}
```

**Root Cause:**
- Health check using incorrect SQL syntax
- Database connection not properly tested

**Solution:**
```python
# Fix health check in routes/health.py
try:
    result = db.session.execute(db.text('SELECT 1')).fetchone()
    if result is None:
        db_status = "disconnected"
except Exception as e:
    db_status = "disconnected"
```

---

## Service Integration Errors

### 1. Auth Service Connection Failed

**Error:**
```
requests.exceptions.ConnectionError: Failed to establish a new connection
```

**Root Cause:**
- Incorrect auth service URL
- Auth service not running
- Network connectivity issues

**Solution:**
```bash
# Verify auth service URL
TELEGIVE_AUTH_URL=https://web-production-ddd7e.up.railway.app

# Test auth service health
curl https://web-production-ddd7e.up.railway.app/health
```

### 2. Auth Service Timeout

**Error:**
```
requests.exceptions.Timeout: Request timed out
```

**Solution:**
```python
# Increase timeout in get_bot_credentials()
response = requests.get(url, timeout=30)  # Increase from 10 to 30 seconds

# Add retry logic
import time
for attempt in range(3):
    try:
        response = requests.get(url, timeout=10)
        break
    except requests.exceptions.Timeout:
        if attempt < 2:
            time.sleep(2 ** attempt)  # Exponential backoff
        else:
            raise
```

### 3. Invalid Bot Token from Auth Service

**Error:**
```json
{"error": "Invalid bot token", "error_code": "INVALID_TOKEN"}
```

**Root Cause:**
- Bot token not properly decrypted
- Account not found in auth service
- Token corruption during transmission

**Solution:**
```python
# Add validation in get_bot_credentials()
if not bot_token or not bot_token.startswith(str(bot_id)):
    raise Exception("Invalid bot token format")

# Verify token format
import re
if not re.match(r'^\d+:[A-Za-z0-9_-]+$', bot_token):
    raise Exception("Bot token format validation failed")
```

---

## Runtime Errors

### 1. Telegram API Rate Limiting

**Error:**
```
HTTP 429: Too Many Requests
```

**Solution:**
```python
# Add rate limiting and retry logic
import time
from functools import wraps

def rate_limit_retry(max_retries=3):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except requests.exceptions.HTTPError as e:
                    if e.response.status_code == 429:
                        retry_after = int(e.response.headers.get('Retry-After', 60))
                        time.sleep(retry_after)
                    else:
                        raise
            raise Exception("Max retries exceeded")
        return wrapper
    return decorator
```

### 2. Channel Not Found Error

**Error:**
```
HTTP 400: Channel not found or not accessible
```

**Root Cause:**
- Channel username doesn't exist
- Bot not added to channel
- Channel is private and bot lacks access

**Solution:**
```python
# Improve error handling in channel validation
def validate_channel_access(bot_token, channel_username):
    try:
        # Try to get channel info
        response = requests.get(f"https://api.telegram.org/bot{bot_token}/getChat", 
                              params={"chat_id": f"@{channel_username}"})
        
        if response.status_code == 400:
            return {"error": "Channel not found or bot not added to channel"}
        elif response.status_code == 403:
            return {"error": "Bot lacks permission to access channel"}
        
        return {"success": True, "data": response.json()}
    except Exception as e:
        return {"error": f"Channel validation failed: {str(e)}"}
```

### 3. Memory Leaks in Long-Running Processes

**Error:**
```
Process killed due to memory usage
```

**Solution:**
```python
# Proper session management
import requests
from contextlib import contextmanager

@contextmanager
def http_session():
    session = requests.Session()
    try:
        yield session
    finally:
        session.close()

# Use in functions
def get_bot_credentials(account_id):
    with http_session() as session:
        response = session.get(url)
        return response.json()
```

---

## Environment Configuration Issues

### 1. Missing Environment Variables

**Error:**
```
KeyError: 'REQUIRED_ENV_VAR'
```

**Solution:**
```python
# Use environment variables with defaults
import os

DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///default.db')
SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')

# Validate required variables
required_vars = ['DATABASE_URL', 'SECRET_KEY', 'TELEGIVE_AUTH_URL']
missing_vars = [var for var in required_vars if not os.getenv(var)]
if missing_vars:
    raise Exception(f"Missing required environment variables: {missing_vars}")
```

### 2. Incorrect Variable Format

**Error:**
```
Invalid DATABASE_URL format
```

**Common Issues:**
```bash
# Wrong - has quotes
DATABASE_URL="${{Postgres.DATABASE_PUBLIC_URL}}"

# Correct - no quotes
DATABASE_URL=${{Postgres.DATABASE_PUBLIC_URL}}
```

### 3. Environment Variable Not Updated

**Root Cause:**
- Service not restarted after variable change
- Variable cached in application

**Solution:**
1. Update variable in Railway dashboard
2. Wait for automatic restart (1-2 minutes)
3. Or manually restart service
4. Verify with health check

---

## Port and Networking Issues

### 1. Port Mismatch

**Error:**
```
502 Bad Gateway - Application failed to respond
```

**Root Cause:**
- Railway domain configured for different port than application

**Solution:**
```bash
# Check what port your app is running on (from logs)
[INFO] Listening at: http://0.0.0.0:8080

# Update Railway domain to match
# Delete current domain, create new one with port 8080
```

### 2. CORS Issues

**Error:**
```
Access to fetch at 'url' from origin 'origin' has been blocked by CORS policy
```

**Solution:**
```python
# Enable CORS in app.py
from flask_cors import CORS

app = Flask(__name__)
CORS(app, origins="*")  # Or specify allowed origins
```

### 3. Service-to-Service Communication

**Error:**
```
Connection refused when calling other services
```

**Solution:**
```bash
# Use correct service URLs
TELEGIVE_AUTH_URL=https://web-production-ddd7e.up.railway.app
TELEGIVE_GIVEAWAY_URL=https://telegive-service.railway.app

# Not internal URLs like:
# telegive-auth.railway.internal (only works within Railway network)
```

---

## Prevention Best Practices

### 1. Development Environment

```bash
# Use virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Test locally before deployment
python app.py
```

### 2. Environment Variables Management

```bash
# Create .env.example with all required variables
DATABASE_URL=postgresql://user:pass@host:port/db
SECRET_KEY=your-secret-key
TELEGIVE_AUTH_URL=https://your-auth-service.com

# Use python-dotenv for local development
pip install python-dotenv
```

### 3. Health Checks and Monitoring

```python
# Comprehensive health check
@app.route('/health')
def health_check():
    checks = {
        'database': check_database(),
        'auth_service': check_auth_service(),
        'telegram_api': check_telegram_api()
    }
    
    overall_status = 'healthy' if all(checks.values()) else 'unhealthy'
    
    return jsonify({
        'status': overall_status,
        'checks': checks,
        'timestamp': datetime.utcnow().isoformat()
    })
```

### 4. Logging and Error Tracking

```python
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Log important events
logger.info(f"Successfully retrieved bot credentials for account {account_id}")
logger.error(f"Failed to connect to auth service: {str(e)}")
```

### 5. Testing Strategy

```python
# Unit tests
import pytest

def test_get_bot_credentials():
    # Mock auth service response
    with patch('requests.get') as mock_get:
        mock_get.return_value.json.return_value = {
            'success': True,
            'account': {'bot_id': 123}
        }
        
        result = get_bot_credentials(1)
        assert result['bot_id'] == 123

# Integration tests
def test_health_endpoint():
    response = client.get('/health')
    assert response.status_code == 200
    assert response.json['status'] in ['healthy', 'unhealthy']
```

### 6. Deployment Checklist

- [ ] All environment variables set correctly
- [ ] Database connection working
- [ ] Health endpoint responding
- [ ] External service integrations tested
- [ ] Error handling implemented
- [ ] Logging configured
- [ ] CORS enabled if needed
- [ ] Rate limiting considered
- [ ] Security headers added
- [ ] Documentation updated

---

## Quick Diagnostic Commands

### Check Service Health
```bash
curl https://telegive-channel-production.up.railway.app/health
```

### Test Database Connection
```bash
curl https://telegive-channel-production.up.railway.app/api/channels/list
```

### Test Auth Integration
```bash
curl -X GET https://telegive-channel-production.up.railway.app/api/channels/validate/1
```

### Check Railway Logs
```bash
railway logs --service telegive-channel
```

### Test Environment Variables
```bash
# In Railway console or logs, check if variables are loaded
echo $DATABASE_URL
echo $TELEGIVE_AUTH_URL
```

---

## Emergency Recovery Steps

### 1. Service Not Responding
1. Check Railway deployment status
2. Review recent logs for errors
3. Verify environment variables
4. Restart service manually
5. Check database connection

### 2. Database Connection Lost
1. Verify DATABASE_URL format
2. Check Postgres service status
3. Test connection from Railway console
4. Restart both services if needed

### 3. Auth Service Integration Broken
1. Test auth service health directly
2. Verify TELEGIVE_AUTH_URL
3. Check network connectivity
4. Review auth service logs
5. Test with curl commands

### 4. Complete Service Failure
1. Check Railway service status
2. Review all environment variables
3. Compare with working service configuration
4. Redeploy from known good commit
5. Contact Railway support if infrastructure issue

---

## Contact and Support

- **Repository**: https://github.com/azatarm-prog/telegive-channel
- **Railway Dashboard**: Check service logs and metrics
- **Health Endpoint**: https://telegive-channel-production.up.railway.app/health

Remember to always check the health endpoint first when diagnosing issues, as it provides comprehensive status information about all service dependencies.

