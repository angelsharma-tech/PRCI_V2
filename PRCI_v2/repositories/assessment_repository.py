"""
Assessment Repository for PRCI v2
Phase 4.2 - Persistent Storage & User System Integration
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func

from .base import BaseRepository
from models.assessment import Assessment, Score, AssessmentType, AssessmentStatus, ScoreType
from utils.logging_utils import get_logger

logger = get_logger(__name__)


class AssessmentRepository(BaseRepository[Assessment]):
    """
    Repository for Assessment model operations
    """
    
    def get_model_class(self):
        return Assessment
    
    # Assessment-specific operations
    
    def create_assessment(self, user_id: int, assessment_type: AssessmentType, 
                        input_text: str = None, title: str = None, **kwargs) -> Assessment:
        """Create a new assessment"""
        assessment_data = {
            'user_id': user_id,
            'assessment_type': assessment_type,
            'input_text': input_text,
            'title': title or f"Assessment - {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}",
            'status': AssessmentStatus.PENDING,
            **kwargs
        }
        
        return self.create(assessment_data)
    
    def get_user_assessments(self, user_id: int, include_deleted: bool = False) -> List[Assessment]:
        """Get all assessments for a user"""
        try:
            query = self.session.query(Assessment).filter(Assessment.user_id == user_id)
            
            if not include_deleted:
                query = query.filter(Assessment.is_deleted == 'N')
            
            return query.order_by(desc(Assessment.created_at)).all()
        except Exception as e:
            logger.error(f"Error getting assessments for user {user_id}: {e}")
            raise
    
    def get_completed_assessments(self, user_id: int = None) -> List[Assessment]:
        """Get completed assessments"""
        try:
            query = self.session.query(Assessment).filter(
                Assessment.status == AssessmentStatus.COMPLETED
            )
            
            if user_id:
                query = query.filter(Assessment.user_id == user_id)
            
            query = query.filter(Assessment.is_deleted == 'N')
            
            return query.order_by(desc(Assessment.completed_at)).all()
        except Exception as e:
            logger.error(f"Error getting completed assessments: {e}")
            raise
    
    def get_pending_assessments(self, user_id: int = None) -> List[Assessment]:
        """Get pending assessments"""
        try:
            query = self.session.query(Assessment).filter(
                Assessment.status == AssessmentStatus.PENDING
            )
            
            if user_id:
                query = query.filter(Assessment.user_id == user_id)
            
            query = query.filter(Assessment.is_deleted == 'N')
            
            return query.order_by(Assessment.created_at).all()
        except Exception as e:
            logger.error(f"Error getting pending assessments: {e}")
            raise
    
    def get_assessment_by_type(self, user_id: int, assessment_type: AssessmentType) -> List[Assessment]:
        """Get assessments by type for a user"""
        try:
            return self.session.query(Assessment).filter(
                and_(
                    Assessment.user_id == user_id,
                    Assessment.assessment_type == assessment_type,
                    Assessment.is_deleted == 'N'
                )
            ).order_by(desc(Assessment.created_at)).all()
        except Exception as e:
            logger.error(f"Error getting assessments by type {assessment_type}: {e}")
            raise
    
    def get_recent_assessments(self, user_id: int, days: int = 30) -> List[Assessment]:
        """Get recent assessments for a user"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            return self.session.query(Assessment).filter(
                and_(
                    Assessment.user_id == user_id,
                    Assessment.created_at >= cutoff_date,
                    Assessment.is_deleted == 'N'
                )
            ).order_by(desc(Assessment.created_at)).all()
        except Exception as e:
            logger.error(f"Error getting recent assessments: {e}")
            raise
    
    def complete_assessment(self, assessment_id: int, risk_level: str = None, 
                         primary_root_cause: str = None, root_cause_data: Dict = None,
                         model_version: str = None, model_confidence: float = None,
                         processing_time_ms: int = None) -> bool:
        """Complete an assessment with results"""
        try:
            assessment = self.get_by_id(assessment_id)
            if assessment:
                assessment.complete(risk_level, primary_root_cause)
                
                if root_cause_data:
                    assessment.root_cause_data = root_cause_data
                if model_version:
                    assessment.model_version = model_version
                if model_confidence is not None:
                    assessment.model_confidence = model_confidence
                if processing_time_ms:
                    assessment.processing_time_ms = processing_time_ms
                
                self.session.commit()
                logger.info(f"Completed assessment {assessment_id}")
                return True
            return False
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error completing assessment {assessment_id}: {e}")
            raise
    
    def fail_assessment(self, assessment_id: int, error_message: str = None) -> bool:
        """Mark assessment as failed"""
        try:
            assessment = self.get_by_id(assessment_id)
            if assessment:
                assessment.fail(error_message)
                self.session.commit()
                logger.info(f"Failed assessment {assessment_id}: {error_message}")
                return True
            return False
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error failing assessment {assessment_id}: {e}")
            raise
    
    def get_assessment_statistics(self, user_id: int = None, days: int = 30) -> Dict[str, Any]:
        """Get assessment statistics"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            query = self.session.query(Assessment).filter(
                and_(
                    Assessment.created_at >= cutoff_date,
                    Assessment.is_deleted == 'N'
                )
            )
            
            if user_id:
                query = query.filter(Assessment.user_id == user_id)
            
            total_assessments = query.count()
            completed_assessments = query.filter(
                Assessment.status == AssessmentStatus.COMPLETED
            ).count()
            failed_assessments = query.filter(
                Assessment.status == AssessmentStatus.FAILED
            ).count()
            
            # Average processing time
            avg_processing_time = self.session.query(
                func.avg(Assessment.processing_time_ms)
            ).filter(
                and_(
                    Assessment.processing_time_ms.isnot(None),
                    Assessment.created_at >= cutoff_date,
                    Assessment.is_deleted == 'N'
                )
            ).scalar() or 0
            
            # Risk level distribution
            risk_distribution = self.session.query(
                Assessment.risk_level,
                func.count(Assessment.id).label('count')
            ).filter(
                and_(
                    Assessment.risk_level.isnot(None),
                    Assessment.created_at >= cutoff_date,
                    Assessment.is_deleted == 'N'
                )
            ).group_by(Assessment.risk_level).all()
            
            return {
                'total_assessments': total_assessments,
                'completed_assessments': completed_assessments,
                'failed_assessments': failed_assessments,
                'completion_rate': (completed_assessments / total_assessments * 100) if total_assessments > 0 else 0,
                'failure_rate': (failed_assessments / total_assessments * 100) if total_assessments > 0 else 0,
                'avg_processing_time_ms': avg_processing_time,
                'risk_distribution': dict(risk_distribution),
                'period_days': days
            }
        except Exception as e:
            logger.error(f"Error getting assessment statistics: {e}")
            raise
    
    def get_assessments_by_risk_level(self, risk_level: str, user_id: int = None) -> List[Assessment]:
        """Get assessments by risk level"""
        try:
            query = self.session.query(Assessment).filter(
                and_(
                    Assessment.risk_level == risk_level,
                    Assessment.is_deleted == 'N'
                )
            )
            
            if user_id:
                query = query.filter(Assessment.user_id == user_id)
            
            return query.order_by(desc(Assessment.completed_at)).all()
        except Exception as e:
            logger.error(f"Error getting assessments by risk level {risk_level}: {e}")
            raise
    
    def search_assessments(self, user_id: int, search_term: str) -> List[Assessment]:
        """Search assessments by title or description"""
        search_fields = ['title', 'description', 'input_text']
        assessments = self.search(search_term, search_fields)
        
        # Filter by user if specified
        if user_id:
            assessments = [a for a in assessments if a.user_id == user_id]
        
        return assessments


class ScoreRepository(BaseRepository[Score]):
    """
    Repository for Score model operations
    """
    
    def get_model_class(self):
        return Score
    
    # Score-specific operations
    
    def create_score(self, assessment_id: int, score_type: ScoreType, 
                   value: float, confidence: float = None, **kwargs) -> Score:
        """Create a new score"""
        score_data = {
            'assessment_id': assessment_id,
            'score_type': score_type,
            'value': value,
            'confidence': confidence,
            **kwargs
        }
        
        return self.create(score_data)
    
    def get_assessment_scores(self, assessment_id: int) -> List[Score]:
        """Get all scores for an assessment"""
        try:
            return self.session.query(Score).filter(
                and_(
                    Score.assessment_id == assessment_id,
                    Score.is_deleted == 'N'
                )
            ).all()
        except Exception as e:
            logger.error(f"Error getting scores for assessment {assessment_id}: {e}")
            raise
    
    def get_scores_by_type(self, user_id: int, score_type: ScoreType, 
                         days: int = 30) -> List[Score]:
        """Get scores by type for a user"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            return self.session.query(Score).join(Assessment).filter(
                and_(
                    Assessment.user_id == user_id,
                    Score.score_type == score_type,
                    Assessment.created_at >= cutoff_date,
                    Assessment.is_deleted == 'N',
                    Score.is_deleted == 'N'
                )
            ).order_by(desc(Score.created_at)).all()
        except Exception as e:
            logger.error(f"Error getting scores by type {score_type}: {e}")
            raise
    
    def get_latest_scores(self, user_id: int, score_types: List[ScoreType] = None) -> Dict[ScoreType, Score]:
        """Get latest scores for each type"""
        try:
            if score_types is None:
                score_types = [ScoreType.DEPRESSION, ScoreType.ANXIETY, ScoreType.OVERALL]
            
            latest_scores = {}
            for score_type in score_types:
                latest_score = self.session.query(Score).join(Assessment).filter(
                    and_(
                        Assessment.user_id == user_id,
                        Score.score_type == score_type,
                        Assessment.is_deleted == 'N',
                        Score.is_deleted == 'N'
                    )
                ).order_by(desc(Score.created_at)).first()
                
                if latest_score:
                    latest_scores[score_type] = latest_score
            
            return latest_scores
        except Exception as e:
            logger.error(f"Error getting latest scores for user {user_id}: {e}")
            raise
    
    def get_score_trends(self, user_id: int, score_type: ScoreType, 
                       days: int = 30) -> List[Dict[str, Any]]:
        """Get score trends over time"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            scores = self.session.query(Score).join(Assessment).filter(
                and_(
                    Assessment.user_id == user_id,
                    Score.score_type == score_type,
                    Assessment.created_at >= cutoff_date,
                    Assessment.is_deleted == 'N',
                    Score.is_deleted == 'N'
                )
            ).order_by(Score.created_at).all()
            
            return [
                {
                    'date': score.created_at.isoformat(),
                    'value': score.value,
                    'confidence': score.confidence,
                    'risk_category': score.risk_category
                }
                for score in scores
            ]
        except Exception as e:
            logger.error(f"Error getting score trends: {e}")
            raise
    
    def get_score_statistics(self, user_id: int, days: int = 30) -> Dict[str, Any]:
        """Get score statistics for a user"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # Average scores by type
            avg_scores = self.session.query(
                Score.score_type,
                func.avg(Score.value).label('avg_value'),
                func.count(Score.id).label('count')
            ).join(Assessment).filter(
                and_(
                    Assessment.user_id == user_id,
                    Assessment.created_at >= cutoff_date,
                    Assessment.is_deleted == 'N',
                    Score.is_deleted == 'N'
                )
            ).group_by(Score.score_type).all()
            
            # Risk category distribution
            risk_distribution = {}
            for score_type in ScoreType:
                risk_counts = self.session.query(
                    Score.value,
                    func.count(Score.id).label('count')
                ).join(Assessment).filter(
                    and_(
                        Assessment.user_id == user_id,
                        Score.score_type == score_type,
                        Assessment.created_at >= cutoff_date,
                        Assessment.is_deleted == 'N',
                        Score.is_deleted == 'N'
                    )
                ).all()
                
                low_risk = sum(1 for value, count in risk_counts if value < 0.33)
                moderate_risk = sum(1 for value, count in risk_counts if 0.33 <= value < 0.66)
                high_risk = sum(1 for value, count in risk_counts if value >= 0.66)
                
                risk_distribution[score_type.value] = {
                    'low': low_risk,
                    'moderate': moderate_risk,
                    'high': high_risk
                }
            
            return {
                'average_scores': dict(avg_scores),
                'risk_distribution': risk_distribution,
                'period_days': days
            }
        except Exception as e:
            logger.error(f"Error getting score statistics: {e}")
            raise
