from app import create_app

# Create the Flask app instance for Vercel
app = create_app()

# Initialize database tables
with app.app_context():
    from database import db
    db.create_all()

# This is required for Vercel
if __name__ == "__main__":
    app.run()