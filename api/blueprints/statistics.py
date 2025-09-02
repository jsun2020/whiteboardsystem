"""
Statistics API Blueprint for Meeting Whiteboard Scribe
Provides endpoints for user and admin statistics
"""
from flask import Blueprint, request, jsonify, session
from functools import wraps
from auth_middleware import require_admin, get_current_user
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

def get_mock_admin_stats():
    return {
        'users': {
            'total': 125,
            'new_today': 3,
            'active_today': 8
        },
        'whiteboards': {
            'total': 890,
            'processed_today': 12,
            'successful_today': 11,
            'failed_today': 1
        },
        'exports': {
            'total': 1250,
            'today': 15,
            'popular_format': 'markdown'
        },
        'performance': {
            'average_processing_time': 2.3,
            'total_storage_gb': 12.4
        },
        'format_distribution': {
            'markdown': 45,
            'pptx': 30,
            'mindmap': 15,
            'notion': 10
        }
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
        stats = get_mock_admin_stats()
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
        
        # Mock user data
        mock_users = [
            {
                'id': 1,
                'full_name': 'John Doe',
                'username': 'johndoe',
                'email': 'john@example.com',
                'is_active': True,
                'last_login': '2024-09-01T10:30:00Z',
                'statistics': {
                    'total_uploads': 25,
                    'monthly_uploads': 8,
                    'total_exports': 18,
                    'total_processing_time': 120
                }
            },
            {
                'id': 2,
                'full_name': 'Jane Smith',
                'username': 'janesmith',
                'email': 'jane@example.com',
                'is_active': True,
                'last_login': '2024-09-02T14:15:00Z',
                'statistics': {
                    'total_uploads': 42,
                    'monthly_uploads': 12,
                    'total_exports': 35,
                    'total_processing_time': 210
                }
            },
            {
                'id': 3,
                'full_name': 'Admin User',
                'username': 'jason',
                'email': 'jsun2016@live.com',
                'is_active': True,
                'last_login': '2024-09-02T16:00:00Z',
                'statistics': {
                    'total_uploads': 100,
                    'monthly_uploads': 25,
                    'total_exports': 85,
                    'total_processing_time': 450
                }
            }
        ]
        
        # Filter by search if provided
        if search:
            mock_users = [u for u in mock_users if search.lower() in u['email'].lower() or search.lower() in u['full_name'].lower()]
        
        # Simple pagination
        total = len(mock_users)
        start = (page - 1) * per_page
        end = start + per_page
        users_page = mock_users[start:end]
        
        return jsonify({
            'success': True,
            'data': {
                'users': users_page,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': total,
                    'has_prev': page > 1,
                    'has_next': end < total
                }
            }
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': f'Failed to retrieve users list: {str(e)}'
        }), 500

@statistics_bp.route('/admin/users/<int:user_id>/stats', methods=['GET'])
@require_admin
def get_user_stats(user_id):
    """Get detailed statistics for a specific user"""
    try:
        # Mock user detail data
        user_detail = {
            'user': {
                'id': user_id,
                'full_name': 'John Doe' if user_id == 1 else 'Jane Smith',
                'username': 'johndoe' if user_id == 1 else 'janesmith',
                'email': f'user{user_id}@example.com',
                'is_active': True
            },
            'statistics': {
                'basic_stats': {
                    'total_uploads': 25,
                    'total_exports': 18,
                    'total_projects': 10
                },
                'success_rates': {
                    'upload_success_rate': 95,
                    'export_success_rate': 90
                }
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
    """Update system statistics (mock implementation)"""
    try:
        # In a real implementation, this would refresh/recalculate statistics
        # For now, just return success
        return jsonify({
            'success': True,
            'message': 'System statistics updated successfully'
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