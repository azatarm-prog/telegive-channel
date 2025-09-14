"""
Service-to-service authentication utilities
Handles authentication between Telegive services
"""

import os
import logging
from functools import wraps
from flask import request, jsonify

logger = logging.getLogger(__name__)

# Service tokens for inter-service communication
VALID_SERVICE_TOKENS = {
    'giveaway_service': os.getenv('CHANNEL_SERVICE_TOKEN', 'ch4nn3l_s3rv1c3_t0k3n_2025_s3cur3_r4nd0m_str1ng'),
    'auth_service': os.getenv('AUTH_SERVICE_TOKEN', 'ch4nn3l_s3rv1c3_t0k3n_2025_s3cur3_r4nd0m_str1ng')
}

def require_service_token(f):
    """
    Decorator to require valid service token for API endpoints
    
    Usage:
        @require_service_token
        def protected_endpoint():
            return jsonify({'message': 'Access granted'})
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get token from header
        service_token = request.headers.get('X-Service-Token')
        
        if not service_token:
            logger.warning("Service token missing in request")
            return jsonify({
                'success': False,
                'error': 'Service token required',
                'code': 'MISSING_SERVICE_TOKEN'
            }), 401
        
        # Validate token
        if service_token not in VALID_SERVICE_TOKENS.values():
            logger.warning(f"Invalid service token provided: {service_token[:10]}...")
            return jsonify({
                'success': False,
                'error': 'Invalid service token',
                'code': 'INVALID_SERVICE_TOKEN'
            }), 403
        
        # Identify which service is making the request
        service_name = None
        for name, token in VALID_SERVICE_TOKENS.items():
            if token == service_token:
                service_name = name
                break
        
        logger.info(f"Service authenticated: {service_name}")
        
        # Add service info to request context
        request.service_name = service_name
        request.service_token = service_token
        
        return f(*args, **kwargs)
    
    return decorated_function

def get_requesting_service():
    """
    Get the name of the service making the current request
    
    Returns:
        str: Service name or None if not authenticated
    """
    return getattr(request, 'service_name', None)

def is_service_request():
    """
    Check if the current request is from an authenticated service
    
    Returns:
        bool: True if request is from authenticated service
    """
    return hasattr(request, 'service_name') and request.service_name is not None

def validate_service_token(token):
    """
    Validate a service token
    
    Args:
        token (str): Service token to validate
    
    Returns:
        tuple: (is_valid, service_name)
    """
    if not token:
        return False, None
    
    for service_name, valid_token in VALID_SERVICE_TOKENS.items():
        if token == valid_token:
            return True, service_name
    
    return False, None

def create_service_response(data, service_name=None):
    """
    Create a standardized response for service requests
    
    Args:
        data: Response data
        service_name: Name of requesting service (optional)
    
    Returns:
        dict: Formatted response
    """
    response = {
        'success': True,
        'data': data,
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    }
    
    if service_name:
        response['requested_by'] = service_name
    
    return response

# Service endpoint permissions
SERVICE_PERMISSIONS = {
    'giveaway_service': [
        'read_channel_config',
        'verify_channel_status',
        'check_bot_permissions'
    ],
    'auth_service': [
        'read_account_info',
        'verify_account_status'
    ]
}

def require_service_permission(permission):
    """
    Decorator to require specific service permission
    
    Args:
        permission (str): Required permission
    
    Usage:
        @require_service_permission('read_channel_config')
        def get_channel_config():
            return jsonify({'config': 'data'})
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            service_name = get_requesting_service()
            
            if not service_name:
                return jsonify({
                    'success': False,
                    'error': 'Service authentication required',
                    'code': 'SERVICE_AUTH_REQUIRED'
                }), 401
            
            service_perms = SERVICE_PERMISSIONS.get(service_name, [])
            
            if permission not in service_perms:
                logger.warning(f"Service {service_name} lacks permission: {permission}")
                return jsonify({
                    'success': False,
                    'error': f'Service lacks required permission: {permission}',
                    'code': 'INSUFFICIENT_PERMISSIONS'
                }), 403
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator

