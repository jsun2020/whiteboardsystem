from flask import Blueprint, request, jsonify
from models.project import Project
from models.whiteboard import Whiteboard
from models.export import Export
from models.user import User
from database import db
from datetime import datetime, timedelta
import uuid

workspace_bp = Blueprint('workspace', __name__)

@workspace_bp.route('/projects', methods=['GET'])
def list_projects():
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        sort_by = request.args.get('sort_by', 'updated_at')
        order = request.args.get('order', 'desc')
        
        query = Project.query
        
        # Add sorting
        if sort_by == 'created_at':
            query = query.order_by(Project.created_at.desc() if order == 'desc' else Project.created_at.asc())
        elif sort_by == 'title':
            query = query.order_by(Project.title.desc() if order == 'desc' else Project.title.asc())
        else:  # default to updated_at
            query = query.order_by(Project.updated_at.desc() if order == 'desc' else Project.updated_at.asc())
        
        # Paginate
        projects_pagination = query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        projects = []
        for project in projects_pagination.items:
            project_data = project.to_dict()
            # Add recent whiteboard info
            recent_whiteboard = Whiteboard.query.filter_by(project_id=project.id)\
                .order_by(Whiteboard.created_at.desc()).first()
            if recent_whiteboard:
                project_data['last_activity'] = recent_whiteboard.created_at.isoformat()
            projects.append(project_data)
        
        return jsonify({
            'projects': projects,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': projects_pagination.total,
                'pages': projects_pagination.pages,
                'has_next': projects_pagination.has_next,
                'has_prev': projects_pagination.has_prev
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@workspace_bp.route('/projects', methods=['POST'])
def create_project():
    try:
        data = request.get_json()
        
        project = Project(
            title=data.get('title', 'Untitled Project'),
            description=data.get('description', ''),
            status='draft'
        )
        
        db.session.add(project)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'project': project.to_dict()
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@workspace_bp.route('/projects/<project_id>', methods=['GET'])
def get_project(project_id):
    try:
        project = Project.query.get_or_404(project_id)
        
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
        return jsonify({'error': str(e)}), 500

@workspace_bp.route('/projects/<project_id>', methods=['PUT'])
def update_project(project_id):
    try:
        data = request.get_json()
        project = Project.query.get_or_404(project_id)
        
        if 'title' in data:
            project.title = data['title']
        if 'description' in data:
            project.description = data['description']
        if 'status' in data:
            project.status = data['status']
        
        project.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'project': project.to_dict()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@workspace_bp.route('/projects/<project_id>', methods=['DELETE'])
def delete_project(project_id):
    try:
        project = Project.query.get_or_404(project_id)
        
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
def create_share_link():
    try:
        data = request.get_json()
        project_id = data.get('project_id')
        
        if not project_id:
            return jsonify({'error': 'Project ID required'}), 400
        
        project = Project.query.get_or_404(project_id)
        
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
def get_dashboard():
    try:
        # Get recent projects
        recent_projects = Project.query.order_by(Project.updated_at.desc()).limit(5).all()
        
        # Get statistics
        total_projects = Project.query.count()
        total_whiteboards = Whiteboard.query.count()
        completed_whiteboards = Whiteboard.query.filter_by(processing_status='completed').count()
        total_exports = Export.query.count()
        
        # Get recent activity
        recent_whiteboards = Whiteboard.query.order_by(Whiteboard.created_at.desc()).limit(5).all()
        
        return jsonify({
            'stats': {
                'total_projects': total_projects,
                'total_whiteboards': total_whiteboards,
                'completed_whiteboards': completed_whiteboards,
                'total_exports': total_exports,
                'processing_rate': (completed_whiteboards / total_whiteboards * 100) if total_whiteboards > 0 else 0
            },
            'recent_projects': [p.to_dict() for p in recent_projects],
            'recent_activity': [
                {
                    'type': 'whiteboard_processed',
                    'project_id': wb.project_id,
                    'whiteboard_id': wb.id,
                    'filename': wb.filename,
                    'created_at': wb.created_at.isoformat()
                } for wb in recent_whiteboards
            ]
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@workspace_bp.route('/search', methods=['GET'])
def search_projects():
    try:
        query = request.args.get('q', '')
        if not query:
            return jsonify({'error': 'Search query required'}), 400
        
        # Search in project titles and descriptions
        projects = Project.query.filter(
            db.or_(
                Project.title.contains(query),
                Project.description.contains(query)
            )
        ).limit(20).all()
        
        # Search in whiteboard content
        whiteboards = Whiteboard.query.filter(
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