"""
Report Repository for PRCI v2
Phase 4.2 - Persistent Storage & User System Integration
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func

from .base import BaseRepository
from models.report import Report, ReportType, ReportFormat, ReportStatus
from utils.logging_utils import get_logger

logger = get_logger(__name__)


class ReportRepository(BaseRepository[Report]):
    """
    Repository for Report model operations
    """
    
    def get_model_class(self):
        return Report
    
    # Report-specific operations
    
    def create_report(self, user_id: int, title: str, report_type: ReportType,
                    format: ReportFormat, parameters: Dict[str, Any] = None,
                    description: str = None) -> Report:
        """Create a new report"""
        report_data = {
            'user_id': user_id,
            'title': title,
            'report_type': report_type,
            'format': format,
            'status': ReportStatus.PENDING,
            'parameters': parameters,
            'description': description
        }
        
        return self.create(report_data)
    
    def get_user_reports(self, user_id: int, report_type: ReportType = None,
                       format: ReportFormat = None) -> List[Report]:
        """Get reports for a user"""
        try:
            query = self.session.query(Report).filter(
                and_(
                    Report.user_id == user_id,
                    Report.is_deleted == 'N'
                )
            )
            
            if report_type:
                query = query.filter(Report.report_type == report_type)
            
            if format:
                query = query.filter(Report.format == format)
            
            return query.order_by(desc(Report.created_at)).all()
        except Exception as e:
            logger.error(f"Error getting reports for user {user_id}: {e}")
            raise
    
    def get_reports_by_status(self, status: ReportStatus, user_id: int = None) -> List[Report]:
        """Get reports by status"""
        try:
            query = self.session.query(Report).filter(
                and_(
                    Report.status == status,
                    Report.is_deleted == 'N'
                )
            )
            
            if user_id:
                query = query.filter(Report.user_id == user_id)
            
            return query.order_by(desc(Report.created_at)).all()
        except Exception as e:
            logger.error(f"Error getting reports by status {status}: {e}")
            raise
    
    def get_completed_reports(self, user_id: int = None, days: int = 30) -> List[Report]:
        """Get completed reports"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            query = self.session.query(Report).filter(
                and_(
                    Report.status == ReportStatus.COMPLETED,
                    Report.created_at >= cutoff_date,
                    Report.is_deleted == 'N'
                )
            )
            
            if user_id:
                query = query.filter(Report.user_id == user_id)
            
            return query.order_by(desc(Report.completed_at)).all()
        except Exception as e:
            logger.error(f"Error getting completed reports: {e}")
            raise
    
    def start_generation(self, report_id: int) -> bool:
        """Mark report as currently generating"""
        try:
            report = self.get_by_id(report_id)
            if report:
                report.start_generation()
                self.session.commit()
                logger.info(f"Started generation for report {report_id}")
                return True
            return False
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error starting generation for report {report_id}: {e}")
            raise
    
    def complete_generation(self, report_id: int, file_data: bytes = None,
                         file_path: str = None, generation_time_ms: int = None) -> bool:
        """Mark report generation as completed"""
        try:
            report = self.get_by_id(report_id)
            if report:
                report.complete_generation(file_data, file_path, generation_time_ms)
                self.session.commit()
                logger.info(f"Completed generation for report {report_id}")
                return True
            return False
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error completing generation for report {report_id}: {e}")
            raise
    
    def fail_generation(self, report_id: int, error_message: str = None) -> bool:
        """Mark report generation as failed"""
        try:
            report = self.get_by_id(report_id)
            if report:
                report.fail_generation(error_message)
                self.session.commit()
                logger.info(f"Failed generation for report {report_id}: {error_message}")
                return True
            return False
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error failing generation for report {report_id}: {e}")
            raise
    
    def mark_email_sent(self, report_id: int) -> bool:
        """Mark report as sent via email"""
        try:
            report = self.get_by_id(report_id)
            if report:
                report.mark_email_sent()
                self.session.commit()
                logger.info(f"Marked email sent for report {report_id}")
                return True
            return False
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error marking email sent for report {report_id}: {e}")
            raise
    
    def increment_download_count(self, report_id: int) -> bool:
        """Increment download count for a report"""
        try:
            report = self.get_by_id(report_id)
            if report:
                report.increment_download_count()
                self.session.commit()
                logger.info(f"Incremented download count for report {report_id}")
                return True
            return False
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error incrementing download count for report {report_id}: {e}")
            raise
    
    def generate_access_token(self, report_id: int) -> Optional[str]:
        """Generate access token for public report access"""
        try:
            report = self.get_by_id(report_id)
            if report:
                token = report.generate_access_token()
                self.session.commit()
                return token
            return None
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error generating access token for report {report_id}: {e}")
            raise
    
    def set_expiration(self, report_id: int, days: int = 30) -> bool:
        """Set report expiration"""
        try:
            report = self.get_by_id(report_id)
            if report:
                report.set_expiration(days)
                self.session.commit()
                logger.info(f"Set expiration for report {report_id}: {days} days")
                return True
            return False
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error setting expiration for report {report_id}: {e}")
            raise
    
    def get_report_by_token(self, token: str) -> Optional[Report]:
        """Get report by access token"""
        try:
            return self.session.query(Report).filter(
                and_(
                    Report.access_token == token,
                    Report.is_deleted == 'N'
                )
            ).first()
        except Exception as e:
            logger.error(f"Error getting report by token {token}: {e}")
            raise
    
    def get_accessible_report(self, token: str) -> Optional[Report]:
        """Get report that is accessible by token"""
        report = self.get_report_by_token(token)
        if report and report.is_accessible_by_token(token):
            return report
        return None
    
    def get_public_reports(self) -> List[Report]:
        """Get all public reports"""
        try:
            return self.session.query(Report).filter(
                and_(
                    Report.is_public == True,
                    Report.status == ReportStatus.COMPLETED,
                    Report.is_deleted == 'N'
                )
            ).order_by(desc(Report.created_at)).all()
        except Exception as e:
            logger.error(f"Error getting public reports: {e}")
            raise
    
    def search_reports(self, user_id: int, search_term: str) -> List[Report]:
        """Search reports by title or description"""
        search_fields = ['title', 'description']
        reports = self.search(search_term, search_fields)
        
        # Filter by user if specified
        if user_id:
            reports = [r for r in reports if r.user_id == user_id]
        
        return reports
    
    def get_report_statistics(self, user_id: int = None, days: int = 30) -> Dict[str, Any]:
        """Get report statistics"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            query = self.session.query(Report).filter(
                and_(
                    Report.created_at >= cutoff_date,
                    Report.is_deleted == 'N'
                )
            )
            
            if user_id:
                query = query.filter(Report.user_id == user_id)
            
            total_reports = query.count()
            
            # Status distribution
            status_counts = query.with_entities(
                Report.status,
                func.count(Report.id).label('count')
            ).group_by(Report.status).all()
            
            # Type distribution
            type_counts = query.with_entities(
                Report.report_type,
                func.count(Report.id).label('count')
            ).group_by(Report.report_type).all()
            
            # Format distribution
            format_counts = query.with_entities(
                Report.format,
                func.count(Report.id).label('count')
            ).group_by(Report.format).all()
            
            # Generation statistics
            completed_reports = query.filter(Report.status == ReportStatus.COMPLETED)
            
            avg_generation_time = completed_reports.with_entities(
                func.avg(Report.generation_time_ms)
            ).scalar() or 0
            
            total_file_size = completed_reports.with_entities(
                func.sum(Report.file_size_bytes)
            ).scalar() or 0
            
            # Email statistics
            email_sent_count = completed_reports.filter(
                Report.email_sent == True
            ).count()
            
            # Download statistics
            total_downloads = completed_reports.with_entities(
                func.sum(Report.download_count)
            ).scalar() or 0
            
            return {
                'total_reports': total_reports,
                'status_distribution': dict(status_counts),
                'type_distribution': dict(type_counts),
                'format_distribution': dict(format_counts),
                'avg_generation_time_ms': avg_generation_time,
                'total_file_size_mb': total_file_size / (1024 * 1024),
                'email_sent_count': email_sent_count,
                'total_downloads': total_downloads,
                'period_days': days
            }
        except Exception as e:
            logger.error(f"Error getting report statistics: {e}")
            raise
    
    def get_reports_by_date_range(self, user_id: int, start_date: datetime, 
                               end_date: datetime) -> List[Report]:
        """Get reports within a date range"""
        try:
            return self.session.query(Report).filter(
                and_(
                    Report.user_id == user_id,
                    Report.created_at >= start_date,
                    Report.created_at <= end_date,
                    Report.is_deleted == 'N'
                )
            ).order_by(desc(Report.created_at)).all()
        except Exception as e:
            logger.error(f"Error getting reports by date range: {e}")
            raise
    
    def cleanup_expired_reports(self) -> int:
        """Clean up expired reports"""
        try:
            expired_count = self.session.query(Report).filter(
                and_(
                    Report.expires_at <= datetime.utcnow(),
                    Report.is_deleted == 'N'
                )
            ).update({'status': ReportStatus.EXPIRED})
            
            self.session.commit()
            logger.info(f"Marked {expired_count} reports as expired")
            return expired_count
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error cleaning up expired reports: {e}")
            raise
    
    def get_large_reports(self, size_mb: float = 10) -> List[Report]:
        """Get reports larger than specified size"""
        try:
            size_bytes = size_mb * 1024 * 1024
            return self.session.query(Report).filter(
                and_(
                    Report.file_size_bytes >= size_bytes,
                    Report.status == ReportStatus.COMPLETED,
                    Report.is_deleted == 'N'
                )
            ).order_by(desc(Report.file_size_bytes)).all()
        except Exception as e:
            logger.error(f"Error getting large reports: {e}")
            raise
    
    def get_recent_reports(self, user_id: int = None, days: int = 7, 
                         limit: int = 50) -> List[Report]:
        """Get recent reports"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            query = self.session.query(Report).filter(
                and_(
                    Report.created_at >= cutoff_date,
                    Report.is_deleted == 'N'
                )
            )
            
            if user_id:
                query = query.filter(Report.user_id == user_id)
            
            return query.order_by(desc(Report.created_at)).limit(limit).all()
        except Exception as e:
            logger.error(f"Error getting recent reports: {e}")
            raise
