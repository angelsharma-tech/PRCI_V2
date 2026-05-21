"""
Intervention Repository for PRCI v2
Phase 4.2 - Persistent Storage & User System Integration
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func

from .base import BaseRepository
from models.intervention import Intervention, UserIntervention, InterventionType, InterventionCategory, InterventionStatus, UserInterventionStatus
from utils.logging_utils import get_logger

logger = get_logger(__name__)


class InterventionRepository(BaseRepository[Intervention]):
    """
    Repository for Intervention model operations
    """
    
    def get_model_class(self):
        return Intervention
    
    # Intervention-specific operations
    
    def get_active_interventions(self) -> List[Intervention]:
        """Get all active interventions"""
        try:
            return self.session.query(Intervention).filter(
                and_(
                    Intervention.status == InterventionStatus.ACTIVE,
                    Intervention.is_deleted == 'N'
                )
            ).order_by(Intervention.priority.asc()).all()
        except Exception as e:
            logger.error(f"Error getting active interventions: {e}")
            raise
    
    def get_interventions_by_type(self, intervention_type: InterventionType) -> List[Intervention]:
        """Get interventions by type"""
        try:
            return self.session.query(Intervention).filter(
                and_(
                    Intervention.intervention_type == intervention_type,
                    Intervention.status == InterventionStatus.ACTIVE,
                    Intervention.is_deleted == 'N'
                )
            ).order_by(Intervention.priority.asc()).all()
        except Exception as e:
            logger.error(f"Error getting interventions by type {intervention_type}: {e}")
            raise
    
    def get_interventions_by_category(self, category: InterventionCategory) -> List[Intervention]:
        """Get interventions by category"""
        try:
            return self.session.query(Intervention).filter(
                and_(
                    Intervention.category == category,
                    Intervention.status == InterventionStatus.ACTIVE,
                    Intervention.is_deleted == 'N'
                )
            ).order_by(Intervention.priority.asc()).all()
        except Exception as e:
            logger.error(f"Error getting interventions by category {category}: {e}")
            raise
    
    def get_suitable_interventions(self, root_cause: str = None, risk_level: str = None,
                                 score_value: float = None) -> List[Intervention]:
        """Get interventions suitable for given conditions"""
        try:
            interventions = self.get_active_interventions()
            
            suitable_interventions = []
            for intervention in interventions:
                if intervention.is_suitable_for(root_cause, risk_level, score_value):
                    suitable_interventions.append(intervention)
            
            # Sort by priority and effectiveness
            suitable_interventions.sort(key=lambda x: (x.priority, -(x.effectiveness_score or 0)))
            
            return suitable_interventions
        except Exception as e:
            logger.error(f"Error getting suitable interventions: {e}")
            raise
    
    def search_interventions(self, search_term: str) -> List[Intervention]:
        """Search interventions by title or description"""
        search_fields = ['title', 'description', 'instructions']
        return self.search(search_term, search_fields)
    
    def update_effectiveness_data(self, intervention_id: int, avg_rating: float, 
                              completion_rate: float) -> bool:
        """Update intervention effectiveness data"""
        try:
            intervention = self.get_by_id(intervention_id)
            if intervention:
                intervention.effectiveness_score = avg_rating
                intervention.completion_rate = completion_rate
                self.session.commit()
                logger.info(f"Updated effectiveness for intervention {intervention_id}")
                return True
            return False
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error updating effectiveness for intervention {intervention_id}: {e}")
            raise
    
    def get_intervention_statistics(self) -> Dict[str, Any]:
        """Get intervention statistics"""
        try:
            # Intervention counts by type
            type_counts = self.session.query(
                Intervention.intervention_type,
                func.count(Intervention.id).label('count')
            ).filter(
                and_(
                    Intervention.status == InterventionStatus.ACTIVE,
                    Intervention.is_deleted == 'N'
                )
            ).group_by(Intervention.intervention_type).all()
            
            # Intervention counts by category
            category_counts = self.session.query(
                Intervention.category,
                func.count(Intervention.id).label('count')
            ).filter(
                and_(
                    Intervention.status == InterventionStatus.ACTIVE,
                    Intervention.is_deleted == 'N'
                )
            ).group_by(Intervention.category).all()
            
            # Average effectiveness scores
            avg_effectiveness = self.session.query(
                func.avg(Intervention.effectiveness_score)
            ).filter(
                and_(
                    Intervention.effectiveness_score.isnot(None),
                    Intervention.status == InterventionStatus.ACTIVE,
                    Intervention.is_deleted == 'N'
                )
            ).scalar() or 0
            
            # Evidence-based interventions
            evidence_based_count = self.session.query(Intervention).filter(
                and_(
                    Intervention.evidence_based == True,
                    Intervention.status == InterventionStatus.ACTIVE,
                    Intervention.is_deleted == 'N'
                )
            ).count()
            
            total_active = self.session.query(Intervention).filter(
                and_(
                    Intervention.status == InterventionStatus.ACTIVE,
                    Intervention.is_deleted == 'N'
                )
            ).count()
            
            return {
                'total_active': total_active,
                'type_distribution': dict(type_counts),
                'category_distribution': dict(category_counts),
                'avg_effectiveness_score': avg_effectiveness,
                'evidence_based_count': evidence_based_count,
                'evidence_based_percentage': (evidence_based_count / total_active * 100) if total_active > 0 else 0
            }
        except Exception as e:
            logger.error(f"Error getting intervention statistics: {e}")
            raise


class UserInterventionRepository(BaseRepository[UserIntervention]):
    """
    Repository for UserIntervention model operations
    """
    
    def get_model_class(self):
        return UserIntervention
    
    # User intervention-specific operations
    
    def recommend_intervention(self, user_id: int, intervention_id: int, 
                            assessment_id: int = None, personalized_notes: str = None) -> UserIntervention:
        """Recommend an intervention to a user"""
        intervention_data = {
            'user_id': user_id,
            'intervention_id': intervention_id,
            'assessment_id': assessment_id,
            'status': UserInterventionStatus.RECOMMENDED,
            'personalized_notes': personalized_notes
        }
        
        return self.create(intervention_data)
    
    def get_user_interventions(self, user_id: int, 
                             status: UserInterventionStatus = None) -> List[UserIntervention]:
        """Get interventions for a user"""
        try:
            query = self.session.query(UserIntervention).filter(
                and_(
                    UserIntervention.user_id == user_id,
                    UserIntervention.is_deleted == 'N'
                )
            )
            
            if status:
                query = query.filter(UserIntervention.status == status)
            
            return query.order_by(desc(UserIntervention.recommended_at)).all()
        except Exception as e:
            logger.error(f"Error getting user interventions for user {user_id}: {e}")
            raise
    
    def get_active_user_interventions(self, user_id: int) -> List[UserIntervention]:
        """Get active interventions for a user"""
        active_statuses = [
            UserInterventionStatus.RECOMMENDED,
            UserInterventionStatus.ACCEPTED,
            UserInterventionStatus.IN_PROGRESS
        ]
        
        try:
            return self.session.query(UserIntervention).filter(
                and_(
                    UserIntervention.user_id == user_id,
                    UserIntervention.status.in_(active_statuses),
                    UserIntervention.is_deleted == 'N'
                )
            ).order_by(desc(UserIntervention.recommended_at)).all()
        except Exception as e:
            logger.error(f"Error getting active user interventions: {e}")
            raise
    
    def accept_intervention(self, user_intervention_id: int) -> bool:
        """Accept a recommended intervention"""
        try:
            user_intervention = self.get_by_id(user_intervention_id)
            if user_intervention and user_intervention.is_recommended:
                user_intervention.accept()
                self.session.commit()
                logger.info(f"Accepted user intervention {user_intervention_id}")
                return True
            return False
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error accepting user intervention {user_intervention_id}: {e}")
            raise
    
    def start_intervention(self, user_intervention_id: int) -> bool:
        """Start an intervention"""
        try:
            user_intervention = self.get_by_id(user_intervention_id)
            if user_intervention and user_intervention.is_accepted:
                user_intervention.start()
                self.session.commit()
                logger.info(f"Started user intervention {user_intervention_id}")
                return True
            return False
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error starting user intervention {user_intervention_id}: {e}")
            raise
    
    def complete_intervention(self, user_intervention_id: int, rating: int = None,
                          feedback: str = None, effectiveness: int = None) -> bool:
        """Complete an intervention"""
        try:
            user_intervention = self.get_by_id(user_intervention_id)
            if user_intervention:
                user_intervention.complete(rating, feedback, effectiveness)
                self.session.commit()
                logger.info(f"Completed user intervention {user_intervention_id}")
                return True
            return False
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error completing user intervention {user_intervention_id}: {e}")
            raise
    
    def update_progress(self, user_intervention_id: int, progress_percentage: float) -> bool:
        """Update intervention progress"""
        try:
            user_intervention = self.get_by_id(user_intervention_id)
            if user_intervention:
                user_intervention.update_progress(progress_percentage)
                self.session.commit()
                logger.info(f"Updated progress for user intervention {user_intervention_id}: {progress_percentage}")
                return True
            return False
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error updating progress for user intervention {user_intervention_id}: {e}")
            raise
    
    def reject_intervention(self, user_intervention_id: int) -> bool:
        """Reject an intervention"""
        try:
            user_intervention = self.get_by_id(user_intervention_id)
            if user_intervention:
                user_intervention.reject()
                self.session.commit()
                logger.info(f"Rejected user intervention {user_intervention_id}")
                return True
            return False
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error rejecting user intervention {user_intervention_id}: {e}")
            raise
    
    def get_user_intervention_statistics(self, user_id: int, days: int = 30) -> Dict[str, Any]:
        """Get intervention statistics for a user"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            query = self.session.query(UserIntervention).filter(
                and_(
                    UserIntervention.user_id == user_id,
                    UserIntervention.recommended_at >= cutoff_date,
                    UserIntervention.is_deleted == 'N'
                )
            )
            
            total_interventions = query.count()
            
            # Status distribution
            status_counts = self.session.query(
                UserIntervention.status,
                func.count(UserIntervention.id).label('count')
            ).filter(
                and_(
                    UserIntervention.user_id == user_id,
                    UserIntervention.recommended_at >= cutoff_date,
                    UserIntervention.is_deleted == 'N'
                )
            ).group_by(UserIntervention.status).all()
            
            # Completion statistics
            completed_interventions = query.filter(
                UserIntervention.status == UserInterventionStatus.COMPLETED
            )
            
            completion_count = completed_interventions.count()
            avg_duration = completed_interventions.with_entities(
                func.avg(func.datediff(UserIntervention.completed_at, UserIntervention.started_at))
            ).scalar() or 0
            
            avg_rating = completed_interventions.with_entities(
                func.avg(UserIntervention.user_rating)
            ).scalar() or 0
            
            avg_effectiveness = completed_interventions.with_entities(
                func.avg(UserIntervention.effectiveness_rating)
            ).scalar() or 0
            
            return {
                'total_interventions': total_interventions,
                'status_distribution': dict(status_counts),
                'completion_count': completion_count,
                'completion_rate': (completion_count / total_interventions * 100) if total_interventions > 0 else 0,
                'avg_duration_days': avg_duration,
                'avg_user_rating': avg_rating,
                'avg_effectiveness_rating': avg_effectiveness,
                'period_days': days
            }
        except Exception as e:
            logger.error(f"Error getting user intervention statistics: {e}")
            raise
    
    def get_intervention_completion_trends(self, days: int = 90) -> List[Dict[str, Any]]:
        """Get intervention completion trends over time"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # Group by date
            trends = self.session.query(
                func.date(UserIntervention.completed_at).label('date'),
                func.count(UserIntervention.id).label('completed_count'),
                func.avg(UserIntervention.user_rating).label('avg_rating')
            ).filter(
                and_(
                    UserIntervention.status == UserInterventionStatus.COMPLETED,
                    UserIntervention.completed_at >= cutoff_date,
                    UserIntervention.is_deleted == 'N'
                )
            ).group_by(func.date(UserIntervention.completed_at)).all()
            
            return [
                {
                    'date': str(trend.date),
                    'completed_count': trend.completed_count,
                    'avg_rating': float(trend.avg_rating) if trend.avg_rating else 0
                }
                for trend in trends
            ]
        except Exception as e:
            logger.error(f"Error getting intervention completion trends: {e}")
            raise
    
    def get_overdue_interventions(self, user_id: int, days: int = 7) -> List[UserIntervention]:
        """Get interventions that should be completed but aren't"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            return self.session.query(UserIntervention).filter(
                and_(
                    UserIntervention.user_id == user_id,
                    UserIntervention.status.in_([UserInterventionStatus.ACCEPTED, UserInterventionStatus.IN_PROGRESS]),
                    UserIntervention.started_at <= cutoff_date,
                    UserIntervention.is_deleted == 'N'
                )
            ).all()
        except Exception as e:
            logger.error(f"Error getting overdue interventions: {e}")
            raise
