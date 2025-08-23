from datetime import datetime, timezone
from database import db
import uuid
import json

class Whiteboard(db.Model):
    __tablename__ = 'whiteboards'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = db.Column(db.String(36), db.ForeignKey('projects.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    original_path = db.Column(db.String(500), nullable=False)
    processed_path = db.Column(db.String(500), nullable=True)
    file_size = db.Column(db.Integer, nullable=False)
    mime_type = db.Column(db.String(100), nullable=False)
    
    # Processing status
    processing_status = db.Column(db.String(20), default='uploaded')  # uploaded, processing, completed, error
    processing_progress = db.Column(db.Integer, default=0)  # 0-100
    error_message = db.Column(db.Text, nullable=True)
    
    # Extracted content
    raw_text = db.Column(db.Text, nullable=True)
    structured_content = db.Column(db.Text, nullable=True)  # JSON string
    confidence_score = db.Column(db.Float, nullable=True)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    processed_at = db.Column(db.DateTime, nullable=True)
    
    def to_dict(self):
        structured = None
        if self.structured_content:
            try:
                structured = json.loads(self.structured_content)
            except json.JSONDecodeError:
                structured = None
        
        return {
            'id': self.id,
            'project_id': self.project_id,
            'filename': self.filename,
            'file_size': self.file_size,
            'mime_type': self.mime_type,
            'processing_status': self.processing_status,
            'processing_progress': self.processing_progress,
            'error_message': self.error_message,
            'raw_text': self.raw_text,
            'structured_content': structured,
            'confidence_score': self.confidence_score,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'processed_at': self.processed_at.isoformat() if self.processed_at else None
        }
    
    def set_structured_content(self, content_dict):
        self.structured_content = json.dumps(content_dict, ensure_ascii=False, indent=2)
    
    def get_structured_content(self):
        if self.structured_content:
            try:
                return json.loads(self.structured_content)
            except json.JSONDecodeError:
                return None
        return None
    
    def update_processing_status(self, status, progress=None, error_message=None):
        self.processing_status = status
        if progress is not None:
            self.processing_progress = progress
        if error_message is not None:
            self.error_message = error_message
        if status == 'completed':
            self.processed_at = datetime.now(timezone.utc)
        db.session.commit()