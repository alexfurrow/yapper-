from extensions import db
from datetime import datetime
import jwt
import os
import re
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import secrets

class users(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    email_verified = db.Column(db.Boolean, default=False)
    email_verification_token = db.Column(db.String(100), unique=True)
    password_reset_token = db.Column(db.String(100), unique=True)
    password_reset_expires = db.Column(db.DateTime)
    failed_login_attempts = db.Column(db.Integer, default=0)
    account_locked_until = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f"<User {self.username}>"
    
    @staticmethod
    def validate_password(password):
        """Validate password strength"""
        if len(password) < 8:
            return False, "Password must be at least 8 characters long"
        
        if not re.search(r'[A-Z]', password):
            return False, "Password must contain at least one uppercase letter"
        
        if not re.search(r'[a-z]', password):
            return False, "Password must contain at least one lowercase letter"
        
        if not re.search(r'\d', password):
            return False, "Password must contain at least one number"
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            return False, "Password must contain at least one special character"
        
        # Check for common passwords (you can expand this list)
        common_passwords = ['password', '123456', 'qwerty', 'admin', 'letmein']
        if password.lower() in common_passwords:
            return False, "Password is too common"
        
        return True, "Password is valid"
    
    @staticmethod
    def validate_email(email):
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def set_password(self, password):
        """Set password with validation"""
        is_valid, message = self.validate_password(password)
        if not is_valid:
            raise ValueError(message)
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def is_account_locked(self):
        """Check if account is temporarily locked"""
        if self.account_locked_until and datetime.utcnow() < self.account_locked_until:
            return True
        return False
    
    def increment_failed_attempts(self):
        """Increment failed login attempts and lock account if needed"""
        self.failed_login_attempts += 1
        
        # Lock account after 5 failed attempts for 15 minutes
        if self.failed_login_attempts >= 5:
            self.account_locked_until = datetime.utcnow() + timedelta(minutes=15)
        
        db.session.commit()
    
    def reset_failed_attempts(self):
        """Reset failed login attempts on successful login"""
        self.failed_login_attempts = 0
        self.account_locked_until = None
        db.session.commit()
    
    def generate_email_verification_token(self):
        """Generate email verification token"""
        self.email_verification_token = secrets.token_urlsafe(32)
        db.session.commit()
        return self.email_verification_token
    
    def generate_password_reset_token(self):
        """Generate password reset token"""
        self.password_reset_token = secrets.token_urlsafe(32)
        self.password_reset_expires = datetime.utcnow() + timedelta(hours=1)
        db.session.commit()
        return self.password_reset_token
    
    def verify_email_verification_token(self, token):
        """Verify email verification token"""
        if self.email_verification_token == token:
            self.email_verified = True
            self.email_verification_token = None
            db.session.commit()
            return True
        return False
    
    def verify_password_reset_token(self, token):
        """Verify password reset token"""
        if (self.password_reset_token == token and 
            self.password_reset_expires and 
            datetime.utcnow() < self.password_reset_expires):
            return True
        return False
    
    def clear_password_reset_token(self):
        """Clear password reset token after use"""
        self.password_reset_token = None
        self.password_reset_expires = None
        db.session.commit()
        
    def generate_token(self):
        payload = {
            'user_id': self.id,
            'exp': datetime.utcnow() + timedelta(days=1)  # Token expires in 1 day
        }
        return jwt.encode(
            payload,
            os.environ.get('SECRET_KEY', 'dev-secret-key'),
            algorithm='HS256'
        )
    
    @staticmethod
    def verify_token(token):
        try:
            payload = jwt.decode(
                token,
                os.environ.get('SECRET_KEY', 'dev-secret-key'),
                algorithms=['HS256']
            )
            return users.query.get(payload['user_id'])
        except:
            return None

#personal details (state, city, etc)
#user settings (langauge, timezone, etc.)
#notifications
#subscriptions
#user behavior
#account status
#external integrations such as facebook_id, google_id, etc.

#background data 