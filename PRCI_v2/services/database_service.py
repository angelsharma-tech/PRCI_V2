"""
Database Service for PRCI v2
Phase 4.2 - Persistent Storage & User System Integration
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

from db.connection import get_session_manager, with_db_session, with_transaction
from repositories.user_repository import UserRepository
from repositories.session_repository import SessionRepository
from repositories.conversation_repository import ConversationRepository, MessageRepository
from repositories.assessment_repository import AssessmentRepository, ScoreRepository
from repositories.intervention_repository import InterventionRepository, UserInterventionRepository
from repositories.report_repository import ReportRepository

from models.user import User, UserStatus, UserRole
from models.session import UserSession
from models.conversation import Conversation, Message, ConversationStatus, MessageRole
from models.assessment import Assessment, Score, AssessmentType, AssessmentStatus, ScoreType
from models.intervention import Intervention, UserIntervention, InterventionType, InterventionCategory, UserInterventionStatus
from models.report import Report, ReportType, ReportFormat, ReportStatus

from utils.logging_utils import get_logger, PerformanceTimer

logger = get_logger(__name__)


class DatabaseService:
    """
    High-level database service providing unified access to all data operations
    """
    
    def __init__(self):
        self.session_manager = get_session_manager()
        
        # Initialize repositories
        self.user_repo = UserRepository()
        self.session_repo = SessionRepository()
        self.conversation_repo = ConversationRepository()
        self.message_repo = MessageRepository()
        self.assessment_repo = AssessmentRepository()
        self.score_repo = ScoreRepository()
        self.intervention_repo = InterventionRepository()
        self.user_intervention_repo = UserInterventionRepository()
        self.report_repo = ReportRepository()
    
    # User Management
    
    def create_user(self, email: str, **kwargs) -> Optional[User]:
        """Create a new user"""
        try:
            with self.session_manager.get_session() as session:
                self.user_repo.session = session
                return self.user_repo.create_user(email, **kwargs)
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            return None
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        try:
            with self.session_manager.get_session() as session:
                self.user_repo.session = session
                return self.user_repo.find_by_email(email)
        except Exception as e:
            logger.error(f"Error getting user by email: {e}")
            return None
    
    def update_user(self, user_id: int, **kwargs) -> bool:
        """Update user information"""
        try:
            with self.session_manager.transaction() as session:
                self.user_repo.session = session
                return self.user_repo.update_user(user_id, **kwargs) is not None
        except Exception as e:
            logger.error(f"Error updating user: {e}")
            return False
    
    # Session Management
    
    def create_session(self, user_id: int, **kwargs) -> Optional[UserSession]:
        """Create a new user session"""
        try:
            with self.session_manager.get_session() as session:
                self.session_repo.session = session
                return self.session_repo.create_session(user_id, **kwargs)
        except Exception as e:
            logger.error(f"Error creating session: {e}")
            return None
    
    def get_valid_session(self, session_id: str) -> Optional[UserSession]:
        """Get a valid session"""
        try:
            with self.session_manager.get_session() as session:
                self.session_repo.session = session
                return self.session_repo.get_valid_session(session_id)
        except Exception as e:
            logger.error(f"Error getting valid session: {e}")
            return None
    
    def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions"""
        try:
            with self.session_manager.get_session() as session:
                self.session_repo.session = session
                return self.session_repo.cleanup_expired_sessions()
        except Exception as e:
            logger.error(f"Error cleaning up sessions: {e}")
            return 0
    
    # Conversation Management
    
    def create_conversation(self, user_id: int, **kwargs) -> Optional[Conversation]:
        """Create a new conversation"""
        try:
            with self.session_manager.get_session() as session:
                self.conversation_repo.session = session
                return self.conversation_repo.create_conversation(user_id, **kwargs)
        except Exception as e:
            logger.error(f"Error creating conversation: {e}")
            return None
    
    def get_user_conversations(self, user_id: int, **kwargs) -> List[Conversation]:
        """Get user conversations"""
        try:
            with self.session_manager.get_session() as session:
                self.conversation_repo.session = session
                return self.conversation_repo.get_user_conversations(user_id, **kwargs)
        except Exception as e:
            logger.error(f"Error getting user conversations: {e}")
            return []
    
    def add_message(self, conversation_id: int, role: MessageRole, content: str, **kwargs) -> Optional[Message]:
        """Add a message to conversation"""
        try:
            with self.session_manager.get_session() as session:
                self.message_repo.session = session
                return self.message_repo.create_message(conversation_id, role, content, **kwargs)
        except Exception as e:
            logger.error(f"Error adding message: {e}")
            return None
    
    def get_conversation_messages(self, conversation_id: int, **kwargs) -> List[Message]:
        """Get conversation messages"""
        try:
            with self.session_manager.get_session() as session:
                self.message_repo.session = session
                return self.message_repo.get_conversation_messages(conversation_id, **kwargs)
        except Exception as e:
            logger.error(f"Error getting conversation messages: {e}")
            return []
    
    # Assessment Management
    
    def create_assessment(self, user_id: int, assessment_type: AssessmentType, **kwargs) -> Optional[Assessment]:
        """Create a new assessment"""
        try:
            with self.session_manager.get_session() as session:
                self.assessment_repo.session = session
                return self.assessment_repo.create_assessment(user_id, assessment_type, **kwargs)
        except Exception as e:
            logger.error(f"Error creating assessment: {e}")
            return None
    
    def complete_assessment(self, assessment_id: int, **kwargs) -> bool:
        """Complete an assessment with results"""
        try:
            with self.session_manager.transaction() as session:
                self.assessment_repo.session = session
                return self.assessment_repo.complete_assessment(assessment_id, **kwargs)
        except Exception as e:
            logger.error(f"Error completing assessment: {e}")
            return False
    
    def get_user_assessments(self, user_id: int, **kwargs) -> List[Assessment]:
        """Get user assessments"""
        try:
            with self.session_manager.get_session() as session:
                self.assessment_repo.session = session
                return self.assessment_repo.get_user_assessments(user_id, **kwargs)
        except Exception as e:
            logger.error(f"Error getting user assessments: {e}")
            return []
    
    def create_score(self, assessment_id: int, score_type: ScoreType, value: float, **kwargs) -> Optional[Score]:
        """Create a new score"""
        try:
            with self.session_manager.get_session() as session:
                self.score_repo.session = session
                return self.score_repo.create_score(assessment_id, score_type, value, **kwargs)
        except Exception as e:
            logger.error(f"Error creating score: {e}")
            return None
    
    def get_assessment_scores(self, assessment_id: int) -> List[Score]:
        """Get assessment scores"""
        try:
            with self.session_manager.get_session() as session:
                self.score_repo.session = session
                return self.score_repo.get_assessment_scores(assessment_id)
        except Exception as e:
            logger.error(f"Error getting assessment scores: {e}")
            return []
    
    # Intervention Management
    
    def get_suitable_interventions(self, **kwargs) -> List[Intervention]:
        """Get suitable interventions for user conditions"""
        try:
            with self.session_manager.get_session() as session:
                self.intervention_repo.session = session
                return self.intervention_repo.get_suitable_interventions(**kwargs)
        except Exception as e:
            logger.error(f"Error getting suitable interventions: {e}")
            return []
    
    def recommend_intervention(self, user_id: int, intervention_id: int, **kwargs) -> Optional[UserIntervention]:
        """Recommend an intervention to a user"""
        try:
            with self.session_manager.get_session() as session:
                self.user_intervention_repo.session = session
                return self.user_intervention_repo.recommend_intervention(user_id, intervention_id, **kwargs)
        except Exception as e:
            logger.error(f"Error recommending intervention: {e}")
            return None
    
    def accept_intervention(self, user_intervention_id: int) -> bool:
        """Accept a recommended intervention"""
        try:
            with self.session_manager.transaction() as session:
                self.user_intervention_repo.session = session
                return self.user_intervention_repo.accept_intervention(user_intervention_id)
        except Exception as e:
            logger.error(f"Error accepting intervention: {e}")
            return False
    
    def complete_intervention(self, user_intervention_id: int, **kwargs) -> bool:
        """Complete an intervention"""
        try:
            with self.session_manager.transaction() as session:
                self.user_intervention_repo.session = session
                return self.user_intervention_repo.complete_intervention(user_intervention_id, **kwargs)
        except Exception as e:
            logger.error(f"Error completing intervention: {e}")
            return False
    
    # Report Management
    
    def create_report(self, user_id: int, title: str, report_type: ReportType, **kwargs) -> Optional[Report]:
        """Create a new report"""
        try:
            with self.session_manager.get_session() as session:
                self.report_repo.session = session
                return self.report_repo.create_report(user_id, title, report_type, **kwargs)
        except Exception as e:
            logger.error(f"Error creating report: {e}")
            return None
    
    def complete_report_generation(self, report_id: int, **kwargs) -> bool:
        """Complete report generation"""
        try:
            with self.session_manager.transaction() as session:
                self.report_repo.session = session
                return self.report_repo.complete_generation(report_id, **kwargs)
        except Exception as e:
            logger.error(f"Error completing report generation: {e}")
            return False
    
    def get_user_reports(self, user_id: int, **kwargs) -> List[Report]:
        """Get user reports"""
        try:
            with self.session_manager.get_session() as session:
                self.report_repo.session = session
                return self.report_repo.get_user_reports(user_id, **kwargs)
        except Exception as e:
            logger.error(f"Error getting user reports: {e}")
            return []
    
    # Analytics and Statistics
    
    def get_user_dashboard_data(self, user_id: int) -> Dict[str, Any]:
        """Get comprehensive dashboard data for a user"""
        try:
            with PerformanceTimer("user_dashboard_data_fetch"):
                with self.session_manager.get_session() as session:
                    # Set session for all repositories
                    for repo in [self.user_repo, self.conversation_repo, self.assessment_repo, 
                                 self.user_intervention_repo, self.report_repo]:
                        repo.session = session
                    
                    # Get user info
                    user = self.user_repo.find_by_email("")  # Will be updated with actual email
                    
                    # Get recent assessments
                    recent_assessments = self.assessment_repo.get_recent_assessments(user_id, days=30)
                    
                    # Get latest scores
                    latest_scores = self.score_repo.get_latest_scores(user_id)
                    
                    # Get active interventions
                    active_interventions = self.user_intervention_repo.get_active_user_interventions(user_id)
                    
                    # Get recent reports
                    recent_reports = self.report_repo.get_recent_reports(user_id, days=30)
                    
                    return {
                        "user": user.to_safe_dict() if user else None,
                        "recent_assessments": [a.to_safe_dict() for a in recent_assessments[-5:]],
                        "latest_scores": {
                            score_type.value: score.to_safe_dict()
                            for score_type, score in latest_scores.items()
                        },
                        "active_interventions": [ui.to_safe_dict() for ui in active_interventions],
                        "recent_reports": [r.to_safe_dict() for r in recent_reports],
                        "statistics": {
                            "total_assessments": len(recent_assessments),
                            "total_interventions": len(active_interventions),
                            "total_reports": len(recent_reports)
                        }
                    }
        except Exception as e:
            logger.error(f"Error getting user dashboard data: {e}")
            return {}
    
    def get_system_statistics(self) -> Dict[str, Any]:
        """Get system-wide statistics"""
        try:
            with PerformanceTimer("system_statistics_fetch"):
                with self.session_manager.get_session() as session:
                    # Set session for all repositories
                    for repo in [self.user_repo, self.conversation_repo, self.assessment_repo,
                                 self.intervention_repo, self.report_repo]:
                        repo.session = session
                    
                    return {
                        "users": self.user_repo.get_user_statistics(),
                        "interventions": self.intervention_repo.get_intervention_statistics(),
                        "reports": self.report_repo.get_report_statistics()
                    }
        except Exception as e:
            logger.error(f"Error getting system statistics: {e}")
            return {}
    
    # Health and Maintenance
    
    def check_database_health(self) -> Dict[str, Any]:
        """Check database health status"""
        try:
            health_checker = self.session_manager.DatabaseHealthChecker()
            
            return {
                "connection": health_checker.check_connection(),
                "tables": health_checker.check_tables([
                    "users", "user_sessions", "conversations", "messages",
                    "assessments", "scores", "interventions", "user_interventions", "reports"
                ]),
                "database_info": health_checker.get_database_info()
            }
        except Exception as e:
            logger.error(f"Error checking database health: {e}")
            return {"status": "error", "message": str(e)}
    
    def perform_maintenance(self) -> Dict[str, Any]:
        """Perform database maintenance tasks"""
        try:
            with PerformanceTimer("database_maintenance"):
                with self.session_manager.get_session() as session:
                    # Clean up expired sessions
                    cleaned_sessions = self.session_repo.cleanup_expired_sessions()
                    
                    # Clean up expired reports
                    cleaned_reports = self.report_repo.cleanup_expired_reports()
                    
                    return {
                        "cleaned_sessions": cleaned_sessions,
                        "cleaned_reports": cleaned_reports,
                        "timestamp": datetime.utcnow().isoformat()
                    }
        except Exception as e:
            logger.error(f"Error performing maintenance: {e}")
            return {"error": str(e), "timestamp": datetime.utcnow().isoformat()}


# Global database service instance
_database_service = None


def get_database_service() -> DatabaseService:
    """Get the global database service instance"""
    global _database_service
    if _database_service is None:
        _database_service = DatabaseService()
    return _database_service
