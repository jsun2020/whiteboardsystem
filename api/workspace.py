from flask import Blueprint, request, jsonify, session
from functools import wraps
# from models.project import Project
# from models.whiteboard import Whiteboard
# from models.export import Export
# from models.user import User
from database import db
from datetime import datetime, timedelta, timezone
import uuid

# Simple login required decorator that works with session-based auth
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_email' not in session:
            return jsonify({'error': 'Authentication required'}), 401
        
        # Create a mock user object for compatibility
        class MockUser:
            def __init__(self, email):
                self.id = session.get('user_id', str(uuid.uuid4()))
                self.email = email
                self.is_admin = session.get('is_admin', False)
        
        request.current_user = MockUser(session['user_email'])
        return f(*args, **kwargs)
    return decorated_function

workspace_bp = Blueprint('workspace', __name__)

@workspace_bp.route('/projects', methods=['GET'])
@login_required
def list_projects():
    """List user projects - returns mock data"""
    try:
        user = request.current_user
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        # Return mock project data
        mock_projects = [
            {
                'id': f'proj-{i+1}',
                'title': f'Project {i+1}',
                'description': f'Mock project {i+1} description',
                'status': 'active',
                'user_id': user.id,
                'whiteboard_count': 2 + i,
                'created_at': f'2024-08-{15+i}T10:00:00Z',
                'updated_at': f'2024-08-{20+i}T15:30:00Z',
                'last_activity': f'2024-08-{22+i}T12:00:00Z'
            } for i in range(min(per_page, 5))  # Return up to 5 mock projects
        ]
        
        return jsonify({
            'projects': mock_projects,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': 5,
                'pages': 1,
                'has_next': False,
                'has_prev': False
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@workspace_bp.route('/projects', methods=['POST'])
@login_required
def create_project():
    """Create new project - returns mock data"""
    try:
        user = request.current_user
        data = request.get_json()
        
        # Return mock project creation response
        mock_project = {
            'id': f'proj-new-{uuid.uuid4().hex[:8]}',
            'title': data.get('title', 'Untitled Project'),
            'description': data.get('description', ''),
            'status': 'draft',
            'user_id': user.id,
            'whiteboard_count': 0,
            'created_at': datetime.now(timezone.utc).isoformat(),
            'updated_at': datetime.now(timezone.utc).isoformat()
        }
        
        return jsonify({
            'success': True,
            'project': mock_project
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@workspace_bp.route('/projects/<project_id>', methods=['GET'])
@login_required
def get_project(project_id):
    try:
        user = request.current_user
        print(f"DEBUG: Getting project {project_id} for user {user.id}")
        
        project = Project.query.get(project_id)
        if not project:
            print(f"ERROR: Project not found: {project_id}")
            return jsonify({'error': 'Project not found', 'code': 404}), 404
        
        # Verify project belongs to current user
        if project.user_id != user.id:
            print(f"ERROR: Access denied. Project user_id: {project.user_id}, Current user: {user.id}")
            return jsonify({'error': 'Access denied', 'code': 403}), 403
        
        project_data = project.to_dict()
        
        # Add whiteboards
        whiteboards = Whiteboard.query.filter_by(project_id=project_id)\
            .order_by(Whiteboard.created_at.desc()).all()
        project_data['whiteboards'] = [wb.to_dict() for wb in whiteboards]
        
        # Add exports
        exports = Export.query.filter_by(project_id=project_id)\
            .order_by(Export.created_at.desc()).all()
        project_data['exports'] = [exp.to_dict() for exp in exports]
        
        return jsonify(project_data)
        
    except Exception as e:
        print(f"ERROR: Exception in get_project: {e}")
        return jsonify({'error': str(e), 'code': 500}), 500

@workspace_bp.route('/projects/<project_id>', methods=['PUT'])
@login_required
def update_project(project_id):
    try:
        user = request.current_user
        data = request.get_json()
        project = Project.query.get_or_404(project_id)
        
        # Verify project belongs to current user
        if project.user_id != user.id:
            return jsonify({'error': 'Access denied'}), 403
        
        if 'title' in data:
            project.title = data['title']
        if 'description' in data:
            project.description = data['description']
        if 'status' in data:
            project.status = data['status']
        
        project.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'project': project.to_dict()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@workspace_bp.route('/projects/<project_id>', methods=['DELETE'])
@login_required
def delete_project(project_id):
    try:
        user = request.current_user
        project = Project.query.get_or_404(project_id)
        
        # Verify project belongs to current user
        if project.user_id != user.id:
            return jsonify({'error': 'Access denied'}), 403
        
        # Delete associated whiteboards and exports (cascade should handle this)
        db.session.delete(project)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Project deleted successfully'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@workspace_bp.route('/share', methods=['POST'])
@login_required
def create_share_link():
    try:
        user = request.current_user
        data = request.get_json()
        project_id = data.get('project_id')
        
        if not project_id:
            return jsonify({'error': 'Project ID required'}), 400
        
        project = Project.query.get_or_404(project_id)
        
        # Verify project belongs to current user
        if project.user_id != user.id:
            return jsonify({'error': 'Access denied'}), 403
        
        # Create or get existing share token
        if not project.share_token:
            share_token = project.create_share_token()
        else:
            share_token = project.share_token
        
        return jsonify({
            'success': True,
            'share_token': share_token,
            'share_url': f"/share/{share_token}",
            'expires_at': None  # For now, links don't expire
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@workspace_bp.route('/share/<share_token>', methods=['GET'])
def get_shared_project(share_token):
    try:
        project = Project.find_by_share_token(share_token)
        if not project:
            return jsonify({'error': 'Share link not found or expired'}), 404
        
        project_data = project.to_dict()
        
        # Add whiteboards with content
        whiteboards = Whiteboard.query.filter_by(project_id=project.id)\
            .filter(Whiteboard.processing_status == 'completed')\
            .order_by(Whiteboard.created_at.desc()).all()
        
        project_data['whiteboards'] = [wb.to_dict() for wb in whiteboards]
        project_data['is_shared'] = True
        
        return jsonify(project_data)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@workspace_bp.route('/dashboard', methods=['GET'])
@login_required
def get_dashboard():
    """Get user dashboard - regular users can access their own dashboard"""
    try:
        user = request.current_user
        
        # Return mock data for user dashboard
        # In production, this would query the database for actual user data
        return jsonify({
            'success': True,
            'stats': {
                'total_projects': 5 if user.is_admin else 2,
                'total_whiteboards': 15 if user.is_admin else 8,
                'completed_whiteboards': 12 if user.is_admin else 6,
                'total_exports': 8 if user.is_admin else 3,
                'processing_rate': 80.0
            },
            'recent_projects': [
                {
                    'id': f'proj-{i+1}',
                    'title': f'Meeting Notes {i+1}',
                    'description': f'Whiteboard analysis for meeting {i+1}',
                    'whiteboard_count': 2 + i,
                    'created_at': f'2024-08-{20+i}T10:00:00Z',
                    'updated_at': f'2024-08-{25+i}T15:30:00Z'
                } for i in range(3)
            ],
            'recent_activity': [
                {
                    'type': 'whiteboard_processed',
                    'project_id': f'proj-{i+1}',
                    'whiteboard_id': f'wb-{i+1}',
                    'filename': f'whiteboard_{i+1}.jpg',
                    'created_at': f'2024-08-{28+i}T12:00:00Z'
                } for i in range(3)
            ]
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@workspace_bp.route('/search', methods=['GET'])
@login_required
def search_projects():
    try:
        user = request.current_user
        query = request.args.get('q', '')
        if not query:
            return jsonify({'error': 'Search query required'}), 400
        
        # Search in project titles and descriptions for current user
        projects = Project.query.filter(
            Project.user_id == user.id,
            db.or_(
                Project.title.contains(query),
                Project.description.contains(query)
            )
        ).limit(20).all()
        
        # Search in whiteboard content for current user (through project)
        whiteboards = Whiteboard.query.join(Project).filter(
            Project.user_id == user.id,
            db.or_(
                Whiteboard.raw_text.contains(query),
                Whiteboard.structured_content.contains(query)
            )
        ).limit(20).all()
        
        results = {
            'projects': [p.to_dict() for p in projects],
            'whiteboards': [wb.to_dict() for wb in whiteboards],
            'total_results': len(projects) + len(whiteboards)
        }
        
        return jsonify(results)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500