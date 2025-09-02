"""
Statistics Service for Meeting Whiteboard Scribe
Handles user statistics tracking and aggregation
"""
from datetime import datetime, date, timezone, timedelta
from sqlalchemy import func, and_
from database import db, UserStatistics, SystemStatistics
from models.user import User
from models.project import Project
from models.whiteboard import Whiteboard
from models.export import Export

class StatisticsService:
    
    @staticmethod
    def get_or_create_user_stats(user_id: str, target_date: date = None) -> UserStatistics:
        """Get or create user statistics record for a specific date"""
        if target_date is None:
            target_date = datetime.now(timezone.utc).date()
        
        stats = UserStatistics.query.filter_by(
            user_id=user_id,
            date=target_date
        ).first()
        
        if not stats:
            stats = UserStatistics(
                user_id=user_id,
                date=target_date
            )
            db.session.add(stats)
            db.session.commit()
        
        return stats
    
    @staticmethod
    def update_user_activity(user_id: str, activity_type: str, **kwargs):
        """Update user statistics based on activity"""
        stats = StatisticsService.get_or_create_user_stats(user_id)
        
        if activity_type == 'project_created':
            stats.projects_created_today += 1
        elif activity_type == 'image_uploaded':
            stats.images_uploaded_today += 1
            if 'file_size' in kwargs:
                stats.total_file_size_processed += kwargs['file_size']
        elif activity_type == 'image_processed':
            stats.images_processed_today += 1
        elif activity_type == 'export_generated':
            stats.exports_generated_today += 1
            if 'export_type' in kwargs:
                export_types = stats.get_export_types_dict()
                export_type = kwargs['export_type']
                export_types[export_type] = export_types.get(export_type, 0) + 1
                stats.set_export_types_dict(export_types)
        elif activity_type == 'session_time':
            if 'duration_minutes' in kwargs:
                stats.session_duration += kwargs['duration_minutes']
        
        db.session.commit()
    
    @staticmethod
    def get_user_statistics(user_id: str, days: int = 30) -> dict:
        """Get user statistics for the specified number of days"""
        end_date = datetime.now(timezone.utc).date()
        start_date = end_date - timedelta(days=days-1)
        
        stats = UserStatistics.query.filter(
            and_(
                UserStatistics.user_id == user_id,
                UserStatistics.date >= start_date,
                UserStatistics.date <= end_date
            )
        ).order_by(UserStatistics.date.desc()).all()
        
        # Calculate totals
        total_projects = sum(s.projects_created_today for s in stats)
        total_images_uploaded = sum(s.images_uploaded_today for s in stats)
        total_images_processed = sum(s.images_processed_today for s in stats)
        total_exports = sum(s.exports_generated_today for s in stats)
        total_session_time = sum(s.session_duration for s in stats)
        total_file_size = sum(s.total_file_size_processed for s in stats)
        
        # Aggregate export types
        all_export_types = {}
        for s in stats:
            export_types = s.get_export_types_dict()
            for export_type, count in export_types.items():
                all_export_types[export_type] = all_export_types.get(export_type, 0) + count
        
        # Recent activity (last 7 days)
        recent_stats = [s for s in stats if s.date >= end_date - timedelta(days=6)]
        
        return {
            'user_id': user_id,
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'days': days
            },
            'totals': {
                'projects_created': total_projects,
                'images_uploaded': total_images_uploaded,
                'images_processed': total_images_processed,
                'exports_generated': total_exports,
                'session_time_minutes': total_session_time,
                'file_size_processed_bytes': total_file_size
            },
            'export_types': all_export_types,
            'daily_stats': [s.to_dict() for s in stats],
            'recent_activity': [s.to_dict() for s in recent_stats]
        }
    
    @staticmethod
    def get_admin_dashboard_stats(days: int = 30) -> dict:
        """Get comprehensive statistics for admin dashboard"""
        end_date = datetime.now(timezone.utc).date()
        start_date = end_date - timedelta(days=days-1)
        
        # System statistics
        system_stats = SystemStatistics.query.filter(
            and_(
                SystemStatistics.date >= start_date,
                SystemStatistics.date <= end_date
            )
        ).order_by(SystemStatistics.date.desc()).all()
        
        # User statistics
        user_count = User.query.count()
        active_users_today = UserStatistics.query.filter(
            and_(
                UserStatistics.date == end_date,
                (UserStatistics.projects_created_today > 0) |
                (UserStatistics.images_uploaded_today > 0) |
                (UserStatistics.images_processed_today > 0) |
                (UserStatistics.exports_generated_today > 0)
            )
        ).count()
        
        # Project statistics
        total_projects = Project.query.count()
        projects_today = Project.query.filter(
            func.date(Project.created_at) == end_date
        ).count()
        
        # Whiteboard statistics
        total_whiteboards = Whiteboard.query.count()
        whiteboards_today = Whiteboard.query.filter(
            func.date(Whiteboard.created_at) == end_date
        ).count()
        
        # Export statistics
        total_exports = Export.query.count()
        exports_today = Export.query.filter(
            func.date(Export.created_at) == end_date
        ).count()
        
        # Calculate totals from system stats
        total_users_registered = sum(s.total_users_registered_today for s in system_stats)
        total_projects_period = sum(s.total_projects_created_today for s in system_stats)
        total_images_uploaded = sum(s.total_images_uploaded_today for s in system_stats)
        total_images_processed = sum(s.total_images_processed_today for s in system_stats)
        total_exports_period = sum(s.total_exports_generated_today for s in system_stats)
        
        # Aggregate export types
        all_export_breakdown = {}
        for s in system_stats:
            breakdown = s.get_export_breakdown_dict()
            for export_type, count in breakdown.items():
                all_export_breakdown[export_type] = all_export_breakdown.get(export_type, 0) + count
        
        # Top users by activity
        top_users = db.session.query(
            UserStatistics.user_id,
            User.username,
            User.display_name,
            func.sum(UserStatistics.projects_created_today).label('total_projects'),
            func.sum(UserStatistics.images_processed_today).label('total_processed'),
            func.sum(UserStatistics.exports_generated_today).label('total_exports')
        ).join(User, UserStatistics.user_id == User.id).filter(
            UserStatistics.date >= start_date
        ).group_by(
            UserStatistics.user_id, User.username, User.display_name
        ).order_by(
            func.sum(UserStatistics.images_processed_today).desc()
        ).limit(10).all()
        
        return {
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'days': days
            },
            'overview': {
                'total_users': user_count,
                'active_users_today': active_users_today,
                'total_projects': total_projects,
                'projects_created_today': projects_today,
                'total_whiteboards': total_whiteboards,
                'whiteboards_uploaded_today': whiteboards_today,
                'total_exports': total_exports,
                'exports_generated_today': exports_today
            },
            'period_totals': {
                'users_registered': total_users_registered,
                'projects_created': total_projects_period,
                'images_uploaded': total_images_uploaded,
                'images_processed': total_images_processed,
                'exports_generated': total_exports_period
            },
            'export_breakdown': all_export_breakdown,
            'daily_system_stats': [s.to_dict() for s in system_stats],
            'top_users': [
                {
                    'user_id': user.user_id,
                    'username': user.username,
                    'display_name': user.display_name,
                    'projects_created': int(user.total_projects or 0),
                    'images_processed': int(user.total_processed or 0),
                    'exports_generated': int(user.total_exports or 0)
                } for user in top_users
            ]
        }