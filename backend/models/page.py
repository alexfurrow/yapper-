from extensions import db
from datetime import datetime

class Page(db.Model):
    __tablename__ = 'pages'
    
    entry_id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    processed = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'entry_id': self.entry_id,
            'content': self.content,
            'processed': self.processed,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        } 