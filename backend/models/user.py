from extensions import db
from datetime import datetime

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    # email = db.Column(db.String(120), unique=True, nullable=False)
    # password_hash = db.Column(db.String(128))
    # created_at = db.Column(db.DateTime, default=datetime.utcnow) 
    # updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    # is_active = db.Column(db.Boolean, default=True)
    # is_verified = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f"<User {self.username}>"

#personal details (state, city, etc)
#user settings (langauge, timezone, etc.)
#notifications
#subscriptions
#user behavior
#account status
#external integrations such as facebook_id, google_id, etc.





#background data
