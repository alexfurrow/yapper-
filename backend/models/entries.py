from extensions import db
from datetime import datetime
import json
from sqlalchemy.dialects.postgresql import ARRAY, FLOAT

class entries(db.Model):
    __tablename__ = 'entries'
    
    entry_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String, nullable=True)  # Supabase user ID (UUID string)
    user_entry_id = db.Column(db.Integer, nullable=True)  # User-specific entry number
    content = db.Column(db.Text, nullable=False)
    processed = db.Column(db.Text)
    vectors = db.Column(ARRAY(FLOAT))  # Store embeddings as array of floats
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Note: User relationship handled through Supabase auth
    # user_id field stores the Supabase user ID as a string
    
    def to_dict(self):
        return {
            'entry_id': self.entry_id,
            'user_entry_id': self.user_entry_id,  # Use this for display
            'user_id': self.user_id,
            'content': self.content,
            'processed': self.processed,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        } 