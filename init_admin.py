#!/usr/bin/env python3
"""
Script to create the first admin user for Meeting Whiteboard Scribe
Run this after deploying to create your admin account
"""

import os
import sys
from app import create_app
from database import db
from models.user import User

def create_admin_user(email, password, username=None, display_name=None):
    """Create an admin user"""
    app = create_app()
    
    with app.app_context():
        # Check if user already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            print(f"User with email {email} already exists!")
            return False
        
        # Create admin user
        admin = User()
        admin.email = email
        admin.username = username or email.split('@')[0]
        admin.display_name = display_name or admin.username
        admin.set_password(password)
        admin.is_admin = True
        admin.is_active = True
        admin.email_verified = True
        
        try:
            db.session.add(admin)
            db.session.commit()
            print(f"✅ Admin user created successfully!")
            print(f"   Email: {admin.email}")
            print(f"   Username: {admin.username}")
            print(f"   Admin: {admin.is_admin}")
            print(f"\nYou can now login at /admin with these credentials.")
            return True
        except Exception as e:
            print(f"❌ Error creating admin user: {e}")
            db.session.rollback()
            return False

def main():
    """Main function to handle command line arguments"""
    if len(sys.argv) < 3:
        print("Usage: python init_admin.py <email> <password> [username] [display_name]")
        print("Example: python init_admin.py admin@example.com mypassword admin 'Administrator'")
        sys.exit(1)
    
    email = sys.argv[1]
    password = sys.argv[2]
    username = sys.argv[3] if len(sys.argv) > 3 else None
    display_name = sys.argv[4] if len(sys.argv) > 4 else None
    
    # Validate email format
    import re
    if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
        print("❌ Invalid email format!")
        sys.exit(1)
    
    # Validate password strength
    if len(password) < 8:
        print("❌ Password must be at least 8 characters long!")
        sys.exit(1)
    
    print("Creating admin user...")
    print(f"Email: {email}")
    print(f"Username: {username or email.split('@')[0]}")
    print(f"Display Name: {display_name or username or email.split('@')[0]}")
    print()
    
    success = create_admin_user(email, password, username, display_name)
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()