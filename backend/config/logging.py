import re
import logging
import os
import uuid
from logging.handlers import RotatingFileHandler
from flask import g

class RedactSecretsFilter(logging.Filter):
    """Filter to redact sensitive information from log messages"""
    PATTERNS = [
        # JWT tokens (with word boundary anchors)
        re.compile(r"(Bearer\s+)[A-Za-z0-9\-._~+/]+=*\b", re.I),
        re.compile(r"(token['\"]?\s*[:=]\s*['\"]?)[A-Za-z0-9\-._~+/]+=*\b", re.I),
        
        # API Keys (with word boundary anchors)
        re.compile(r"(SUPABASE_[A-Z_]*KEY=)[^\s]+\b", re.I),
        re.compile(r"(OPENAI_API_KEY=)[^\s]+\b", re.I),
        re.compile(r"(API_KEY=)[^\s]+\b", re.I),
        
        # Database URLs (with word boundary anchors)
        re.compile(r"(DATABASE_URL=)[^\s]+\b", re.I),
        re.compile(r"(postgresql://)[^\s]+\b", re.I),
        
        # User content (journal entries) - with word boundary
        re.compile(r"(content['\"]?\s*[:=]\s*['\"]?)[^'\"]{20,}\b", re.I),
        re.compile(r"(processed['\"]?\s*[:=]\s*['\"]?)[^'\"]{20,}\b", re.I),
        
        # Email addresses (with word boundary)
        re.compile(r"\b([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\b"),
        
        # UUIDs (user IDs) - with word boundary
        re.compile(r"\b([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})\b", re.I),
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

class RequestIdFilter(logging.Filter):
    """Filter to add request ID to log records"""
    def filter(self, record):
        record.request_id = getattr(g, "request_id", "-")
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
        '%(asctime)s - %(name)s - %(levelname)s - [%(request_id)s] - %(message)s'
    )
    prod_formatter = logging.Formatter(
        '%(levelname)s: [%(request_id)s] %(message)s'
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
    console_handler.addFilter(RequestIdFilter())
    
    # Add handler to root logger
    root_logger.addHandler(console_handler)
    
    # Add file handler for development only
    if is_dev:
        file_handler = RotatingFileHandler("app.log", maxBytes=2_000_000, backupCount=3)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(dev_formatter)
        file_handler.addFilter(RedactSecretsFilter())
        file_handler.addFilter(RequestIdFilter())
        root_logger.addHandler(file_handler)
    
    # Set specific loggers to reduce noise
    for noisy in ("werkzeug", "urllib3", "botocore", "boto3", "openai", "supabase"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
    
    return root_logger

def get_logger(name):
    """Get a logger instance with redaction already applied"""
    return logging.getLogger(name)
