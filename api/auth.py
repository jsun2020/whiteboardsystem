from flask import Blueprint, request, jsonify, session, current_app
from models.user import User
from database import db
import uuid
from functools import wraps
import jwt
from datetime import datetime, timedelta, timezone

auth_bp = Blueprint('auth', __name__)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'error': 'Authentication required', 'code': 401}), 401
            
        try:
            if token.startswith('Bearer '):
                token = token[7:]
                
            # Check if SECRET_KEY exists
            secret_key = current_app.config.get('SECRET_KEY')
            if not secret_key:
                print("ERROR: SECRET_KEY not configured")
                return jsonify({'error': 'Server configuration error', 'code': 500}), 500
                
            # Decode JWT token
            data = jwt.decode(token, secret_key, algorithms=['HS256'])
            user_id = data.get('user_id')
            
            if not user_id:
                print("ERROR: No user_id in token")
                return jsonify({'error': 'Invalid token format', 'code': 401}), 401
                
            # Get user from database
            current_user = User.query.get(user_id)
            if not current_user:
                print(f"ERROR: User not found: {user_id}")
                return jsonify({'error': 'User not found', 'code': 401}), 401
                
            if not current_user.is_active:
                print(f"ERROR: User inactive: {user_id}")
                return jsonify({'error': 'User account inactive', 'code': 401}), 401
                
            request.current_user = current_user
            
        except jwt.ExpiredSignatureError:
            print("ERROR: JWT token expired")
            return jsonify({'error': 'Token expired', 'code': 401}), 401
        except jwt.InvalidTokenError as e:
            print(f"ERROR: Invalid JWT token: {e}")
            return jsonify({'error': 'Invalid token', 'code': 401}), 401
        except Exception as e:
            print(f"ERROR: Authentication error: {e}")
            return jsonify({'error': 'Authentication failed', 'code': 500}), 500
            
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not hasattr(request, 'current_user') or not request.current_user.is_admin:
            return jsonify({'error': 'Admin privileges required'}), 403
        return f(*args, **kwargs)
    return decorated_function

@auth_bp.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        
        if not data.get('email') or not data.get('password'):
            return jsonify({'error': 'Email and password required'}), 400
        
        # Check if user already exists
        existing_user = User.query.filter_by(email=data['email']).first()
        if existing_user:
            return jsonify({'error': 'Email already registered'}), 400
        
        # Create new user
        user = User()
        user.email = data['email']
        
        # Handle username uniqueness
        base_username = data.get('username', data['email'].split('@')[0])
        username = base_username
        counter = 1
        while User.query.filter_by(username=username).first():
            username = f"{base_username}{counter}"
            counter += 1
        
        user.username = username
        user.display_name = data.get('display_name', user.username)
        user.set_password(data['password'])
        user.session_token = str(uuid.uuid4())
        user.preferred_language = data.get('language', 'en')
        
        db.session.add(user)
        db.session.commit()
        
        # Generate JWT token
        try:
            token = jwt.encode({
                'user_id': user.id,
                'exp': datetime.now(timezone.utc) + timedelta(days=30)
            }, current_app.config['SECRET_KEY'], algorithm='HS256')
        except Exception as jwt_error:
            current_app.logger.error(f'JWT token generation error: {str(jwt_error)}')
            # Fallback to simple session token
            token = user.session_token
        
        return jsonify({
            'success': True,
            'message': 'Registration successful',
            'token': token,
            'user': user.to_dict()
        })
    
    except Exception as e:
        # Rollback any changes
        db.session.rollback()
        current_app.logger.error(f'Registration error: {str(e)}')
        
        # Return a specific error message
        return jsonify({
            'error': f'Registration failed: {str(e)}'
        }), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        
        if not data.get('email') or not data.get('password'):
            return jsonify({'error': 'Email and password required'}), 400
        
        user = User.query.filter_by(email=data['email']).first()
        
        if not user or not user.check_password(data['password']):
            return jsonify({'error': 'Invalid email or password'}), 401
        
        if not user.is_active:
            return jsonify({'error': 'Account is disabled'}), 401
        
        user.update_activity()
        
        # Generate JWT token
        try:
            token = jwt.encode({
                'user_id': user.id,
                'exp': datetime.now(timezone.utc) + timedelta(days=30)
            }, current_app.config['SECRET_KEY'], algorithm='HS256')
        except Exception as jwt_error:
            current_app.logger.error(f'JWT token generation error: {str(jwt_error)}')
            # Fallback to simple session token
            token = user.session_token
        
        return jsonify({
            'success': True,
            'message': 'Login successful',
            'token': token,
            'user': user.to_dict()
        })
    
    except Exception as e:
        # Rollback any changes
        db.session.rollback()
        current_app.logger.error(f'Login error: {str(e)}')
        
        return jsonify({
            'error': f'Login failed: {str(e)}'
        }), 500

