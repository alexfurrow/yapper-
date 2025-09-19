import re
import logging
import os
from logging.handlers import RotatingFileHandler

class RedactSecretsFilter(logging.Filter):
    """Filter to redact sensitive information from log messages"""
    PATTERNS = [
        # JWT tokens
        re.compile(r"(Bearer\s+)[A-Za-z0-9\-._~+/]+=*", re.I),
        re.compile(r"(token['\"]?\s*[:=]\s*['\"]?)[A-Za-z0-9\-._~+/]+=*", re.I),
        
        # API Keys
        re.compile(r"(SUPABASE_[A-Z_]*KEY=)[^\s]+", re.I),
        re.compile(r"(OPENAI_API_KEY=)[^\s]+", re.I),
        re.compile(r"(API_KEY=)[^\s]+", re.I),
        
        # Database URLs
        re.compile(r"(DATABASE_URL=)[^\s]+", re.I),
        re.compile(r"(postgresql://)[^\s]+", re.I),
        
        # User content (journal entries)
        re.compile(r"(content['\"]?\s*[:=]\s*['\"]?)[^'\"]{20,}", re.I),
        re.compile(r"(processed['\"]?\s*[:=]\s*['\"]?)[^'\"]{20,}", re.I),
        
        # Email addresses
        re.compile(r"([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})"),
        
        # UUIDs (user IDs)
        re.compile(r"([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})", re.I),
    ]
    
    def filter(self, record):
        """Apply redaction patterns to log record"""
        msg = record.getMessage()
        for pattern in self.PATTERNS:
            msg = pattern.sub(r"\1[REDACTED]", msg)
        
        # Update the record
        record.msg = msg
        record.args = ()
        return True

def setup_logging():
    """Configure logging with redaction filter"""
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # Clear any existing handlers
    root_logger.handlers.clear()
    
    # Create formatters
    dev_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    prod_formatter = logging.Formatter(
        '%(levelname)s: %(message)s'
    )
    
    # Determine if we're in development or production
    is_dev = os.environ.get('FLASK_ENV', 'development') == 'development'
    
    # Console handler with redaction (works for both dev and production)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    if is_dev:
        # Development: more detailed formatting
        console_handler.setFormatter(dev_formatter)
    else:
        # Production: simpler formatting for platform logs
        console_handler.setFormatter(prod_formatter)
    
    console_handler.addFilter(RedactSecretsFilter())
    
    # Add handler to root logger
    root_logger.addHandler(console_handler)
    
    # Set specific loggers to reduce noise
    logging.getLogger('werkzeug').setLevel(logging.WARNING)  # Reduce Flask noise
    logging.getLogger('urllib3').setLevel(logging.WARNING)    # Reduce HTTP noise
    
    return root_logger

def get_logger(name):
    """Get a logger instance with redaction already applied"""
    return logging.getLogger(name)
