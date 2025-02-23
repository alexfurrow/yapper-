from extensions import db
from datetime import datetime
import json

class Story_Table(db.Model):
    __tablename__ = 'stories'
    
    # Primary Key Fields
    entry_id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Setting Fields
    story = db.Column(db.Text)
    
    def to_dict(self):
        return {
            'entry_id': self.entry_id,
            'created_at': self.created_at.isoformat(),
            'story': self.story
        }
