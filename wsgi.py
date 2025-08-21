"""
WSGI entry point for Vercel deployment
"""
from app import create_app
import os

# Create the Flask app
app = create_app(os.environ.get('FLASK_ENV', 'production'))

if __name__ == "__main__":
    app.run()