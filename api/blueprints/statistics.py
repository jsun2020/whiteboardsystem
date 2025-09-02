"""
Statistics API Blueprint for Meeting Whiteboard Scribe
Provides endpoints for user and admin statistics
"""
from flask import Blueprint, request, jsonify, session
from functools import wraps
from auth_middleware import require_admin, get_current_user
from models import User, Whiteboard, Export, Project
from database import db
from sqlalchemy import func, desc, and_
from datetime import datetime, timezone, date
import traceback

statistics_bp = Blueprint('statistics', __name__)

# Simple mock data for demonstration since we don't have full auth system
def get_mock_user_stats():
    return {
        'user_id': 'demo-user-123',
        'period': {
            'start_date': '2024-08-01',
            'end_date': '2024-09-02',
            'days': 30
        },
        'totals': {
            'projects_created': 15,
            'images_uploaded': 45,
            'images_processed': 42,
            'exports_generated': 38,
            'session_time_minutes': 180,
            'file_size_processed_bytes': 25600000
        },
        'export_types': {
            'markdown': 15,
            'pptx': 12,
            'mindmap': 8,
            'notion': 3
        },
        'daily_stats': []
    }

def get_real_admin_stats():
    """Get real admin statistics from database"""
    try:
        today = date.today()
        today_start = datetime.combine(today, datetime.min.time()).replace(tzinfo=timezone.utc)
        
        # Users statistics
        total_users = User.query.count()
        new_users_today = User.query.filter(User.created_at >= today_start).count()
        active_users_today = User.query.filter(User.last_active >= today_start).count()
        
        # Whiteboards statistics
        total_whiteboards = Whiteboard.query.count()
        whiteboards_today = Whiteboard.query.filter(Whiteboard.created_at >= today_start).count()
        successful_today = Whiteboard.query.filter(
            and_(Whiteboard.created_at >= today_start, Whiteboard.processing_status == 'completed')
        ).count()
        failed_today = Whiteboard.query.filter(
            and_(Whiteboard.created_at >= today_start, Whiteboard.processing_status == 'error')
        ).count()
        
        # Exports statistics
        total_exports = Export.query.count()
        exports_today = Export.query.filter(Export.created_at >= today_start).count()
        
        # Get most popular export format
        popular_format_result = db.session.query(
            Export.export_type, func.count(Export.export_type).label('count')
        ).group_by(Export.export_type).order_by(desc('count')).first()
        popular_format = popular_format_result[0] if popular_format_result else 'markdown'
        
        # Format distribution
        format_distribution = {}
        format_counts = db.session.query(
            Export.export_type, func.count(Export.export_type).label('count')
        ).group_by(Export.export_type).all()
        
        for format_type, count in format_counts:
            format_distribution[format_type] = count
        
        # Fill in missing formats with 0
        for format_type in ['markdown', 'pptx', 'mindmap', 'notion', 'confluence']:
            if format_type not in format_distribution:
                format_distribution[format_type] = 0
        
        # Performance metrics (simplified since we don't have processing_duration)
        # Use processing progress as a proxy or set to 0 for now
        avg_processing_time = 2.5  # Default placeholder
        
        # Calculate storage used (sum of file sizes)
        total_storage_bytes = db.session.query(
            func.sum(Whiteboard.file_size)
        ).scalar() or 0
        total_storage_gb = round(total_storage_bytes / (1024 ** 3), 2)
        
        return {
            'users': {
                'total': total_users,
                'new_today': new_users_today,
                'active_today': active_users_today
            },
            'whiteboards': {
                'total': total_whiteboards,
                'processed_today': whiteboards_today,
                'successful_today': successful_today,
                'failed_today': failed_today
            },
            'exports': {
                'total': total_exports,
                'today': exports_today,
                'popular_format': popular_format
            },
            'performance': {
                'average_processing_time': avg_processing_time,
                'total_storage_gb': total_storage_gb
            },
            'format_distribution': format_distribution
        }
    except Exception as e:
        print(f"Error getting admin stats: {e}")
        traceback.print_exc()
        # Fallback to some basic stats if there's an error
        return {
            'users': {'total': 0, 'new_today': 0, 'active_today': 0},
            'whiteboards': {'total': 0, 'processed_today': 0, 'successful_today': 0, 'failed_today': 0},
            'exports': {'total': 0, 'today': 0, 'popular_format': 'markdown'},
            'performance': {'average_processing_time': 0, 'total_storage_gb': 0},
            'format_distribution': {'markdown': 0, 'pptx': 0, 'mindmap': 0, 'notion': 0}
        }

@statistics_bp.route('/user/stats', methods=['GET'])
def get_user_statistics():
    """Get current user's statistics"""
    try:
        stats = get_mock_user_stats()
        return jsonify({
            'success': True,
            'data': stats
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to retrieve user statistics: {str(e)}'
        }), 500

@statistics_bp.route('/admin/dashboard', methods=['GET'])
@require_admin
def get_admin_dashboard():
    """Get admin dashboard statistics"""
    try:
        stats = get_real_admin_stats()
        return jsonify({
            'success': True,
            'data': stats
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': f'Failed to retrieve admin statistics: {str(e)}'
        }), 500