@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    # In JWT, we don't need to do anything server-side for logout
    # Client should just remove the token
    return jsonify({
        'success': True,
        'message': 'Logged out successfully'
    })

@auth_bp.route('/profile', methods=['GET'])
@login_required
def get_profile():
    return jsonify({
        'success': True,
        'user': request.current_user.to_dict()
    })

@auth_bp.route('/profile', methods=['PUT'])
@login_required
def update_profile():
    data = request.get_json()
    user = request.current_user
    
    if 'display_name' in data:
        user.display_name = data['display_name']
    if 'preferred_language' in data:
        user.preferred_language = data['preferred_language']
    if 'theme_preference' in data:
        user.theme_preference = data['theme_preference']
    if 'custom_api_key' in data:
        user.custom_api_key = data['custom_api_key']  # Should encrypt this in production
    
    user.updated_at = datetime.now(timezone.utc)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Profile updated successfully',
        'user': user.to_dict()
    })

@auth_bp.route('/usage', methods=['GET'])
@login_required
def get_usage():
    user = request.current_user
    remaining_free_uses = max(0, 10 - user.free_uses_count)
    
    return jsonify({
        'success': True,
        'usage': {
            'free_uses_count': user.free_uses_count,
            'remaining_free_uses': remaining_free_uses,
            'projects_created': user.projects_created,
            'images_processed': user.images_processed,
            'exports_generated': user.exports_generated,
            'subscription_type': user.subscription_type,
            'subscription_expires_at': user.subscription_expires_at.isoformat() if user.subscription_expires_at else None,
            'payment_status': user.payment_status,
            'can_use_service': user.can_use_service()
        }
    })

@auth_bp.route('/admin/users', methods=['GET'])
@login_required
@admin_required
def list_users():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    users = User.query.paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'success': True,
        'users': [user.to_dict() for user in users.items],
        'pagination': {
            'page': users.page,
            'pages': users.pages,
            'per_page': users.per_page,
            'total': users.total
        }
    })

@auth_bp.route('/admin/stats', methods=['GET'])
@login_required
@admin_required
def get_admin_stats():
    total_users = User.query.count()
    active_subscriptions = User.query.filter(
        User.subscription_expires_at > datetime.now(timezone.utc),
        User.payment_status == 'active'
    ).count()
    pending_payments = User.query.filter_by(payment_status='pending').count()
    
    # Calculate monthly revenue (simplified)
    monthly_revenue = User.query.filter_by(subscription_type='monthly', payment_status='active').count() * 16.5
    semi_annual_revenue = User.query.filter_by(subscription_type='semi_annual', payment_status='active').count() * 99 / 6
    annual_revenue = User.query.filter_by(subscription_type='annual', payment_status='active').count() * 198 / 12
    total_monthly_revenue = monthly_revenue + semi_annual_revenue + annual_revenue
    
    return jsonify({
        'success': True,
        'stats': {
            'total_users': total_users,
            'active_subscriptions': active_subscriptions,
            'monthly_revenue': round(total_monthly_revenue, 2),
            'pending_payments': pending_payments
        }
    })

@auth_bp.route('/admin/users/<user_id>/subscription', methods=['PUT'])
@login_required
@admin_required
def update_user_subscription(user_id):
    data = request.get_json()
    user = User.query.get_or_404(user_id)
    
    if 'subscription_type' in data:
        user.subscription_type = data['subscription_type']
    
    if 'payment_status' in data:
        user.payment_status = data['payment_status']
    
    # Set subscription expiration based on type
    if data.get('activate_subscription'):
        if user.subscription_type == 'monthly':
            user.subscription_expires_at = datetime.now(timezone.utc) + timedelta(days=30)
        elif user.subscription_type == 'semi_annual':
            user.subscription_expires_at = datetime.now(timezone.utc) + timedelta(days=182)
        elif user.subscription_type == 'annual':
            user.subscription_expires_at = datetime.now(timezone.utc) + timedelta(days=365)
        user.payment_status = 'active'
    
    user.updated_at = datetime.now(timezone.utc)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'User subscription updated successfully',
        'user': user.to_dict()
    })

@auth_bp.route('/payment/plans', methods=['GET'])
def get_payment_plans():
    return jsonify({
        'success': True,
        'plans': [
            {
                'id': 'monthly',
                'name': 'Monthly Plan',
                'price': 16.5,
                'currency': 'CNY',
                'duration': '1 month',
                'features': ['Unlimited usage', 'All export formats', 'Priority support']
            },
            {
                'id': 'semi_annual',
                'name': 'Semi-Annual Plan',
                'price': 99,
                'currency': 'CNY',
                'duration': '6 months',
                'features': ['Unlimited usage', 'All export formats', 'Priority support', '17% savings']
            },
            {
                'id': 'annual',
                'name': 'Annual Plan',
                'price': 198,
                'currency': 'CNY',
                'duration': '12 months',
                'features': ['Unlimited usage', 'All export formats', 'Priority support', '50% savings']
            }
        ]
    })