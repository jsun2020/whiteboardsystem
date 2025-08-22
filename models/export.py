from datetime import datetime, timezone
from database import db
import uuid

class Export(db.Model):
    __tablename__ = 'exports'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = db.Column(db.String(36), db.ForeignKey('projects.id'), nullable=False)
    export_type = db.Column(db.String(20), nullable=False)  # markdown, pptx, mindmap, notion, confluence
    filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.Integer, nullable=False)
    
    # Export options
    export_options = db.Column(db.Text, nullable=True)  # JSON string of export options
    
    # Status
    status = db.Column(db.String(20), default='generating')  # generating, completed, error
    error_message = db.Column(db.Text, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at = db.Column(db.DateTime, nullable=True)
    
    # Download tracking
    download_count = db.Column(db.Integer, default=0)
    last_downloaded = db.Column(db.DateTime, nullable=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'project_id': self.project_id,
            'export_type': self.export_type,
            'filename': self.filename,
            'file_size': self.file_size,
            'status': self.status,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'download_count': self.download_count,
            'last_downloaded': self.last_downloaded.isoformat() if self.last_downloaded else None
        }
    
    def mark_downloaded(self):
        self.download_count += 1
        self.last_downloaded = datetime.now(timezone.utc)()
        db.session.commit()
    
    def mark_completed(self):
        self.status = 'completed'
        self.completed_at = datetime.now(timezone.utc)()
        db.session.commit()
    
    def mark_error(self, error_message):
        self.status = 'error'
        self.error_message = error_message
        db.session.commit()