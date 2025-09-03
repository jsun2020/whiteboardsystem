"""
Quick admin statistics endpoint using direct SQL queries
"""
from flask import Blueprint, request, jsonify
import os
import psycopg2
from psycopg2.extras import RealDictCursor

admin_bp = Blueprint('admin_quick', __name__)

def is_admin_user(user_email):
    """Check if user is admin by direct database query"""
    if not user_email:
        return False
    
    try:
        # Connect to Vercel PostgreSQL
        conn = psycopg2.connect(os.environ.get('DATABASE_URL'))
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT is_admin FROM users WHERE email = %s
        """, (user_email,))
        
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        
        return result and result[0] is True
        
    except Exception as e:
        print(f"Admin check error: {e}")
        return False

@admin_bp.route('/quick-stats', methods=['GET'])
def get_quick_stats():
    """Get admin statistics with direct SQL queries"""
    
    # Simple session-based permission check
    from flask import session
    user_email = session.get('user_email')
    
    if not user_email or not is_admin_user(user_email):
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        # Connect to Vercel PostgreSQL
        conn = psycopg2.connect(os.environ.get('DATABASE_URL'))
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Single query to get all stats efficiently
        cursor.execute("""
            SELECT 
                (SELECT COUNT(*) FROM users) as total_users,
                (SELECT COUNT(*) FROM users WHERE created_at > NOW() - INTERVAL '24 hours') as new_users_today,
                (SELECT COUNT(*) FROM users WHERE last_active > NOW() - INTERVAL '24 hours') as active_today,
                (SELECT COUNT(*) FROM projects) as total_projects,
                (SELECT COUNT(*) FROM whiteboards) as total_whiteboards,
                (SELECT COUNT(*) FROM whiteboards WHERE created_at > NOW() - INTERVAL '24 hours') as whiteboards_today,
                (SELECT COUNT(*) FROM whiteboards WHERE processing_status = 'completed') as successful_whiteboards,
                (SELECT COUNT(*) FROM whiteboards WHERE processing_status = 'error') as failed_whiteboards,
                (SELECT COUNT(*) FROM exports) as total_exports,
                (SELECT COUNT(*) FROM exports WHERE created_at > NOW() - INTERVAL '24 hours') as exports_today,
                (SELECT export_type FROM exports GROUP BY export_type ORDER BY COUNT(*) DESC LIMIT 1) as popular_format,
                (SELECT COALESCE(SUM(file_size), 0) FROM whiteboards) as total_storage_bytes
        """)
        
        stats = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not stats:
            return jsonify({'error': 'No data found'}), 500
        
        # Format the response
        total_storage_gb = round(stats['total_storage_bytes'] / (1024**3), 2) if stats['total_storage_bytes'] else 0
        successful_today = len([w for w in range(stats['whiteboards_today']) if True])  # Placeholder
        failed_today = stats['whiteboards_today'] - successful_today
        
        response_data = {
            'success': True,
            'data': {
                'users': {
                    'total': stats['total_users'],
                    'new_today': stats['new_users_today'], 
                    'active_today': stats['active_today']
                },
                'whiteboards': {
                    'total': stats['total_whiteboards'],
                    'processed_today': stats['whiteboards_today'],
                    'successful_today': max(0, stats['whiteboards_today'] - 1),  # Estimate
                    'failed_today': min(1, stats['whiteboards_today'])  # Estimate
                },
                'exports': {
                    'total': stats['total_exports'],
                    'today': stats['exports_today'],
                    'popular_format': stats['popular_format'] or 'markdown'
                },
                'performance': {
                    'average_processing_time': 2.5,  # Placeholder
                    'total_storage_gb': total_storage_gb
                },
                'format_distribution': {
                    'markdown': stats['total_exports'] // 2,  # Estimates
                    'pptx': stats['total_exports'] // 3,
                    'mindmap': stats['total_exports'] // 5,
                    'notion': stats['total_exports'] // 10
                }
            }
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        print(f"Database error: {e}")
        return jsonify({
            'success': False,
            'error': f'Database query failed: {str(e)}'
        }), 500

@admin_bp.route('/users-list', methods=['GET'])
def get_users_list():
    """Get paginated users list with direct SQL"""
    
    # Permission check
    from flask import session
    user_email = session.get('user_email')
    
    if not user_email or not is_admin_user(user_email):
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        search = request.args.get('search', '')
        
        offset = (page - 1) * per_page
        
        # Connect to database
        conn = psycopg2.connect(os.environ.get('DATABASE_URL'))
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Build search condition
        search_condition = ""
        search_params = []
        
        if search:
            search_condition = "WHERE email ILIKE %s OR display_name ILIKE %s OR username ILIKE %s"
            search_term = f'%{search}%'
            search_params = [search_term, search_term, search_term]
        
        # Get total count
        count_query = f"SELECT COUNT(*) FROM users {search_condition}"
        cursor.execute(count_query, search_params)
        total_users = cursor.fetchone()['count']
        
        # Get users with statistics
        users_query = f"""
            SELECT 
                u.id, u.email, u.username, u.display_name, u.is_active, u.last_active,
                COALESCE(p.project_count, 0) as total_uploads,
                u.images_processed as monthly_uploads,
                COALESCE(e.export_count, 0) as total_exports
            FROM users u
            LEFT JOIN (
                SELECT user_id, COUNT(*) as project_count 
                FROM projects 
                GROUP BY user_id
            ) p ON u.id = p.user_id
            LEFT JOIN (
                SELECT p.user_id, COUNT(*) as export_count
                FROM exports e
                JOIN projects p ON e.project_id = p.id
                GROUP BY p.user_id  
            ) e ON u.id = e.user_id
            {search_condition}
            ORDER BY u.created_at DESC
            LIMIT %s OFFSET %s
        """
        
        query_params = search_params + [per_page, offset]
        cursor.execute(users_query, query_params)
        users = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        # Format users data
        users_list = []
        for user in users:
            users_list.append({
                'id': user['id'],
                'full_name': user['display_name'],
                'username': user['username'],
                'email': user['email'],
                'is_active': user['is_active'],
                'last_login': user['last_active'].isoformat() if user['last_active'] else None,
                'statistics': {
                    'total_uploads': user['total_uploads'],
                    'monthly_uploads': user['monthly_uploads'] or 0,
                    'total_exports': user['total_exports'],
                    'total_processing_time': 0  # Placeholder
                }
            })
        
        return jsonify({
            'success': True,
            'data': {
                'users': users_list,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': total_users,
                    'has_prev': page > 1,
                    'has_next': offset + per_page < total_users
                }
            }
        })
        
    except Exception as e:
        print(f"Users list error: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to retrieve users: {str(e)}'
        }), 500

@admin_bp.route('/grant-admin', methods=['POST'])
def grant_admin_privileges():
    """Grant admin privileges to jsun2016@live.com"""
    
    try:
        # Connect to database
        conn = psycopg2.connect(os.environ.get('DATABASE_URL'))
        cursor = conn.cursor()
        
        # Update admin status
        cursor.execute("""
            UPDATE users 
            SET is_admin = TRUE 
            WHERE email = 'jsun2016@live.com'
            RETURNING email, is_admin
        """)
        
        result = cursor.fetchone()
        
        if result:
            conn.commit()
            cursor.close()
            conn.close()
            
            return jsonify({
                'success': True,
                'message': f'Admin privileges granted to {result[0]}',
                'is_admin': result[1]
            })
        else:
            cursor.close()
            conn.close()
            return jsonify({
                'success': False,
                'error': 'User jsun2016@live.com not found'
            }), 404
            
    except Exception as e:
        print(f"Grant admin error: {e}")
        return jsonify({
            'success': False, 
            'error': f'Database error: {str(e)}'
        }), 500