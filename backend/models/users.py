from extensions import db
from datetime import datetime
import jwt
import os
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta

class users(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    # email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    created_at = db.Column(db.DateTime, default=datetime.utcnow) 
    # updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    # is_active = db.Column(db.Boolean, default=True)
    # is_verified = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f"<User {self.username}>"
        
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
        
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