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
    def update_upload_stats(user_id: int, file_size: int, success: bool = True):
        """Update user upload statistics"""
        stats = StatisticsService.get_or_create_user_stats(user_id)
        
        stats.total_uploads += 1
        if success:
            stats.successful_uploads += 1
            stats.total_upload_size += file_size
        else:
            stats.failed_uploads += 1
        
        # Update monthly stats
        StatisticsService._check_monthly_reset(stats)
        stats.monthly_uploads += 1
        
        stats.updated_at = datetime.now(timezone.utc)
        db.session.commit()
    
    @staticmethod
    def update_processing_stats(user_id: int, processing_time: float, success: bool = True):
        """Update user processing statistics"""
        stats = StatisticsService.get_or_create_user_stats(user_id)
        
        if success:
            stats.successful_processes += 1
            stats.total_processing_time += processing_time
            stats.monthly_processing_time += processing_time
            
            # Calculate new average
            if stats.successful_processes > 0:
                stats.average_processing_time = stats.total_processing_time / stats.successful_processes
        else:
            stats.failed_processes += 1
        
        stats.updated_at = datetime.now(timezone.utc)
        db.session.commit()
    
    @staticmethod
    def update_export_stats(user_id: int, export_format: str, success: bool = True):
        """Update user export statistics"""
        stats = StatisticsService.get_or_create_user_stats(user_id)
        
        if success:
            stats.total_exports += 1
            stats.monthly_exports += 1
            
            # Update format-specific counts
            format_counts = stats.exports_by_format or {}
            format_counts[export_format] = format_counts.get(export_format, 0) + 1
            stats.exports_by_format = format_counts
        
        stats.updated_at = datetime.now(timezone.utc)
        db.session.commit()
    
    @staticmethod
    def update_download_stats(user_id: int):
        """Update download statistics"""
        stats = StatisticsService.get_or_create_user_stats(user_id)
        stats.total_downloads += 1
        stats.updated_at = datetime.now(timezone.utc)
        db.session.commit()
    
    @staticmethod
    def update_activity_patterns(user_id: int):
        """Update user activity patterns based on current time"""
        stats = StatisticsService.get_or_create_user_stats(user_id)
        now = datetime.now(timezone.utc)
        
        # Update most active day
        day_name = calendar.day_name[now.weekday()].lower()
        stats.most_active_day = day_name
        
        # Update most active hour
        stats.most_active_hour = now.hour
        
        stats.updated_at = now
        db.session.commit()
    
    @staticmethod
    def get_user_statistics(user_id: int) -> dict:
        """Get comprehensive user statistics"""
        stats = StatisticsService.get_or_create_user_stats(user_id)
        
        # Get additional metrics from related tables
        user_whiteboards = Whiteboard.query.filter_by(user_id=user_id).all()
        user_exports = Export.query.filter_by(user_id=user_id).all()
        
        # Calculate success rates
        total_uploads = stats.total_uploads or 0
        upload_success_rate = (stats.successful_uploads / total_uploads * 100) if total_uploads > 0 else 0
        
        total_processes = (stats.successful_processes or 0) + (stats.failed_processes or 0)
        process_success_rate = (stats.successful_processes / total_processes * 100) if total_processes > 0 else 0
        
        # Recent activity (last 30 days)
        thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
        recent_whiteboards = len([w for w in user_whiteboards if w.created_at >= thirty_days_ago])
        recent_exports = len([e for e in user_exports if e.created_at >= thirty_days_ago])
        
        return {
            'user_id': user_id,
            'basic_stats': stats.to_dict(),
            'success_rates': {
                'upload_success_rate': round(upload_success_rate, 2),
                'process_success_rate': round(process_success_rate, 2)
            },
            'recent_activity': {
                'whiteboards_last_30_days': recent_whiteboards,
                'exports_last_30_days': recent_exports
            },
            'storage_usage': {
                'total_size_mb': round((stats.total_upload_size or 0) / 1024 / 1024, 2),
                'average_file_size_mb': round(((stats.total_upload_size or 0) / (stats.successful_uploads or 1)) / 1024 / 1024, 2)
            }
        }
    
    @staticmethod
    def get_admin_dashboard_stats() -> dict:
        """Get system-wide statistics for admin dashboard"""
        # User statistics
        total_users = User.query.count()
        today = date.today()
        yesterday = today - timedelta(days=1)
        
        new_users_today = User.query.filter(
            func.date(User.created_at) == today
        ).count()
        
        active_users_today = User.query.filter(
            func.date(User.last_login) == today
        ).count()
        
        # Whiteboard statistics
        total_whiteboards = Whiteboard.query.count()
        whiteboards_today = Whiteboard.query.filter(
            func.date(Whiteboard.created_at) == today
        ).count()
        
        successful_processes_today = Whiteboard.query.filter(
            and_(
                func.date(Whiteboard.created_at) == today,
                Whiteboard.status == ProcessingStatus.COMPLETED
            )
        ).count()
        
        failed_processes_today = Whiteboard.query.filter(
            and_(
                func.date(Whiteboard.created_at) == today,
                Whiteboard.status == ProcessingStatus.FAILED
            )
        ).count()
        
        # Export statistics
        total_exports = Export.query.count()
        exports_today = Export.query.filter(
            func.date(Export.created_at) == today
        ).count()
        
        # Performance metrics
        avg_processing_time = db.session.query(
            func.avg(Whiteboard.processing_duration)
        ).filter(
            Whiteboard.status == ProcessingStatus.COMPLETED
        ).scalar() or 0
        
        # Popular formats
        format_counts = db.session.query(
            Export.format, func.count(Export.id)
        ).group_by(Export.format).all()
        
        most_popular_format = max(format_counts, key=lambda x: x[1])[0].value if format_counts else None
        
        # Storage usage
        total_storage = db.session.query(
            func.sum(Whiteboard.file_size)
        ).scalar() or 0
        
        return {
            'users': {
                'total': total_users,
                'new_today': new_users_today,
                'active_today': active_users_today
            },
            'whiteboards': {
                'total': total_whiteboards,
                'processed_today': whiteboards_today,
                'successful_today': successful_processes_today,
                'failed_today': failed_processes_today
            },
            'exports': {
                'total': total_exports,
                'created_today': exports_today,
                'popular_format': most_popular_format
            },
            'performance': {
                'average_processing_time': round(avg_processing_time or 0, 2),
                'total_storage_gb': round(total_storage / 1024 / 1024 / 1024, 2)
            },
            'format_distribution': {
                format.value: count for format, count in format_counts
            }
        }
    
    @staticmethod
    def get_usage_trends(user_id: int, days: int = 30) -> dict:
        """Get user usage trends over specified days"""
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)
        
        # Daily whiteboard uploads
        daily_uploads = db.session.query(
            func.date(Whiteboard.created_at).label('date'),
            func.count(Whiteboard.id).label('count')
        ).filter(
            and_(
                Whiteboard.user_id == user_id,
                Whiteboard.created_at >= start_date
            )
        ).group_by(func.date(Whiteboard.created_at)).all()
        
        # Daily exports
        daily_exports = db.session.query(
            func.date(Export.created_at).label('date'),
            func.count(Export.id).label('count')
        ).filter(
            and_(
                Export.user_id == user_id,
                Export.created_at >= start_date
            )
        ).group_by(func.date(Export.created_at)).all()
        
        # Hourly activity pattern
        hourly_activity = db.session.query(
            extract('hour', Whiteboard.created_at).label('hour'),
            func.count(Whiteboard.id).label('count')
        ).filter(
            and_(
                Whiteboard.user_id == user_id,
                Whiteboard.created_at >= start_date
            )
        ).group_by(extract('hour', Whiteboard.created_at)).all()
        
        return {
            'daily_uploads': [
                {'date': str(date), 'count': count} 
                for date, count in daily_uploads
            ],
            'daily_exports': [
                {'date': str(date), 'count': count} 
                for date, count in daily_exports
            ],
            'hourly_activity': [
                {'hour': int(hour), 'count': count} 
                for hour, count in hourly_activity
            ]
        }
    
    @staticmethod
    def _check_monthly_reset(stats: UserStatistics):
        """Check if monthly statistics need to be reset"""
        today = date.today()
        if not stats.monthly_reset_date or stats.monthly_reset_date.month != today.month:
            stats.monthly_uploads = 0
            stats.monthly_exports = 0
            stats.monthly_processing_time = 0.0
            stats.monthly_reset_date = today
    
    @staticmethod
    def update_system_stats():
        """Update daily system statistics (to be run by cron job)"""
        today = date.today()
        
        # Check if stats for today already exist
        system_stats = SystemStatistics.query.filter_by(date=today).first()
        if not system_stats:
            system_stats = SystemStatistics(date=today)
            db.session.add(system_stats)
        
        # Update all metrics
        admin_stats = StatisticsService.get_admin_dashboard_stats()
        
        system_stats.total_users = admin_stats['users']['total']
        system_stats.new_users = admin_stats['users']['new_today']
        system_stats.active_users = admin_stats['users']['active_today']
        
        system_stats.total_whiteboards = admin_stats['whiteboards']['total']
        system_stats.new_whiteboards = admin_stats['whiteboards']['processed_today']
        system_stats.successful_processes = admin_stats['whiteboards']['successful_today']
        system_stats.failed_processes = admin_stats['whiteboards']['failed_today']
        
        system_stats.total_exports = admin_stats['exports']['total']
        system_stats.new_exports = admin_stats['exports']['created_today']
        system_stats.most_popular_format = admin_stats['exports']['popular_format']
        
        system_stats.average_processing_time = admin_stats['performance']['average_processing_time']
        system_stats.total_storage_used = int(admin_stats['performance']['total_storage_gb'] * 1024 * 1024 * 1024)
        
        db.session.commit()
        return system_stats.to_dict()