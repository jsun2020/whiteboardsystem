"""
Statistics API Blueprint for Meeting Whiteboard Scribe
Provides endpoints for user and admin statistics
"""
from flask import Blueprint, request, jsonify, g
from flask_login import login_required, current_user
from functools import wraps
from services.stats_service import StatisticsService
from models.user import User
import traceback

statistics_bp = Blueprint('statistics', __name__)

def admin_required(f):
    """Decorator to require admin privileges"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            return jsonify({
                'success': False,
                'error': 'Admin privileges required'
            }), 403
        return f(*args, **kwargs)
    return decorated_function

@statistics_bp.route('/user/stats', methods=['GET'])
def get_user_statistics():
    """Get current user's statistics"""
    try:
        # For now, use a demo user ID - this should be replaced with proper auth
        user_id = "demo-user-123"
        days = request.args.get('days', 30, type=int)
        
        stats = StatisticsService.get_user_statistics(user_id, days)
        return jsonify({
            'success': True,
            'data': stats
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to retrieve user statistics: {str(e)}'
        }), 500

@statistics_bp.route('/user/trends', methods=['GET'])
@login_required
def get_user_trends():
    """Get user usage trends"""
    try:
        days = request.args.get('days', 30, type=int)
        if days < 1 or days > 365:
            days = 30
        
        trends = StatisticsService.get_usage_trends(current_user.id, days)
        return jsonify({
            'success': True,
            'data': trends
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to retrieve usage trends: {str(e)}'
        }), 500

@statistics_bp.route('/admin/dashboard', methods=['GET'])
def get_admin_dashboard():
    """Get admin dashboard statistics"""
    try:
        days = request.args.get('days', 30, type=int)
        stats = StatisticsService.get_admin_dashboard_stats(days)
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

@statistics_bp.route('/admin/users/<int:user_id>/stats', methods=['GET'])
@login_required
@admin_required
def get_user_statistics_admin(user_id):
    """Get specific user's statistics (admin only)"""
    try:
        # Check if user exists
        user = User.query.get(user_id)
        if not user:
            return jsonify({
                'success': False,
                'error': 'User not found'
            }), 404
        
        stats = StatisticsService.get_user_statistics(user_id)
        return jsonify({
            'success': True,
            'data': {
                'user': user.to_dict(),
                'statistics': stats
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to retrieve user statistics: {str(e)}'
        }), 500

@statistics_bp.route('/admin/system/update', methods=['POST'])
@login_required
@admin_required
def update_system_statistics():
    """Manually trigger system statistics update"""
    try:
        stats = StatisticsService.update_system_stats()
        return jsonify({
            'success': True,
            'message': 'System statistics updated successfully',
            'data': stats
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': f'Failed to update system statistics: {str(e)}'
        }), 500

@statistics_bp.route('/admin/users/list', methods=['GET'])
@login_required
@admin_required
def get_users_list():
    """Get paginated list of users with basic stats"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        search = request.args.get('search', '', type=str)
        
        # Limit per_page to prevent excessive queries
        per_page = min(per_page, 100)
        
        # Build query
        query = User.query
        if search:
            query = query.filter(
                User.username.ilike(f'%{search}%') |
                User.email.ilike(f'%{search}%') |
                User.full_name.ilike(f'%{search}%')
            )
        
        # Order by creation date (newest first)
        query = query.order_by(User.created_at.desc())
        
        # Paginate
        users_pagination = query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        users_data = []
        for user in users_pagination.items:
            user_dict = user.to_dict()
            # Add basic statistics
            if user.user_stats:
                user_dict['statistics'] = {
                    'total_uploads': user.user_stats.total_uploads or 0,
                    'total_exports': user.user_stats.total_exports or 0,
                    'total_processing_time': user.user_stats.total_processing_time or 0,
                    'monthly_uploads': user.user_stats.monthly_uploads or 0
                }
            else:
                user_dict['statistics'] = {
                    'total_uploads': 0,
                    'total_exports': 0,
                    'total_processing_time': 0,
                    'monthly_uploads': 0
                }
            users_data.append(user_dict)
        
        return jsonify({
            'success': True,
            'data': {
                'users': users_data,
                'pagination': {
                    'page': page,
                    'pages': users_pagination.pages,
                    'per_page': per_page,
                    'total': users_pagination.total,
                    'has_next': users_pagination.has_next,
                    'has_prev': users_pagination.has_prev
                }
            }
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': f'Failed to retrieve users list: {str(e)}'
        }), 500

@statistics_bp.route('/public/summary', methods=['GET'])
def get_public_summary():
    """Get public summary statistics (no authentication required)"""
    try:
        # Only show basic, non-sensitive statistics
        from models import User, Whiteboard, Export
        
        total_users = User.query.filter_by(is_active=True).count()
        total_whiteboards = Whiteboard.query.count()
        total_exports = Export.query.count()
        
        # Calculate success rate
        successful_processes = Whiteboard.query.filter_by(
            status='completed'
        ).count()
        
        success_rate = 0
        if total_whiteboards > 0:
            success_rate = (successful_processes / total_whiteboards) * 100
        
        return jsonify({
            'success': True,
            'data': {
                'total_users': total_users,
                'total_whiteboards_processed': total_whiteboards,
                'total_exports_generated': total_exports,
                'success_rate': round(success_rate, 1)
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to retrieve public statistics: {str(e)}'
        }), 500

# Error handlers
@statistics_bp.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': 'Endpoint not found'
    }), 404

@statistics_bp.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'error': 'Internal server error'
    }), 500