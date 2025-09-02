from functools import wraps
from flask import request, jsonify, session, redirect, url_for, render_template
from datetime import datetime, timezone
import uuid

def verify_user_credentials(email, password):
    """Verify user email and password against database"""
    if not email or not password:
        return False, "Email and password are required"
    
    email = email.lower().strip()
    
    # Import here to avoid circular imports
    from models import User
    from database import db
    
    # Look up user in database
    user = User.query.filter_by(email=email).first()
    if not user:
        return False, "Invalid email or password"
    
    # Check password using the User model's check_password method
    if not user.check_password(password):
        return False, "Invalid email or password"
    
    # Update last active timestamp
    user.last_active = datetime.now(timezone.utc)
    try:
        db.session.commit()
    except:
        db.session.rollback()
    
    # Return real user data from database
    user_data = {
        "id": user.id,
        "email": user.email,
        "username": user.username,
        "display_name": user.display_name or user.username,
        "is_admin": user.is_admin,
        "is_active": user.is_active,
        "can_use_service": user.can_use_service(),
        "projects_created": user.projects_created,
        "images_processed": user.images_processed,
        "exports_generated": user.exports_generated,
        "free_uses_count": user.free_uses_count,
        "subscription_type": user.subscription_type,
        "subscription_expires_at": user.subscription_expires_at.isoformat() if user.subscription_expires_at else None,
        "payment_status": user.payment_status,
        "preferred_language": user.preferred_language,
        "theme_preference": user.theme_preference,
        "last_active": user.last_active.isoformat() if user.last_active else None,
        "created_at": user.created_at.isoformat() if user.created_at else None,
        "is_authenticated": True,
        "authenticated": True
    }
    
    return True, user_data

def is_admin(email):
    """Check if user is admin by looking up in database"""
    if not email:
        return False
        
    from models import User
    user = User.query.filter_by(email=email.lower().strip()).first()
    return user.is_admin if user else False

def require_admin(f):
    """Decorator to require admin access"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if user is logged in and is admin
        user_email = session.get('user_email')
        if not user_email or not is_admin(user_email):
            # For API endpoints (requests expecting JSON), return JSON error
            if request.is_json or request.path.startswith('/api/'):
                return jsonify({
                    'success': False,
                    'error': 'Admin access required',
                    'redirect': '/'
                }), 403
            else:
                # For web pages, redirect to home page (no standalone login)
                return redirect('/')
        return f(*args, **kwargs)
    return decorated_function

def get_current_user():
    """Get current logged in user"""
    return {
        'email': session.get('user_email'),
        'is_admin': is_admin(session.get('user_email')),
        'is_authenticated': 'user_email' in session
    }