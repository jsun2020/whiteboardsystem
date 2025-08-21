from datetime import datetime
from database import db
import uuid
import hashlib
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = db.Column(db.String(120), unique=True, nullable=True)
    username = db.Column(db.String(80), unique=True, nullable=True)
    password_hash = db.Column(db.String(255), nullable=True)
    display_name = db.Column(db.String(120), nullable=True)
    
    # Account status
    is_admin = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    email_verified = db.Column(db.Boolean, default=False)
    
    # Session tracking
    session_token = db.Column(db.String(36), unique=True, nullable=True)
    last_active = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Usage tracking
    projects_created = db.Column(db.Integer, default=0)
    images_processed = db.Column(db.Integer, default=0)
    exports_generated = db.Column(db.Integer, default=0)
    free_uses_count = db.Column(db.Integer, default=0)
    
    # Payment and subscription
    subscription_type = db.Column(db.String(20), default='free')  # free, monthly, semi_annual, annual
    subscription_expires_at = db.Column(db.DateTime, nullable=True)
    payment_status = db.Column(db.String(20), default='none')  # none, pending, active, expired
    custom_api_key = db.Column(db.Text, nullable=True)  # Encrypted custom API key
    
    # Settings
    preferred_language = db.Column(db.String(10), default='en')
    theme_preference = db.Column(db.String(10), default='light')
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    projects = db.relationship('Project', backref='user', lazy=True)
    
    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check if provided password matches hash"""
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)
    
    def can_use_service(self):
        """Check if user can use the service based on subscription or free uses"""
        if self.is_admin:
            return True
        
        # Check if user has active subscription
        if self.subscription_expires_at and self.subscription_expires_at > datetime.utcnow():
            return True
            
        # Check if user has custom API key
        if self.custom_api_key:
            return True
            
        # Check free uses (10 free uses for new users)
        return self.free_uses_count < 10
    
    def increment_usage(self, metric):
        """Increment usage counters"""
        if metric == 'projects':
            self.projects_created += 1
        elif metric == 'images':
            self.images_processed += 1
        elif metric == 'exports':
            self.exports_generated += 1
        
        # Increment free uses if not subscribed and no custom API
        if (not self.subscription_expires_at or self.subscription_expires_at <= datetime.utcnow()) and not self.custom_api_key:
            self.free_uses_count += 1
            
        db.session.commit()
    
    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'username': self.username,
            'display_name': self.display_name,
            'is_admin': self.is_admin,
            'is_active': self.is_active,
            'last_active': self.last_active.isoformat() if self.last_active else None,
            'projects_created': self.projects_created,
            'images_processed': self.images_processed,
            'exports_generated': self.exports_generated,
            'free_uses_count': self.free_uses_count,
            'subscription_type': self.subscription_type,
            'subscription_expires_at': self.subscription_expires_at.isoformat() if self.subscription_expires_at else None,
            'payment_status': self.payment_status,
            'can_use_service': self.can_use_service(),
            'preferred_language': self.preferred_language,
            'theme_preference': self.theme_preference,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def update_activity(self):
        self.last_active = datetime.utcnow()
        db.session.commit()
    
    @classmethod
    def create_anonymous_user(cls):
        user = cls()
        user.session_token = str(uuid.uuid4())
        db.session.add(user)
        db.session.commit()
        return user