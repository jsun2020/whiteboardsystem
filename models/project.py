from datetime import datetime
from database import db
import uuid

class Project(db.Model):
    __tablename__ = 'projects'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = db.Column(db.String(200), nullable=True)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=True)
    status = db.Column(db.String(20), default='draft')  # draft, processing, completed, error
    share_token = db.Column(db.String(36), unique=True, nullable=True)
    
    # Relationships
    whiteboards = db.relationship('Whiteboard', backref='project', lazy=True, cascade='all, delete-orphan')
    exports = db.relationship('Export', backref='project', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'status': self.status,
            'whiteboard_count': len(self.whiteboards),
            'export_count': len(self.exports),
            'share_token': self.share_token
        }
    
    def create_share_token(self):
        self.share_token = str(uuid.uuid4())
        db.session.commit()
        return self.share_token
    
    @classmethod
    def find_by_share_token(cls, token):
        return cls.query.filter_by(share_token=token).first()