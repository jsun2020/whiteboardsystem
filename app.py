import os
from flask import Flask, request, jsonify, render_template, send_file
from flask_cors import CORS
from config import config_by_name
import redis
from datetime import datetime, timezone
from database import db, migrate

def create_app(config_name=None):
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'default')
    
    app = Flask(__name__)
    app.config.from_object(config_by_name[config_name])
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    CORS(app, origins=app.config['CORS_ORIGINS'])
    
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
    from api.auth import auth_bp
    from api.blueprints.statistics import statistics_bp
    
    app.register_blueprint(upload_bp, url_prefix='/api')
    app.register_blueprint(process_bp, url_prefix='/api')
    app.register_blueprint(export_bp, url_prefix='/api')
    app.register_blueprint(workspace_bp, url_prefix='/api')
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(statistics_bp, url_prefix='/api/stats')
    
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
    
    @app.route('/admin')
    def admin_dashboard():
        return render_template('admin.html')
    
    @app.route('/statistics')
    def user_statistics():
        return render_template('statistics.html')
    
    @app.route('/admin/statistics')
    def admin_statistics():
        return render_template('admin_statistics.html')
    
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
        debug_info = {
            'flask_env': os.environ.get('FLASK_ENV'),
            'vercel': os.environ.get('VERCEL'),
            'database_url': 'SET' if os.environ.get('DATABASE_URL') else 'NOT SET',
            'secret_key': 'SET' if app.config.get('SECRET_KEY') else 'NOT SET',
            'static_folder': app.static_folder,
            'template_folder': app.template_folder,
            'upload_folder': app.config.get('UPLOAD_FOLDER'),
            'config_name': config_name
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
        """Serve whiteboard image by whiteboard ID - Mock implementation"""
        return jsonify({'error': 'Whiteboard image serving not implemented yet'}), 404
    
    return app

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5000)