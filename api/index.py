from app import create_app
import os

# Create the Flask app instance for Vercel
app = create_app('production')

# Initialize database tables - handle gracefully
try:
    with app.app_context():
        from database import db
        from models.user import User
        from models.project import Project  
        from models.whiteboard import Whiteboard
        from models.export import Export
        
        # Create all tables
        db.create_all()
        
        print("Database tables initialized successfully")
        
except Exception as e:
    print(f"Database initialization error: {e}")
    # Don't fail the deployment - let it continue

# Add additional configuration for serverless environment
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = False  # Set to True in production with HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True

# This is required for Vercel
if __name__ == "__main__":
    app.run()