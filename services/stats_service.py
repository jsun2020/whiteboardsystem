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
        if target_date is None:
            target_date = datetime.now(timezone.utc).date()
        
        stats = UserStatistics.query.filter_by(
            user_id=user_id,
            date=target_date
        ).first()
        
        if not stats:
            stats = UserStatistics(user_id=user_id, date=target_date)
            db.session.add(stats)
            db.session.commit()
        
        return stats
    
    @staticmethod
    def update_user_activity(user_id: str, activity_type: str, **kwargs):
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
            'daily_stats': [s.to_dict() for s in stats]
        }
    
    @staticmethod
    def get_admin_dashboard_stats(days: int = 30) -> dict:
        end_date = datetime.now(timezone.utc).date()
        
        # User statistics
        user_count = User.query.count()
        
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
        
        return {
            'overview': {
                'total_users': user_count,
                'total_projects': total_projects,
                'projects_created_today': projects_today,
                'total_whiteboards': total_whiteboards,
                'whiteboards_uploaded_today': whiteboards_today,
                'total_exports': total_exports,
                'exports_generated_today': exports_today
            }
        }