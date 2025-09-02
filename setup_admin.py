#!/usr/bin/env python3
"""
Quick setup script for admin user jsun2016@live.com
This will prompt for password and create the admin user
"""

import getpass
import sys
from app import create_app
from database import db
from models import User

def setup_admin():
    """Setup the admin user jsun2016@live.com"""
    ADMIN_EMAIL = 'jsun2016@live.com'
    
    app = create_app()
    
    with app.app_context():
        # Check if admin already exists
        existing_admin = User.query.filter_by(email=ADMIN_EMAIL).first()
        if existing_admin:
            print(f"✅ Admin user {ADMIN_EMAIL} already exists!")
            print(f"   Admin status: {existing_admin.is_admin}")
            
            # Ask if they want to reset password
            reset = input("Do you want to reset the password? (y/n): ").lower().strip()
            if reset == 'y':
                password = getpass.getpass("Enter new password: ")
                confirm_password = getpass.getpass("Confirm password: ")
                
                if password != confirm_password:
                    print("❌ Passwords don't match!")
                    return False
                
                if len(password) < 6:
                    print("❌ Password must be at least 6 characters long!")
                    return False
                
                existing_admin.set_password(password)
                try:
                    db.session.commit()
                    print("✅ Password updated successfully!")
                    return True
                except Exception as e:
                    print(f"❌ Error updating password: {e}")
                    db.session.rollback()
                    return False
            return True
        
        # Create new admin user
        print(f"Creating admin user: {ADMIN_EMAIL}")
        password = getpass.getpass("Enter password for admin: ")
        confirm_password = getpass.getpass("Confirm password: ")
        
        if password != confirm_password:
            print("❌ Passwords don't match!")
            return False
        
        if len(password) < 6:
            print("❌ Password must be at least 6 characters long!")
            return False
        
        # Create admin user
        admin = User()
        admin.email = ADMIN_EMAIL
        admin.username = "jason"
        admin.display_name = "Jason (Admin)"
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
            print(f"   Display Name: {admin.display_name}")
            print(f"   Admin: {admin.is_admin}")
            print(f"\n🎉 You can now login with {ADMIN_EMAIL} and access the admin dashboard!")
            return True
        except Exception as e:
            print(f"❌ Error creating admin user: {e}")
            db.session.rollback()
            return False

if __name__ == '__main__':
    print("=== Admin User Setup ===")
    print("This script will create/update the admin user: jsun2016@live.com")
    print()
    
    success = setup_admin()
    sys.exit(0 if success else 1)