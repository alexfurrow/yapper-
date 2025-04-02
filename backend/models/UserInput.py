from extensions import db
from datetime import datetime
from sqlalchemy.dialects.postgresql import ARRAY, FLOAT

class UserInput(db.Model):
    __tablename__ = 'user_inputs'
    
    entry_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    processed = db.Column(db.Text)
    vectors = db.Column(ARRAY(FLOAT))  # Store embeddings as array of floats
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Define relationship with User
    user = db.relationship('User_Table', backref=db.backref('entries', lazy=True))
    
    def to_dict(self):
        return {
            'entry_id': self.entry_id,
            'user_id': self.user_id,
            'content': self.content,
            'processed': self.processed,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        } 