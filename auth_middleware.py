from functools import wraps
from flask import request, jsonify, session, redirect, url_for, render_template
import hashlib

# Admin users with their hashed passwords
# To generate a new password hash, use: hashlib.sha256('your_password'.encode()).hexdigest()
ADMIN_USERS = {
    'jsun2016@live.com': {
        'password_hash': '8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918',  # "admin" hashed with SHA256
        'is_admin': True
    }
}

def hash_password(password):
    """Hash password using SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_user_credentials(email, password):
    """Verify user email and password"""
    if not email or not password:
        return False, "Email and password are required"
    
    email = email.lower().strip()
    
    # Check if user exists in our admin users
    if email in ADMIN_USERS:
        user_data = ADMIN_USERS[email]
        password_hash = hash_password(password)
        
        if password_hash == user_data['password_hash']:
            return True, {
                'email': email,
                'is_admin': user_data.get('is_admin', False),
                'authenticated': True
            }
        else:
            return False, "Invalid password"
    
    # For demo purposes, allow other users with any password for regular access
    # In production, this should check against a real user database
    if password:  # Just require non-empty password for regular users
        return True, {
            'email': email,
            'is_admin': False,
            'authenticated': True
        }
    
    return False, "Invalid credentials"

def is_admin(email):
    """Check if user is admin"""
    if not email:
        return False
    email = email.lower().strip()
    return email in ADMIN_USERS and ADMIN_USERS[email].get('is_admin', False)

def require_admin(f):
    """Decorator to require admin access"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if user is logged in and is admin
        user_email = session.get('user_email')
        if not user_email or not is_admin(user_email):
            if request.is_json:
                return jsonify({
                    'success': False,
                    'error': 'Admin access required',
                    'redirect': '/login'
                }), 403
            else:
                return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def get_current_user():
    """Get current logged in user"""
    return {
        'email': session.get('user_email'),
        'is_admin': is_admin(session.get('user_email')),
        'is_authenticated': 'user_email' in session
    }