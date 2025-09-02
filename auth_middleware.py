from functools import wraps
from flask import request, jsonify, session, redirect, url_for, render_template
from datetime import datetime, timezone
import uuid

# Admin email - simple check
ADMIN_EMAIL = 'jsun2016@live.com'

def is_admin(email):
    """Check if user is admin - simple email check"""
    return email and email.lower().strip() == ADMIN_EMAIL.lower()

def verify_user_credentials(email, password):
    """Verify user email and password - simplified for demo"""
    if not email or not password:
        return False, "Email and password are required"
    
    email = email.lower().strip()
    
    # For this demo, any non-empty password works
    # In production, you'd verify against a real database
    if password.strip():
        user_data = {
            "id": str(uuid.uuid4()),
            "email": email,
            "username": email.split('@')[0],
            "display_name": "jason" if is_admin(email) else email.split('@')[0],
            "is_admin": is_admin(email),
            "is_active": True,
            "can_use_service": True,
            "projects_created": 25 if is_admin(email) else 0,
            "images_processed": 25 if is_admin(email) else 0,
            "exports_generated": 2 if is_admin(email) else 0,
            "free_uses_count": 11 if is_admin(email) else 0,
            "subscription_type": "free",
            "subscription_expires_at": None,
            "payment_status": "none",
            "preferred_language": "zh-CN" if is_admin(email) else "en",
            "theme_preference": "light",
            "last_active": datetime.now(timezone.utc).isoformat(),
            "created_at": "2025-08-24T10:09:43.648263" if is_admin(email) else datetime.now(timezone.utc).isoformat(),
            "authenticated": True
        }
        
        return True, user_data
    
    return False, "Password is required"

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