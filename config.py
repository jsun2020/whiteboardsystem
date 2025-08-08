import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///whiteboard_scribe.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # File Upload Settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'heic'}
    
    # Redis Settings
    REDIS_URL = os.environ.get('REDIS_URL') or 'redis://localhost:6379'
    
    # Doubao API Settings
    DOUBAO_API_KEY = os.environ.get('DOUBAO_API_KEY')
    DOUBAO_ENDPOINT = os.environ.get('DOUBAO_ENDPOINT') or 'https://ark.cn-beijing.volces.com/api/v3'
    DOUBAO_MODEL_ID = os.environ.get('DOUBAO_MODEL_ID') or 'doubao-seed-1-6-flash-250715'
    
    # Storage Settings
    STORAGE_TYPE = os.environ.get('STORAGE_TYPE') or 'local'
    S3_BUCKET = os.environ.get('S3_BUCKET')
    S3_REGION = os.environ.get('S3_REGION') or 'us-east-1'
    AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
    
    # Export Settings
    EXPORT_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'exports', 'temp')
    
    # Security Settings
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '*').split(',')
    RATE_LIMIT = os.environ.get('RATE_LIMIT') or '100 per hour'

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or 'sqlite:///dev_whiteboard_scribe.db'

class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

config_by_name = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}