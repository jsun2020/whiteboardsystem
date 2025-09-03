#!/usr/bin/env python3
"""
Reset password for jsun2016@live.com
"""
import getpass
from database import db
from models import User
from flask import Flask
import os

def reset_password():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///whiteboard_scribe.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.secret_key = 'reset'
    
    db.init_app(app)
    
    with app.app_context():
        user = User.query.filter_by(email='jsun2016@live.com').first()
        if not user:
            print("User jsun2016@live.com not found!")
            return False
        
        print(f"Resetting password for: {user.email}")
        new_password = getpass.getpass("Enter new password: ")
        confirm_password = getpass.getpass("Confirm password: ")
        
        if new_password != confirm_password:
            print("Passwords don't match!")
            return False
        
        if len(new_password) < 6:
            print("Password must be at least 6 characters!")
            return False
        
        user.set_password(new_password)
        try:
            db.session.commit()
            print("Password updated successfully!")
            return True
        except Exception as e:
            print(f"Error: {e}")
            db.session.rollback()
            return False

if __name__ == '__main__':
    reset_password()