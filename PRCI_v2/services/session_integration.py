"""
Session Integration Service for PRCI v2
Phase 4.2 - Persistent Storage & User System Integration
"""

import json
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

from services.database_service import get_database_service
from models.session import UserSession
from models.user import User
from utils.logging_utils import get_logger, PerformanceTimer

logger = get_logger(__name__)


class SessionIntegration:
    """
    Integrates database session management with Streamlit session state
    """
    
    def __init__(self):
        self.db_service = get_database_service()
        self.current_session_id = None
        self.current_user_id = None
    
    def initialize_session(self, user_identifier: str) -> Optional[str]:
        """
        Initialize or resume a user session
        
        Args:
            user_identifier: Email or session ID
            
        Returns:
            Session ID
        """
        try:
            with PerformanceTimer("session_initialization"):
                # Try to find existing session
                if self._is_valid_session_id(user_identifier):
                    session = self.db_service.get_valid_session(user_identifier)
                    if session:
                        self.current_session_id = session.session_id
                        self.current_user_id = session.user_id
                        self._restore_streamlit_state(session)
                        logger.info(f"Resumed session: {user_identifier}")
                        return session.session_id
                
                # Try to find user by email
                user = self.db_service.get_user_by_email(user_identifier)
                if user:
                    # Create new session for existing user
                    session = self.db_service.create_session(
                        user_id=user.id,
                        user_agent=self._get_user_agent(),
                        ip_address=self._get_client_ip()
                    )
                    if session:
                        self.current_session_id = session.session_id
                        self.current_user_id = user.id
                        self._store_streamlit_state(session)
                        logger.info(f"Created new session for user: {user_identifier}")
                        return session.session_id
                
                # Create new user and session
                user = self.db_service.create_user(
                    email=user_identifier,
                    first_name="User",
                    status="ACTIVE"
                )
                
                if user:
                    session = self.db_service.create_session(
                        user_id=user.id,
                        user_agent=self._get_user_agent(),
                        ip_address=self._get_client_ip()
                    )
                    if session:
                        self.current_session_id = session.session_id
                        self.current_user_id = user.id
                        self._store_streamlit_state(session)
                        logger.info(f"Created new user and session: {user_identifier}")
                        return session.session_id
                
                return None
                
        except Exception as e:
            logger.error(f"Error initializing session: {e}")
            return None
    
    def get_current_user(self) -> Optional[Dict[str, Any]]:
        """
        Get current user information
        """
        try:
            if not self.current_user_id:
                return None
            
            user = self.db_service.get_user_by_email("")  # Will be updated with actual email lookup
            if user:
                return user.to_safe_dict()
            return None
            
        except Exception as e:
            logger.error(f"Error getting current user: {e}")
            return None
    
    def update_session_activity(self) -> bool:
        """
        Update current session activity
        """
        try:
            if not self.current_session_id:
                return False
            
            with self.db_service.session_manager.get_session() as session:
                self.db_service.session_repo.session = session
                return self.db_service.session_repo.update_session_activity(self.current_session_id)
                
        except Exception as e:
            logger.error(f"Error updating session activity: {e}")
            return False
    
    def store_assessment_data(self, assessment_data: Dict[str, Any]) -> bool:
        """
        Store assessment data in session
        """
        try:
            if not self.current_session_id:
                return False
            
            with self.db_service.session_manager.get_session() as session:
                self.db_service.session_repo.session = session
                
                # Get current session data
                current_data = self.db_service.session_repo.get_session_data(self.current_session_id)
                
                # Update with new assessment data
                if 'assessments' not in current_data:
                    current_data['assessments'] = []
                
                current_data['assessments'].append({
                    'timestamp': datetime.utcnow().isoformat(),
                    'data': assessment_data
                })
                
                return self.db_service.session_repo.set_session_data(
                    self.current_session_id, 
                    current_data
                )
                
        except Exception as e:
            logger.error(f"Error storing assessment data: {e}")
            return False
    
    def get_session_assessments(self) -> List[Dict[str, Any]]:
        """
        Get assessment data from current session
        """
        try:
            if not self.current_session_id:
                return []
            
            session_data = self.db_service.session_repo.get_session_data(self.current_session_id)
            return session_data.get('assessments', [])
            
        except Exception as e:
            logger.error(f"Error getting session assessments: {e}")
            return []
    
    def store_conversation_context(self, conversation_id: int, context_data: Dict[str, Any]) -> bool:
        """
        Store conversation context in session
        """
        try:
            if not self.current_session_id:
                return False
            
            with self.db_service.session_manager.get_session() as session:
                self.db_service.session_repo.session = session
                
                # Get current session data
                current_data = self.db_service.session_repo.get_session_data(self.current_session_id)
                
                # Update with new conversation data
                if 'conversations' not in current_data:
                    current_data['conversations'] = {}
                
                current_data['conversations'][str(conversation_id)] = {
                    'last_updated': datetime.utcnow().isoformat(),
                    'context': context_data
                }
                
                return self.db_service.session_repo.set_session_data(
                    self.current_session_id,
                    current_data
                )
                
        except Exception as e:
            logger.error(f"Error storing conversation context: {e}")
            return False
    
    def get_conversation_context(self, conversation_id: int) -> Optional[Dict[str, Any]]:
        """
        Get conversation context from session
        """
        try:
            if not self.current_session_id:
                return None
            
            session_data = self.db_service.session_repo.get_session_data(self.current_session_id)
            conversations = session_data.get('conversations', {})
            return conversations.get(str(conversation_id))
            
        except Exception as e:
            logger.error(f"Error getting conversation context: {e}")
            return None
    
    def store_intervention_state(self, intervention_id: int, state_data: Dict[str, Any]) -> bool:
        """
        Store intervention state in session
        """
        try:
            if not self.current_session_id:
                return False
            
            with self.db_service.session_manager.get_session() as session:
                self.db_service.session_repo.session = session
                
                # Get current session data
                current_data = self.db_service.session_repo.get_session_data(self.current_session_id)
                
                # Update with new intervention data
                if 'interventions' not in current_data:
                    current_data['interventions'] = {}
                
                current_data['interventions'][str(intervention_id)] = {
                    'last_updated': datetime.utcnow().isoformat(),
                    'state': state_data
                }
                
                return self.db_service.session_repo.set_session_data(
                    self.current_session_id,
                    current_data
                )
                
        except Exception as e:
            logger.error(f"Error storing intervention state: {e}")
            return False
    
    def get_intervention_state(self, intervention_id: int) -> Optional[Dict[str, Any]]:
        """
        Get intervention state from session
        """
        try:
            if not self.current_session_id:
                return None
            
            session_data = self.db_service.session_repo.get_session_data(self.current_session_id)
            interventions = session_data.get('interventions', {})
            return interventions.get(str(intervention_id))
            
        except Exception as e:
            logger.error(f"Error getting intervention state: {e}")
            return None
    
    def cleanup_expired_sessions(self) -> int:
        """
        Clean up expired sessions
        """
        try:
            return self.db_service.cleanup_expired_sessions()
        except Exception as e:
            logger.error(f"Error cleaning up expired sessions: {e}")
            return 0
    
    def terminate_session(self) -> bool:
        """
        Terminate current session
        """
        try:
            if not self.current_session_id:
                return False
            
            success = self.db_service.session_repo.deactivate_session(self.current_session_id)
            if success:
                self.current_session_id = None
                self.current_user_id = None
                logger.info("Session terminated")
            
            return success
            
        except Exception as e:
            logger.error(f"Error terminating session: {e}")
            return False
    
    def get_session_statistics(self) -> Dict[str, Any]:
        """
        Get session statistics
        """
        try:
            return self.db_service.session_repo.get_session_statistics(
                user_id=self.current_user_id
            )
        except Exception as e:
            logger.error(f"Error getting session statistics: {e}")
            return {}
    
    def _is_valid_session_id(self, identifier: str) -> bool:
        """
        Check if identifier is a valid session ID format
        """
        try:
            # UUID format validation
            uuid.UUID(identifier)
            return True
        except ValueError:
            return False
    
    def _get_user_agent(self) -> str:
        """
        Get current user agent
        """
        try:
            import streamlit as st
            return st.experimental_get_query_params().get('user_agent', ['unknown'])[0]
        except:
            return "unknown"
    
    def _get_client_ip(self) -> str:
        """
        Get client IP address
        """
        try:
            import streamlit as st
            return st.experimental_get_query_params().get('client_ip', ['127.0.0.1'])[0]
        except:
            return "127.0.0.1"
    
    def _store_streamlit_state(self, session: UserSession) -> None:
        """
        Store session data in Streamlit session state
        """
        try:
            import streamlit as st
            
            # Store session ID
            st.session_state['db_session_id'] = session.session_id
            st.session_state['db_user_id'] = session.user_id
            
            # Store session data
            session_data = session.get_session_data()
            if session_data:
                st.session_state['db_session_data'] = session_data
                
        except Exception as e:
            logger.error(f"Error storing Streamlit state: {e}")
    
    def _restore_streamlit_state(self, session: UserSession) -> None:
        """
        Restore Streamlit session state from database
        """
        try:
            import streamlit as st
            
            # Restore session ID
            st.session_state['db_session_id'] = session.session_id
            st.session_state['db_user_id'] = session.user_id
            
            # Restore session data
            session_data = session.get_session_data()
            if session_data:
                st.session_state['db_session_data'] = session_data
                
        except Exception as e:
            logger.error(f"Error restoring Streamlit state: {e}")
    
    def get_streamlit_session_id(self) -> Optional[str]:
        """
        Get session ID from Streamlit session state
        """
        try:
            import streamlit as st
            return st.session_state.get('db_session_id')
        except:
            return None
    
    def get_streamlit_user_id(self) -> Optional[int]:
        """
        Get user ID from Streamlit session state
        """
        try:
            import streamlit as st
            return st.session_state.get('db_user_id')
        except:
            return None
    
    def sync_streamlit_state(self) -> bool:
        """
        Synchronize database session with Streamlit session state
        """
        try:
            import streamlit as st
            
            # Get Streamlit session ID
            streamlit_session_id = st.session_state.get('db_session_id')
            
            if not streamlit_session_id:
                return False
            
            # If database session doesn't match, update database
            if self.current_session_id != streamlit_session_id:
                session = self.db_service.get_valid_session(streamlit_session_id)
                if session:
                    self.current_session_id = session.session_id
                    self.current_user_id = session.user_id
                    self._restore_streamlit_state(session)
                    logger.info(f"Synchronized session: {streamlit_session_id}")
                    return True
            
            return True
            
        except Exception as e:
            logger.error(f"Error synchronizing Streamlit state: {e}")
            return False


# Global session integration instance
_session_integration = None


def get_session_integration() -> SessionIntegration:
    """
    Get the global session integration instance
    """
    global _session_integration
    if _session_integration is None:
        _session_integration = SessionIntegration()
    return _session_integration
