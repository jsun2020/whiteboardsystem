"""
Database Models for Meeting Whiteboard Scribe
Includes user management, whiteboard processing, and user statistics tracking
"""
from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import enum

db = SQLAlchemy()

class ProcessingStatus(enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class ExportFormat(enum.Enum):
    MARKDOWN = "markdown"
    PPTX = "pptx"
    MINDMAP = "mindmap"
    NOTION = "notion"
    CONFLUENCE = "confluence"

# User Management
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(100))
    avatar_url = db.Column(db.String(255))
    is_active = db.Column(db.Boolean, default=True)
    is_admin = db.Column(db.Boolean, default=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    last_login = db.Column(db.DateTime)
    
    # Usage limits
    monthly_upload_limit = db.Column(db.Integer, default=50)  # Number of whiteboards per month
    monthly_export_limit = db.Column(db.Integer, default=100)  # Number of exports per month
    
    # Relationships
    whiteboards = db.relationship('Whiteboard', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    exports = db.relationship('Export', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    user_stats = db.relationship('UserStatistics', backref='user', uselist=False, cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'full_name': self.full_name,
            'avatar_url': self.avatar_url,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }

# Whiteboard Processing
class Whiteboard(db.Model):
    __tablename__ = 'whiteboards'
    
    id = db.Column(db.String(36), primary_key=True)  # UUID
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    
    # File information
    original_filename = db.Column(db.String(255), nullable=False)
    file_size = db.Column(db.Integer)  # bytes
    mime_type = db.Column(db.String(100))
    file_path = db.Column(db.String(500))  # S3/local storage path
    
    # Processing information
    status = db.Column(db.Enum(ProcessingStatus), default=ProcessingStatus.PENDING, nullable=False, index=True)
    processing_started_at = db.Column(db.DateTime)
    processing_completed_at = db.Column(db.DateTime)
    processing_duration = db.Column(db.Float)  # seconds
    error_message = db.Column(db.Text)
    
    # Content analysis results
    extracted_text = db.Column(db.Text)
    structured_content = db.Column(db.JSON)  # Parsed sections, action items, etc.
    confidence_score = db.Column(db.Float)  # OCR/analysis confidence
    language_detected = db.Column(db.String(10))  # 'en', 'zh', etc.
    
    # Metadata
    title = db.Column(db.String(200))  # User-defined or auto-generated title
    description = db.Column(db.Text)
    tags = db.Column(db.JSON)  # List of tags
    is_public = db.Column(db.Boolean, default=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    exports = db.relationship('Export', backref='whiteboard', lazy='dynamic', cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'status': self.status.value,
            'original_filename': self.original_filename,
            'file_size': self.file_size,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'processing_duration': self.processing_duration,
            'confidence_score': self.confidence_score,
            'language_detected': self.language_detected,
            'tags': self.tags
        }

# Export Management
class Export(db.Model):
    __tablename__ = 'exports'
    
    id = db.Column(db.String(36), primary_key=True)  # UUID
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    whiteboard_id = db.Column(db.String(36), db.ForeignKey('whiteboards.id'), nullable=False, index=True)
    
    # Export information
    format = db.Column(db.Enum(ExportFormat), nullable=False, index=True)
    file_path = db.Column(db.String(500))  # Storage path
    file_size = db.Column(db.Integer)  # bytes
    
    # Processing
    status = db.Column(db.Enum(ProcessingStatus), default=ProcessingStatus.PENDING, nullable=False)
    generation_started_at = db.Column(db.DateTime)
    generation_completed_at = db.Column(db.DateTime)
    generation_duration = db.Column(db.Float)  # seconds
    error_message = db.Column(db.Text)
    
    # Metadata
    title = db.Column(db.String(200))
    download_count = db.Column(db.Integer, default=0)
    is_public = db.Column(db.Boolean, default=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    def to_dict(self):
        return {
            'id': self.id,
            'format': self.format.value,
            'title': self.title,
            'status': self.status.value,
            'file_size': self.file_size,
            'download_count': self.download_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'generation_duration': self.generation_duration
        }

# User Statistics Tracking
class UserStatistics(db.Model):
    __tablename__ = 'user_statistics'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True, index=True)
    
    # Upload Statistics
    total_uploads = db.Column(db.Integer, default=0)
    total_upload_size = db.Column(db.BigInteger, default=0)  # bytes
    successful_uploads = db.Column(db.Integer, default=0)
    failed_uploads = db.Column(db.Integer, default=0)
    
    # Processing Statistics
    total_processing_time = db.Column(db.Float, default=0.0)  # seconds
    average_processing_time = db.Column(db.Float, default=0.0)  # seconds
    successful_processes = db.Column(db.Integer, default=0)
    failed_processes = db.Column(db.Integer, default=0)
    
    # Export Statistics
    total_exports = db.Column(db.Integer, default=0)
    exports_by_format = db.Column(db.JSON, default=lambda: {
        'markdown': 0, 'pptx': 0, 'mindmap': 0, 'notion': 0, 'confluence': 0
    })
    total_downloads = db.Column(db.Integer, default=0)
    
    # Usage Patterns
    most_active_day = db.Column(db.String(10))  # 'monday', 'tuesday', etc.
    most_active_hour = db.Column(db.Integer)  # 0-23
    preferred_language = db.Column(db.String(10))  # 'en', 'zh', etc.
    
    # Monthly Statistics (current month)
    monthly_uploads = db.Column(db.Integer, default=0)
    monthly_exports = db.Column(db.Integer, default=0)
    monthly_processing_time = db.Column(db.Float, default=0.0)
    monthly_reset_date = db.Column(db.Date)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    def to_dict(self):
        return {
            'total_uploads': self.total_uploads,
            'successful_uploads': self.successful_uploads,
            'failed_uploads': self.failed_uploads,
            'total_upload_size': self.total_upload_size,
            'total_processing_time': self.total_processing_time,
            'average_processing_time': self.average_processing_time,
            'total_exports': self.total_exports,
            'exports_by_format': self.exports_by_format,
            'total_downloads': self.total_downloads,
            'monthly_uploads': self.monthly_uploads,
            'monthly_exports': self.monthly_exports,
            'monthly_processing_time': self.monthly_processing_time,
            'most_active_day': self.most_active_day,
            'most_active_hour': self.most_active_hour,
            'preferred_language': self.preferred_language
        }

# System-wide Statistics
class SystemStatistics(db.Model):
    __tablename__ = 'system_statistics'
    
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, unique=True, index=True)
    
    # Daily metrics
    total_users = db.Column(db.Integer, default=0)
    new_users = db.Column(db.Integer, default=0)
    active_users = db.Column(db.Integer, default=0)
    
    total_whiteboards = db.Column(db.Integer, default=0)
    new_whiteboards = db.Column(db.Integer, default=0)
    successful_processes = db.Column(db.Integer, default=0)
    failed_processes = db.Column(db.Integer, default=0)
    
    total_exports = db.Column(db.Integer, default=0)
    new_exports = db.Column(db.Integer, default=0)
    total_downloads = db.Column(db.Integer, default=0)
    
    # Performance metrics
    average_processing_time = db.Column(db.Float, default=0.0)
    total_storage_used = db.Column(db.BigInteger, default=0)  # bytes
    
    # Usage patterns
    peak_hour = db.Column(db.Integer)  # Hour with most activity (0-23)
    most_popular_format = db.Column(db.String(20))  # Most exported format
    
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    def to_dict(self):
        return {
            'date': self.date.isoformat(),
            'total_users': self.total_users,
            'new_users': self.new_users,
            'active_users': self.active_users,
            'total_whiteboards': self.total_whiteboards,
            'new_whiteboards': self.new_whiteboards,
            'successful_processes': self.successful_processes,
            'failed_processes': self.failed_processes,
            'total_exports': self.total_exports,
            'new_exports': self.new_exports,
            'total_downloads': self.total_downloads,
            'average_processing_time': self.average_processing_time,
            'total_storage_used': self.total_storage_used,
            'peak_hour': self.peak_hour,
            'most_popular_format': self.most_popular_format
        }