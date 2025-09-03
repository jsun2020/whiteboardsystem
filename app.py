import os
from flask import Flask, request, jsonify, render_template, send_file, session
from flask_cors import CORS
from config import config_by_name
import redis
from datetime import datetime, timezone
from database import db, migrate
import uuid

def create_app(config_name=None):
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'default')
    
    app = Flask(__name__)
    app.config.from_object(config_by_name[config_name])
    
    # Ensure secret key is set for sessions
    if not app.config.get('SECRET_KEY'):
        app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # Configure session for production/development
    is_production = os.environ.get('VERCEL') or config_name == 'production'
    app.config['SESSION_COOKIE_SECURE'] = is_production  # Only send over HTTPS in production
    app.config['SESSION_COOKIE_HTTPONLY'] = True  # Prevent XSS
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # CSRF protection
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    CORS(app, origins=app.config['CORS_ORIGINS'], supports_credentials=True)
    
    # Create upload and export directories
    try:
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        os.makedirs(app.config['EXPORT_FOLDER'], exist_ok=True)
        # Create subdirectories for uploads
        os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'original'), exist_ok=True)
        os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'processed'), exist_ok=True)
    except OSError as e:
        # In serverless environments, directories will be created on demand
        print(f"Warning: Could not create directories: {e}")
    
    # Register blueprints
    from api.upload import upload_bp
    from api.process import process_bp
    from api.export import export_bp
    from api.workspace import workspace_bp
    # from api.auth import auth_bp  # Using direct auth implementation instead
    from api.blueprints.statistics import statistics_bp
    from api.admin.quick_stats import admin_bp
    
    app.register_blueprint(upload_bp, url_prefix='/api')
    app.register_blueprint(process_bp, url_prefix='/api')
    app.register_blueprint(export_bp, url_prefix='/api')
    app.register_blueprint(workspace_bp, url_prefix='/api')
    # app.register_blueprint(auth_bp, url_prefix='/api/auth')  # Using direct auth implementation instead
    app.register_blueprint(statistics_bp, url_prefix='/api/statistics')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    
    # Main routes
    @app.route('/')
    def index():
        return render_template('index.html')
    
    @app.route('/preview/<project_id>')
    def preview(project_id):
        return render_template('preview.html', project_id=project_id)
    
    @app.route('/share/<share_id>')
    def share(share_id):
        return render_template('share.html', share_id=share_id)
    
    @app.route('/admin-panel')
    def admin_panel():
        from auth_middleware import require_admin
        @require_admin
        def _admin_panel():
            return render_template('admin.html')
        return _admin_panel()
    
    @app.route('/statistics')
    def user_statistics():
        return render_template('statistics.html')
    
    @app.route('/admin-panel/statistics')
    def admin_statistics():
        from auth_middleware import require_admin
        @require_admin
        def _admin_stats():
            return render_template('admin_statistics.html')
        return _admin_stats()
    
    
    @app.route('/api/auth/register', methods=['POST'])
    def api_register():
        data = request.get_json()
        email = data.get('email', '').strip().lower()
        username = data.get('username', '').strip()
        display_name = data.get('display_name', '').strip()
        password = data.get('password', '')
        
        if not email or not password:
            return jsonify({
                'success': False,
                'error': 'Email and password are required'
            }), 400
        
        if len(password) < 6:
            return jsonify({
                'success': False,
                'error': 'Password must be at least 6 characters long'
            }), 400
        
        from models import User
        from database import db
        
        # Check if user already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return jsonify({
                'success': False,
                'error': 'An account with this email already exists'
            }), 400
        
        # Create new user
        new_user = User()
        new_user.email = email
        new_user.username = username or email.split('@')[0]
        new_user.display_name = display_name or new_user.username
        new_user.set_password(password)
        
        # Set admin status for the specific admin email
        if email == 'jsun2016@live.com':
            new_user.is_admin = True
        
        try:
            db.session.add(new_user)
            db.session.commit()
            
            # Auto-login the user after registration
            session['user_email'] = new_user.email
            session['is_admin'] = new_user.is_admin
            session['user_id'] = new_user.id
            
            # Return user data
            user_data = {
                "id": new_user.id,
                "email": new_user.email,
                "username": new_user.username,
                "display_name": new_user.display_name,
                "is_admin": new_user.is_admin,
                "is_active": new_user.is_active,
                "can_use_service": new_user.can_use_service(),
                "projects_created": new_user.projects_created,
                "images_processed": new_user.images_processed,
                "exports_generated": new_user.exports_generated,
                "free_uses_count": new_user.free_uses_count,
                "subscription_type": new_user.subscription_type,
                "is_authenticated": True,
                "authenticated": True
            }
            
            return jsonify({
                'success': True,
                'user': user_data,
                'message': 'Account created successfully'
            })
            
        except Exception as e:
            db.session.rollback()
            return jsonify({
                'success': False,
                'error': 'Failed to create account. Please try again.'
            }), 500

    @app.route('/api/auth/login', methods=['POST'])
    def api_login():
        data = request.get_json()
        email = data.get('email', '').strip()
        password = data.get('password', '')
        
        from auth_middleware import verify_user_credentials
        
        # Verify credentials
        is_valid, result = verify_user_credentials(email, password)
        
        if is_valid:
            # Store user info in session
            session['user_email'] = result['email']
            session['is_admin'] = result['is_admin']
            session['user_id'] = result['id']
            
            return jsonify({
                'success': True,
                'user': result  # Return complete user object like your example
            })
        else:
            return jsonify({
                'success': False,
                'error': result  # This contains the error message
            }), 401
    
    @app.route('/api/auth/logout', methods=['POST'])
    def api_logout():
        session.clear()
        return jsonify({'success': True})
    
    @app.route('/api/auth/status', methods=['GET'])
    def api_auth_status():
        # Check if user is logged in
        if 'user_email' not in session:
            return jsonify({
                'success': True,
                'user': {
                    'is_authenticated': False,
                    'authenticated': False,
                    'is_admin': False
                }
            })
        
        # Get user data from database
        email = session.get('user_email')
        from models import User
        
        user = User.query.filter_by(email=email).first()
        if not user:
            # User not found in database, clear session
            session.clear()
            return jsonify({
                'success': True,
                'user': {
                    'is_authenticated': False,
                    'authenticated': False,
                    'is_admin': False
                }
            })
        
        # Return real user data from database
        user_data = {
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "display_name": user.display_name or user.username,
            "is_admin": user.is_admin,
            "is_active": user.is_active,
            "is_authenticated": True,
            "authenticated": True,
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
            "created_at": user.created_at.isoformat() if user.created_at else None
        }
        
        return jsonify({
            'success': True,
            'user': user_data
        })
    
    @app.route('/api/auth/setup-admin', methods=['POST', 'GET'])
    def setup_admin_route():
        """Temporary route to set admin privileges for jsun2016@live.com - REMOVE AFTER USE"""
        # Allow both GET and POST requests without secret for this specific user
        # This is a temporary measure to resolve the immediate admin access issue
        
        from models import User
        from database import db
        
        # Find the user and set admin privileges
        user = User.query.filter_by(email='jsun2016@live.com').first()
        if not user:
            return jsonify({
                'success': False,
                'error': 'User jsun2016@live.com not found'
            }), 404
        
        # Set admin privileges
        user.is_admin = True
        
        try:
            db.session.commit()
            return jsonify({
                'success': True,
                'message': f'Admin privileges granted to {user.email}',
                'user': {
                    'email': user.email,
                    'is_admin': user.is_admin,
                    'display_name': user.display_name
                }
            })
        except Exception as e:
            db.session.rollback()
            return jsonify({
                'success': False,
                'error': f'Database error: {str(e)}'
            }), 500


    @app.route('/api/auth/hash-password', methods=['POST'])
    def hash_password_route():
        """Utility route to generate password hash for admin setup - REMOVE IN PRODUCTION"""
        data = request.get_json()
        password = data.get('password', '')
        
        if not password:
            return jsonify({
                'success': False,
                'error': 'Password is required'
            }), 400
        
        from auth_middleware import hash_password
        password_hash = hash_password(password)
        
        return jsonify({
            'success': True,
            'password_hash': password_hash,
            'note': 'Use this hash in ADMIN_USERS dictionary. Remove this route in production!'
        })
    
    @app.route('/health')
    def health():
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'version': '1.0.0'
        })
    
    @app.route('/debug')
    def debug():
        """Debug route to check environment"""
        import glob
        
        upload_folder = app.config.get('UPLOAD_FOLDER', 'uploads')
        
        # Find all files in upload directories
        upload_files = []
        try:
            for pattern in [
                os.path.join(upload_folder, '**/*'),
                os.path.join('public', 'uploads', '*'),
                'uploads/**/*',
                'public/uploads/*'
            ]:
                files = glob.glob(pattern, recursive=True)
                upload_files.extend(files)
        except Exception as e:
            upload_files.append(f"Error scanning: {str(e)}")
        
        debug_info = {
            'flask_env': os.environ.get('FLASK_ENV'),
            'vercel': os.environ.get('VERCEL'),
            'database_url': 'SET' if os.environ.get('DATABASE_URL') else 'NOT SET',
            'secret_key': 'SET' if app.config.get('SECRET_KEY') else 'NOT SET',
            'static_folder': app.static_folder,
            'template_folder': app.template_folder,
            'upload_folder': app.config.get('UPLOAD_FOLDER'),
            'config_name': config_name,
            'upload_files': upload_files,
            'current_directory': os.getcwd(),
            'directory_contents': os.listdir('.') if os.path.exists('.') else 'Cannot list'
        }
        return jsonify(debug_info)
    
    @app.route('/uploads/<path:filename>')
    def uploaded_file(filename):
        """Serve uploaded files"""
        import os
        upload_folder = app.config['UPLOAD_FOLDER']
        # Check both original and processed paths
        file_path = os.path.join(upload_folder, 'original', filename)
        if not os.path.exists(file_path):
            file_path = os.path.join(upload_folder, 'processed', filename)
        if not os.path.exists(file_path):
            # Try without subfolder
            file_path = os.path.join(upload_folder, filename)
        
        if os.path.exists(file_path):
            return send_file(file_path)
        else:
            return jsonify({'error': 'File not found'}), 404

    @app.route('/api/whiteboard/image/<whiteboard_id>')
    def whiteboard_image(whiteboard_id):
        """Serve whiteboard image by whiteboard ID"""
        import os
        
        # Try to find the image in various possible locations
        possible_paths = [
            # Check in upload folders
            os.path.join(app.config.get('UPLOAD_FOLDER', 'uploads'), 'original', f'{whiteboard_id}'),
            os.path.join(app.config.get('UPLOAD_FOLDER', 'uploads'), 'processed', f'{whiteboard_id}'),
            os.path.join(app.config.get('UPLOAD_FOLDER', 'uploads'), f'{whiteboard_id}'),
            # Check with common image extensions
            os.path.join(app.config.get('UPLOAD_FOLDER', 'uploads'), 'original', f'{whiteboard_id}.jpg'),
            os.path.join(app.config.get('UPLOAD_FOLDER', 'uploads'), 'original', f'{whiteboard_id}.jpeg'),
            os.path.join(app.config.get('UPLOAD_FOLDER', 'uploads'), 'original', f'{whiteboard_id}.png'),
            os.path.join(app.config.get('UPLOAD_FOLDER', 'uploads'), 'processed', f'{whiteboard_id}.jpg'),
            os.path.join(app.config.get('UPLOAD_FOLDER', 'uploads'), 'processed', f'{whiteboard_id}.jpeg'),
            os.path.join(app.config.get('UPLOAD_FOLDER', 'uploads'), 'processed', f'{whiteboard_id}.png'),
            # Check in public folder
            os.path.join('public', 'uploads', f'{whiteboard_id}.jpg'),
            os.path.join('public', 'uploads', f'{whiteboard_id}.jpeg'),
            os.path.join('public', 'uploads', f'{whiteboard_id}.png'),
        ]
        
        # Find the first existing file
        for path in possible_paths:
            if os.path.exists(path):
                try:
                    return send_file(path)
                except Exception as e:
                    print(f"Error serving file {path}: {e}")
                    continue
        
        # If no image found, return a placeholder or 404
        return jsonify({
            'error': 'Image not found',
            'whiteboard_id': whiteboard_id,
            'searched_paths': possible_paths
        }), 404
    
    return app

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5000)