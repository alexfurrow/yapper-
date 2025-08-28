from flask import request, jsonify
from functools import wraps
from datetime import datetime, timedelta
import redis
import os

# Initialize Redis for rate limiting (fallback to in-memory if Redis not available)
try:
    redis_client = redis.Redis.from_url(os.environ.get('REDIS_URL', 'redis://localhost:6379'))
    redis_client.ping()  # Test connection
    USE_REDIS = True
except:
    USE_REDIS = False
    # In-memory storage for rate limiting (not recommended for production)
    rate_limit_store = {}

def get_client_ip():
    """Get client IP address"""
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0]
    return request.remote_addr

def check_rate_limit(key, max_requests, window_seconds):
    """Check if rate limit is exceeded"""
    current_time = datetime.utcnow()
    
    if USE_REDIS:
        # Use Redis for rate limiting
        current_count = redis_client.get(key)
        if current_count and int(current_count) >= max_requests:
            return False
        
        pipe = redis_client.pipeline()
        pipe.incr(key)
        pipe.expire(key, window_seconds)
        pipe.execute()
        return True
    else:
        # Fallback to in-memory storage
        if key not in rate_limit_store:
            rate_limit_store[key] = {'count': 0, 'reset_time': current_time + timedelta(seconds=window_seconds)}
        
        store = rate_limit_store[key]
        
        # Reset if window has passed
        if current_time > store['reset_time']:
            store['count'] = 0
            store['reset_time'] = current_time + timedelta(seconds=window_seconds)
        
        if store['count'] >= max_requests:
            return False
        
        store['count'] += 1
        return True

def rate_limit(max_requests=5, window_seconds=60, key_func=None):
    """Rate limiting decorator"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if key_func:
                key = f"rate_limit:{key_func()}"
            else:
                key = f"rate_limit:{get_client_ip()}:{f.__name__}"
            
            if not check_rate_limit(key, max_requests, window_seconds):
                return jsonify({
                    'error': 'Rate limit exceeded',
                    'message': f'Too many requests. Please try again in {window_seconds} seconds.'
                }), 429
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator
