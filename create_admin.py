#!/usr/bin/env python3
"""
Create an admin user for the whiteboard scribe application
Usage: python create_admin.py admin@example.com password123
"""
import sys
import os

# Add the current directory to the path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from app import create_app
from database import db
from models.user import User

def create_admin_user(email, password):
    """Create an admin user"""
    app = create_app()
    
    with app.app_context():
        # Check if user already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            if existing_user.is_admin:
                print(f"Admin user {email} already exists!")
                return True
            else:
                # Upgrade existing user to admin
                existing_user.is_admin = True
                db.session.commit()
                print(f"User {email} upgraded to admin!")
                return True
        
        # Create new admin user
        admin = User()
        admin.email = email
        admin.username = email.split('@')[0] + '_admin'
        admin.display_name = 'Administrator'
        admin.set_password(password)
        admin.is_admin = True
        admin.is_active = True
        admin.email_verified = True
        admin.subscription_type = 'unlimited'
        admin.payment_status = 'active'
        
        try:
            db.session.add(admin)
            db.session.commit()
            print(f"Admin user created successfully!")
            print(f"Email: {admin.email}")
            print(f"Username: {admin.username}")
            print(f"You can now login with admin privileges.")
            return True
        except Exception as e:
            print(f"Error creating admin user: {e}")
            db.session.rollback()
            return False

def main():
    if len(sys.argv) != 3:
        print("Usage: python create_admin.py <email> <password>")
        print("Example: python create_admin.py admin@company.com mypassword123")
        sys.exit(1)
    
    email = sys.argv[1]
    password = sys.argv[2]
    
    if len(password) < 8:
        print("Password must be at least 8 characters long!")
        sys.exit(1)
    
    success = create_admin_user(email, password)
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()