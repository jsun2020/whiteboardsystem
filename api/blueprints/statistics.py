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

# Health check endpoint
@statistics_bp.route('/health', methods=['GET'])
def health_check():
    """Simple health check for the statistics service"""
    return jsonify({
        'success': True,
        'message': 'Statistics service is running',
        'timestamp': '2024-09-02T12:00:00Z'
    })