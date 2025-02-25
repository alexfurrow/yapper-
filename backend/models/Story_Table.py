from extensions import db
from datetime import datetime
import json

class Story_Table(db.Model):
    __tablename__ = 'stories'
    
    # Add a unique story_id as primary key
    story_id = db.Column(db.Integer, primary_key=True)
    # Make entry_id a foreign key that doesn't need to be unique
    entry_id = db.Column(db.Integer, db.ForeignKey('pages.entry_id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Setting Fields
    story = db.Column(db.Text)
    
    def to_dict(self):
        return {
            'story_id': self.story_id,
            'entry_id': self.entry_id,
            'created_at': self.created_at.isoformat(),
            'story': self.story
        }
