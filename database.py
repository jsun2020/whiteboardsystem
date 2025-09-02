from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime, timezone
import json

db = SQLAlchemy()
migrate = Migrate()

class UserStatistics(db.Model):
    __tablename__ = 'user_statistics'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False, index=True)
    
    # Daily statistics
    date = db.Column(db.Date, nullable=False, index=True)
    
    # Usage counts for the day
    projects_created_today = db.Column(db.Integer, default=0)
    images_uploaded_today = db.Column(db.Integer, default=0)
    images_processed_today = db.Column(db.Integer, default=0)
    exports_generated_today = db.Column(db.Integer, default=0)
    
    # Export type breakdown (JSON)
    export_types_used = db.Column(db.Text, nullable=True)  # JSON: {"markdown": 2, "pptx": 1}
    
    # Time spent (in minutes)
    session_duration = db.Column(db.Integer, default=0)
    
    # File sizes processed (in bytes)
    total_file_size_processed = db.Column(db.BigInteger, default=0)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Composite unique constraint for user_id + date
    __table_args__ = (db.UniqueConstraint('user_id', 'date', name='_user_date_uc'),)
    
    def get_export_types_dict(self):
        if self.export_types_used:
            try:
                return json.loads(self.export_types_used)
            except json.JSONDecodeError:
                return {}
        return {}
    
    def set_export_types_dict(self, export_dict):
        self.export_types_used = json.dumps(export_dict) if export_dict else None
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'date': self.date.isoformat() if self.date else None,
            'projects_created_today': self.projects_created_today,
            'images_uploaded_today': self.images_uploaded_today,
            'images_processed_today': self.images_processed_today,
            'exports_generated_today': self.exports_generated_today,
            'export_types_used': self.get_export_types_dict(),
            'session_duration': self.session_duration,
            'total_file_size_processed': self.total_file_size_processed,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class SystemStatistics(db.Model):
    __tablename__ = 'system_statistics'
    
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, unique=True, index=True)
    
    # Daily totals
    total_users_registered_today = db.Column(db.Integer, default=0)
    total_projects_created_today = db.Column(db.Integer, default=0)
    total_images_uploaded_today = db.Column(db.Integer, default=0)
    total_images_processed_today = db.Column(db.Integer, default=0)
    total_exports_generated_today = db.Column(db.Integer, default=0)
    
    # Active user counts
    daily_active_users = db.Column(db.Integer, default=0)
    
    # File processing stats
    total_file_size_processed_today = db.Column(db.BigInteger, default=0)
    avg_processing_time_seconds = db.Column(db.Float, default=0)
    
    # Export breakdown (JSON)
    export_types_breakdown = db.Column(db.Text, nullable=True)  # JSON
    
    # Error rates
    processing_error_count = db.Column(db.Integer, default=0)
    processing_success_rate = db.Column(db.Float, default=100.0)
    
    # System performance
    avg_response_time_ms = db.Column(db.Float, default=0)
    peak_concurrent_users = db.Column(db.Integer, default=0)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    def get_export_breakdown_dict(self):
        if self.export_types_breakdown:
            try:
                return json.loads(self.export_types_breakdown)
            except json.JSONDecodeError:
                return {}
        return {}
    
    def set_export_breakdown_dict(self, breakdown_dict):
        self.export_types_breakdown = json.dumps(breakdown_dict) if breakdown_dict else None
    
    def to_dict(self):
        return {
            'id': self.id,
            'date': self.date.isoformat() if self.date else None,
            'total_users_registered_today': self.total_users_registered_today,
            'total_projects_created_today': self.total_projects_created_today,
            'total_images_uploaded_today': self.total_images_uploaded_today,
            'total_images_processed_today': self.total_images_processed_today,
            'total_exports_generated_today': self.total_exports_generated_today,
            'daily_active_users': self.daily_active_users,
            'total_file_size_processed_today': self.total_file_size_processed_today,
            'avg_processing_time_seconds': self.avg_processing_time_seconds,
            'export_types_breakdown': self.get_export_breakdown_dict(),
            'processing_error_count': self.processing_error_count,
            'processing_success_rate': self.processing_success_rate,
            'avg_response_time_ms': self.avg_response_time_ms,
            'peak_concurrent_users': self.peak_concurrent_users,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }