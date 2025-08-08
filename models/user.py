from datetime import datetime
from database import db
import uuid

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = db.Column(db.String(120), unique=True, nullable=True)
    username = db.Column(db.String(80), unique=True, nullable=True)
    display_name = db.Column(db.String(120), nullable=True)
    
    # Session tracking
    session_token = db.Column(db.String(36), unique=True, nullable=True)
    last_active = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Usage tracking
    projects_created = db.Column(db.Integer, default=0)
    images_processed = db.Column(db.Integer, default=0)
    exports_generated = db.Column(db.Integer, default=0)
    
    # Settings
    preferred_language = db.Column(db.String(10), default='en')
    theme_preference = db.Column(db.String(10), default='light')
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    projects = db.relationship('Project', backref='user', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'username': self.username,
            'display_name': self.display_name,
            'last_active': self.last_active.isoformat() if self.last_active else None,
            'projects_created': self.projects_created,
            'images_processed': self.images_processed,
            'exports_generated': self.exports_generated,
            'preferred_language': self.preferred_language,
            'theme_preference': self.theme_preference,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def update_activity(self):
        self.last_active = datetime.utcnow()
        db.session.commit()
    
    def increment_usage(self, metric):
        if metric == 'projects':
            self.projects_created += 1
        elif metric == 'images':
            self.images_processed += 1
        elif metric == 'exports':
            self.exports_generated += 1
        db.session.commit()
    
    @classmethod
    def create_anonymous_user(cls):
        user = cls()
        user.session_token = str(uuid.uuid4())
        db.session.add(user)
        db.session.commit()
        return user