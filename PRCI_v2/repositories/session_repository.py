"""
Session Repository for PRCI v2
Phase 4.2 - Persistent Storage & User System Integration
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from sqlalchemy.orm import Session
from sqlalchemy import and_

from .base import BaseRepository
from models.session import UserSession
from utils.logging_utils import get_logger

logger = get_logger(__name__)


class SessionRepository(BaseRepository[UserSession]):
    """
    Repository for UserSession model operations
    """
    
    def get_model_class(self):
        return UserSession
    
    # Session-specific operations
    
    def create_session(self, user_id: int, user_agent: str = None, 
                     ip_address: str = None, expires_hours: int = 24) -> UserSession:
        """Create a new user session"""
        session_data = {
            'user_id': user_id,
            'user_agent': user_agent,
            'ip_address': ip_address,
            'expires_hours': expires_hours
        }
        
        return UserSession.create_session(
            self.session, user_id, user_agent, ip_address, expires_hours
        )
    
    def find_by_session_id(self, session_id: str) -> Optional[UserSession]:
        """Find session by session ID"""
        return UserSession.find_by_session_id(self.session, session_id)
    
    def find_active_sessions(self, user_id: int) -> List[UserSession]:
        """Find all active sessions for a user"""
        return UserSession.find_active_sessions(self.session, user_id)
    
    def get_valid_session(self, session_id: str) -> Optional[UserSession]:
        """Get a valid (active and not expired) session"""
        session = self.find_by_session_id(session_id)
        if session and session.is_valid():
            return session
        return None
    
    def deactivate_session(self, session_id: str) -> bool:
        """Deactivate a specific session"""
        try:
            session = self.find_by_session_id(session_id)
            if session:
                session.deactivate()
                self.session.commit()
                logger.info(f"Deactivated session {session_id}")
                return True
            return False
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error deactivating session {session_id}: {e}")
            raise
    
    def deactivate_user_sessions(self, user_id: int) -> int:
        """Deactivate all sessions for a user"""
        try:
            sessions = self.find_active_sessions(user_id)
            deactivated_count = 0
            
            for session in sessions:
                session.deactivate()
                deactivated_count += 1
            
            self.session.commit()
            logger.info(f"Deactivated {deactivated_count} sessions for user {user_id}")
            return deactivated_count
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error deactivating sessions for user {user_id}: {e}")
            raise
    
    def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions"""
        return UserSession.cleanup_expired_sessions(self.session)
    
    def extend_session(self, session_id: str, hours: int = 24) -> bool:
        """Extend session expiration"""
        try:
            session = self.find_by_session_id(session_id)
            if session:
                session.extend_session(hours)
                self.session.commit()
                logger.info(f"Extended session {session_id} by {hours} hours")
                return True
            return False
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error extending session {session_id}: {e}")
            raise
    
    def update_session_activity(self, session_id: str) -> bool:
        """Update session activity timestamp"""
        try:
            session = self.find_by_session_id(session_id)
            if session:
                session.update_activity()
                self.session.commit()
                return True
            return False
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error updating session activity {session_id}: {e}")
            raise
    
    def set_session_data(self, session_id: str, data: Dict[str, Any]) -> bool:
        """Store session data"""
        try:
            session = self.find_by_session_id(session_id)
            if session:
                session.set_session_data(data)
                self.session.commit()
                return True
            return False
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error setting session data {session_id}: {e}")
            raise
    
    def get_session_data(self, session_id: str) -> Dict[str, Any]:
        """Get session data"""
        session = self.find_by_session_id(session_id)
        if session:
            return session.get_session_data()
        return {}
    
    def set_streamlit_state(self, session_id: str, state_data: Dict[str, Any]) -> bool:
        """Store Streamlit session state"""
        try:
            session = self.find_by_session_id(session_id)
            if session:
                session.set_streamlit_state(state_data)
                self.session.commit()
                return True
            return False
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error setting Streamlit state {session_id}: {e}")
            raise
    
    def get_streamlit_state(self, session_id: str) -> Dict[str, Any]:
        """Get Streamlit session state"""
        session = self.find_by_session_id(session_id)
        if session:
            return session.get_streamlit_state()
        return {}
    
    def get_user_sessions(self, user_id: int, include_expired: bool = False) -> List[UserSession]:
        """Get all sessions for a user"""
        try:
            query = self.session.query(UserSession).filter(
                and_(
                    UserSession.user_id == user_id,
                    UserSession.is_deleted == 'N'
                )
            )
            
            if not include_expired:
                query = query.filter(UserSession.expires_at > datetime.utcnow())
            
            return query.order_by(UserSession.last_activity_at.desc()).all()
        except Exception as e:
            logger.error(f"Error getting sessions for user {user_id}: {e}")
            raise
    
    def get_session_statistics(self, user_id: int = None) -> Dict[str, Any]:
        """Get session statistics"""
        try:
            query = self.session.query(UserSession).filter(
                UserSession.is_deleted == 'N'
            )
            
            if user_id:
                query = query.filter(UserSession.user_id == user_id)
            
            total_sessions = query.count()
            
            # Active sessions
            active_query = query.filter(
                and_(
                    UserSession.is_active == True,
                    UserSession.expires_at > datetime.utcnow()
                )
            )
            active_sessions = active_query.count()
            
            # Expired sessions
            expired_query = query.filter(UserSession.expires_at <= datetime.utcnow())
            expired_sessions = expired_query.count()
            
            # Recent sessions (last 24 hours)
            twenty_four_hours_ago = datetime.utcnow() - timedelta(hours=24)
            recent_sessions = query.filter(
                UserSession.created_at >= twenty_four_hours_ago
            ).count()
            
            return {
                'total_sessions': total_sessions,
                'active_sessions': active_sessions,
                'expired_sessions': expired_sessions,
                'recent_sessions': recent_sessions,
                'activity_rate': (active_sessions / total_sessions * 100) if total_sessions > 0 else 0
            }
        except Exception as e:
            logger.error(f"Error getting session statistics: {e}")
            raise
    
    def get_sessions_by_ip(self, ip_address: str) -> List[UserSession]:
        """Get sessions by IP address"""
        try:
            return self.session.query(UserSession).filter(
                and_(
                    UserSession.ip_address == ip_address,
                    UserSession.is_deleted == 'N',
                    UserSession.expires_at > datetime.utcnow()
                )
            ).all()
        except Exception as e:
            logger.error(f"Error getting sessions by IP {ip_address}: {e}")
            raise
    
    def get_long_running_sessions(self, hours: int = 24) -> List[UserSession]:
        """Get sessions running longer than specified hours"""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            return self.session.query(UserSession).filter(
                and_(
                    UserSession.created_at <= cutoff_time,
                    UserSession.is_active == True,
                    UserSession.is_deleted == 'N',
                    UserSession.expires_at > datetime.utcnow()
                )
            ).all()
        except Exception as e:
            logger.error(f"Error getting long running sessions: {e}")
            raise
    
    def terminate_all_sessions(self) -> int:
        """Terminate all active sessions (emergency use)"""
        try:
            terminated_count = self.session.query(UserSession).filter(
                and_(
                    UserSession.is_active == True,
                    UserSession.is_deleted == 'N'
                )
            ).update({'is_active': False})
            
            self.session.commit()
            logger.info(f"Terminated all active sessions: {terminated_count}")
            return terminated_count
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error terminating all sessions: {e}")
            raise