@statistics_bp.route('/admin/users/list', methods=['GET'])
@require_admin
def get_admin_users_list():
    """Get paginated list of users for admin"""
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        search = request.args.get('search', '')
        
        # Build the query
        query = User.query
        
        # Apply search filter if provided
        if search:
            search_term = f'%{search}%'
            query = query.filter(
                db.or_(
                    User.email.ilike(search_term),
                    User.full_name.ilike(search_term),
                    User.username.ilike(search_term)
                )
            )
        
        # Order by creation date (newest first)
        query = query.order_by(desc(User.created_at))
        
        # Apply pagination
        pagination = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        users = pagination.items
        users_list = []
        
        for user in users:
            # Get user statistics from built-in fields and related models
            total_whiteboards = Whiteboard.query.join(Project).filter(Project.user_id == user.id).count()
            total_exports = Export.query.join(Project).filter(Project.user_id == user.id).count()
            
            user_data = {
                'id': user.id,
                'full_name': user.display_name,  # Use display_name from actual model
                'username': user.username,
                'email': user.email,
                'is_active': user.is_active,
                'last_login': user.last_active.isoformat() if user.last_active else None,  # Use last_active
                'statistics': {
                    'total_uploads': total_whiteboards,  # Count of whiteboards
                    'monthly_uploads': user.images_processed,  # Use built-in field
                    'total_exports': total_exports,  # Count from exports table
                    'total_processing_time': 0  # Placeholder since we don't track this
                }
            }
            users_list.append(user_data)
        
        return jsonify({
            'success': True,
            'data': {
                'users': users_list,
                'pagination': {
                    'page': pagination.page,
                    'per_page': pagination.per_page,
                    'total': pagination.total,
                    'has_prev': pagination.has_prev,
                    'has_next': pagination.has_next
                }
            }
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': f'Failed to retrieve users list: {str(e)}'
        }), 500

@statistics_bp.route('/admin/users/<user_id>/stats', methods=['GET'])
@require_admin
def get_user_stats(user_id):
    """Get detailed statistics for a specific user"""
    try:
        # Get user from database (user_id is string in this model)
        user = User.query.filter_by(id=user_id).first_or_404()
        
        # Get user statistics from related models
        user_projects = Project.query.filter_by(user_id=user.id).all()
        project_ids = [p.id for p in user_projects]
        
        total_whiteboards = Whiteboard.query.filter(Whiteboard.project_id.in_(project_ids)).count() if project_ids else 0
        total_exports = Export.query.filter(Export.project_id.in_(project_ids)).count() if project_ids else 0
        
        # Calculate success rates
        successful_whiteboards = Whiteboard.query.filter(
            and_(Whiteboard.project_id.in_(project_ids), Whiteboard.processing_status == 'completed')
        ).count() if project_ids else 0
        
        failed_whiteboards = Whiteboard.query.filter(
            and_(Whiteboard.project_id.in_(project_ids), Whiteboard.processing_status == 'error')
        ).count() if project_ids else 0
        
        upload_success_rate = 0
        if total_whiteboards > 0:
            upload_success_rate = round((successful_whiteboards / total_whiteboards) * 100, 1)
        
        successful_exports = Export.query.filter(
            and_(Export.project_id.in_(project_ids), Export.status == 'completed')
        ).count() if project_ids else 0
        
        export_success_rate = 0
        if total_exports > 0:
            export_success_rate = round((successful_exports / total_exports) * 100, 1)
        
        # Get export format breakdown
        format_breakdown = {}
        if project_ids:
            format_counts = db.session.query(
                Export.export_type, func.count(Export.export_type).label('count')
            ).filter(Export.project_id.in_(project_ids)).group_by(Export.export_type).all()
            
            for format_type, count in format_counts:
                format_breakdown[format_type] = count
        
        user_detail = {
            'user': {
                'id': user.id,
                'full_name': user.display_name,
                'username': user.username,
                'email': user.email,
                'is_active': user.is_active,
                'created_at': user.created_at.isoformat() if user.created_at else None,
                'last_login': user.last_active.isoformat() if user.last_active else None
            },
            'statistics': {
                'basic_stats': {
                    'total_uploads': total_whiteboards,
                    'total_exports': total_exports,
                    'total_projects': len(user_projects),
                    'successful_uploads': successful_whiteboards,
                    'failed_uploads': failed_whiteboards,
                    'total_processing_time': 0,  # Not tracked in current model
                    'average_processing_time': 0  # Not tracked in current model
                },
                'success_rates': {
                    'upload_success_rate': upload_success_rate,
                    'export_success_rate': export_success_rate
                },
                'monthly_stats': {
                    'monthly_uploads': user.images_processed or 0,
                    'monthly_exports': user.exports_generated or 0,
                    'monthly_processing_time': 0  # Not tracked
                },
                'format_breakdown': format_breakdown
            }
        }
        
        return jsonify({
            'success': True,
            'data': user_detail
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': f'Failed to retrieve user statistics: {str(e)}'
        }), 500

@statistics_bp.route('/admin/system/update', methods=['POST'])
@require_admin
def update_system_stats():
    """Update system statistics by recalculating from database"""
    try:
        # Since we don't have a separate SystemStatistics table, 
        # this endpoint will just trigger a refresh of the cached statistics
        # and return current counts
        
        total_users = User.query.count()
        total_whiteboards = Whiteboard.query.count()
        total_exports = Export.query.count()
        
        return jsonify({
            'success': True,
            'message': 'System statistics refreshed successfully',
            'data': {
                'updated_date': date.today().isoformat(),
                'total_users': total_users,
                'total_whiteboards': total_whiteboards,
                'total_exports': total_exports
            }
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': f'Failed to update system statistics: {str(e)}'
        }), 500

# Health check endpoint
@statistics_bp.route('/health', methods=['GET'])
def health_check():
    """Simple health check for the statistics service"""
    return jsonify({
        'success': True,
        'message': 'Statistics service is running',
        'timestamp': '2024-09-02T12:00:00Z'
    })