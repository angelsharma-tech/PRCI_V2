"""
Persistence Service for PRCI v2
Phase 4.2 - Persistent Storage & User System Integration
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

from services.database_service import get_database_service
from services.session_integration import get_session_integration
from services.inference_service import get_inference_service
from services.scoring_service import get_scoring_service
from services.intervention_service import get_intervention_service
from services.report_service import get_report_service

from models.assessment import Assessment, AssessmentType, AssessmentStatus, ScoreType
from models.conversation import Conversation, Message, MessageRole
from models.intervention import Intervention, UserIntervention, UserInterventionStatus
from models.report import Report, ReportType, ReportFormat, ReportStatus

from utils.logging_utils import get_logger, PerformanceTimer

logger = get_logger(__name__)


class PersistenceService:
    """
    High-level persistence service that bridges the database layer with application services
    """
    
    def __init__(self):
        self.db_service = get_database_service()
        self.session_integration = get_session_integration()
        self.inference_service = get_inference_service()
        self.scoring_service = get_scoring_service()
        self.intervention_service = get_intervention_service()
        self.report_service = get_report_service()
    
    # Assessment Persistence
    
    def save_assessment(self, user_id: int, input_text: str, **kwargs) -> Optional[int]:
        """
        Save a complete assessment with scores and analysis
        """
        try:
            with PerformanceTimer("assessment_save"):
                # Create assessment record
                assessment = self.db_service.create_assessment(
                    user_id=user_id,
                    assessment_type=AssessmentType.AUTOMATIC,
                    input_text=input_text,
                    **kwargs
                )
                
                if not assessment:
                    logger.error("Failed to create assessment record")
                    return None
                
                # Run inference analysis
                analysis_result = self.inference_service.analyze_text(input_text)
                
                if not analysis_result:
                    logger.error("Failed to run inference analysis")
                    return assessment.id
                
                # Create scores
                scores = []
                
                # Depression score
                if analysis_result.get('depression_score') is not None:
                    depression_score = self.db_service.create_score(
                        assessment_id=assessment.id,
                        score_type=ScoreType.DEPRESSION,
                        value=analysis_result['depression_score'],
                        confidence=analysis_result.get('confidence', {}).get('depression')
                    )
                    scores.append(depression_score)
                
                # Anxiety score
                if analysis_result.get('anxiety_score') is not None:
                    anxiety_score = self.db_service.create_score(
                        assessment_id=assessment.id,
                        score_type=ScoreType.ANXIETY,
                        value=analysis_result['anxiety_score'],
                        confidence=analysis_result.get('confidence', {}).get('anxiety')
                    )
                    scores.append(anxiety_score)
                
                # Overall score
                if analysis_result.get('risk_level'):
                    overall_score = 0.5  # Default mid-range
                    if analysis_result['risk_level'] == 'HIGH':
                        overall_score = 0.8
                    elif analysis_result['risk_level'] == 'LOW':
                        overall_score = 0.2
                    
                    overall_score_record = self.db_service.create_score(
                        assessment_id=assessment.id,
                        score_type=ScoreType.OVERALL,
                        value=overall_score
                    )
                    scores.append(overall_score_record)
                
                # Complete assessment with results
                success = self.db_service.complete_assessment(
                    assessment_id=assessment.id,
                    risk_level=analysis_result.get('risk_level'),
                    primary_root_cause=analysis_result.get('top_root_cause'),
                    root_cause_data=analysis_result.get('root_causes'),
                    model_version=analysis_result.get('model_version'),
                    model_confidence=analysis_result.get('confidence', {}).get('overall'),
                    processing_time_ms=analysis_result.get('processing_time_ms')
                )
                
                if success:
                    # Store in session for immediate use
                    self.session_integration.store_assessment_data({
                        'assessment_id': assessment.id,
                        'analysis_result': analysis_result,
                        'timestamp': datetime.utcnow().isoformat()
                    })
                    
                    logger.info(f"Assessment saved successfully: {assessment.id}")
                    return assessment.id
                else:
                    logger.error("Failed to complete assessment")
                    return assessment.id
                
        except Exception as e:
            logger.error(f"Error saving assessment: {e}")
            return None
    
    def get_user_assessment_history(self, user_id: int, days: int = 30) -> List[Dict[str, Any]]:
        """
        Get user's assessment history
        """
        try:
            assessments = self.db_service.get_user_assessments(user_id)
            
            # Enrich with scores and analysis
            enriched_assessments = []
            for assessment in assessments:
                scores = self.db_service.get_assessment_scores(assessment.id)
                
                # Convert scores to dictionary
                score_dict = {}
                for score in scores:
                    score_dict[score.score_type.value] = score.to_safe_dict()
                
                # Get session data if available
                session_assessments = self.session_integration.get_session_assessments()
                session_assessment = next(
                    (sa for sa in session_assessments 
                     if sa.get('assessment_id') == assessment.id), 
                    None
                )
                
                enriched_assessments.append({
                    'assessment': assessment.to_safe_dict(),
                    'scores': score_dict,
                    'session_data': session_assessment,
                    'has_session_data': session_assessment is not None
                })
            
            return enriched_assessments
            
        except Exception as e:
            logger.error(f"Error getting assessment history: {e}")
            return []
    
    # Conversation Persistence
    
    def save_conversation_message(self, conversation_id: int, role: MessageRole, 
                              content: str, **kwargs) -> Optional[int]:
        """
        Save a conversation message
        """
        try:
            message = self.db_service.add_message(
                conversation_id=conversation_id,
                role=role,
                content=content,
                **kwargs
            )
            
            if message:
                # Update conversation activity
                self.db_service.update_conversation_activity(conversation_id)
                
                # Store in session context
                context_data = self.session_integration.get_conversation_context(conversation_id) or {}
                context_data['last_message'] = {
                    'id': message.id,
                    'role': role.value,
                    'content': content[:200],  # Truncate for storage
                    'timestamp': datetime.utcnow().isoformat()
                }
                
                self.session_integration.store_conversation_context(conversation_id, context_data)
                
                logger.info(f"Message saved: {message.id}")
                return message.id
            
            return None
            
        except Exception as e:
            logger.error(f"Error saving conversation message: {e}")
            return None
    
    def get_conversation_history(self, user_id: int, conversation_id: int = None) -> List[Dict[str, Any]]:
        """
        Get conversation history for a user
        """
        try:
            if conversation_id:
                # Get specific conversation
                conversations = [self.db_service.conversation_repo.get_by_id(conversation_id)]
            else:
                # Get all user conversations
                conversations = self.db_service.get_user_conversations(user_id)
            
            # Enrich with messages
            enriched_conversations = []
            for conversation in conversations:
                messages = self.db_service.get_conversation_messages(conversation.id, limit=100)
                
                enriched_conversations.append({
                    'conversation': conversation.to_safe_dict(),
                    'messages': [msg.to_safe_dict() for msg in messages],
                    'message_count': len(messages),
                    'session_context': self.session_integration.get_conversation_context(conversation.id)
                })
            
            return enriched_conversations
            
        except Exception as e:
            logger.error(f"Error getting conversation history: {e}")
            return []
    
    # Intervention Persistence
    
    def recommend_and_track_interventions(self, user_id: int, assessment_id: int, 
                                       root_cause: str = None, risk_level: str = None) -> List[Dict[str, Any]]:
        """
        Recommend interventions based on assessment and track them
        """
        try:
            # Get suitable interventions
            interventions = self.db_service.get_suitable_interventions(
                root_cause=root_cause,
                risk_level=risk_level
            )
            
            tracked_interventions = []
            
            for intervention in interventions[:3]:  # Top 3 recommendations
                # Create user intervention record
                user_intervention = self.db_service.recommend_intervention(
                    user_id=user_id,
                    intervention_id=intervention.id,
                    assessment_id=assessment_id,
                    personalized_notes=f"Recommended based on {root_cause or 'general'} assessment"
                )
                
                if user_intervention:
                    # Store intervention state in session
                    self.session_integration.store_intervention_state(
                        intervention_id=user_intervention.id,
                        state_data={
                            'recommended_at': datetime.utcnow().isoformat(),
                            'source': 'assessment',
                            'root_cause': root_cause,
                            'risk_level': risk_level,
                            'intervention_data': intervention.to_safe_dict()
                        }
                    )
                    
                    tracked_interventions.append({
                        'user_intervention': user_intervention.to_safe_dict(),
                        'intervention': intervention.to_safe_dict(),
                        'state': self.session_integration.get_intervention_state(user_intervention.id)
                    })
            
            return tracked_interventions
            
        except Exception as e:
            logger.error(f"Error recommending interventions: {e}")
            return []
    
    def update_intervention_progress(self, user_intervention_id: int, progress_percentage: float, 
                                rating: int = None, feedback: str = None) -> bool:
        """
        Update intervention progress and completion
        """
        try:
            # Update progress in database
            success = self.db_service.update_progress(user_intervention_id, progress_percentage)
            
            if progress_percentage >= 1.0:
                # Complete the intervention
                success = self.db_service.complete_intervention(
                    user_intervention_id,
                    rating=rating,
                    feedback=feedback,
                    effectiveness=rating
                ) and success
            
            # Update session state
            if success:
                current_state = self.session_integration.get_intervention_state(user_intervention_id) or {}
                current_state.update({
                    'progress': progress_percentage,
                    'last_updated': datetime.utcnow().isoformat()
                })
                
                if progress_percentage >= 1.0:
                    current_state['completed_at'] = current_state['last_updated']
                    if rating:
                        current_state['rating'] = rating
                    if feedback:
                        current_state['feedback'] = feedback
                
                self.session_integration.store_intervention_state(user_intervention_id, current_state)
            
            return success
            
        except Exception as e:
            logger.error(f"Error updating intervention progress: {e}")
            return False
    
    # Report Persistence
    
    def generate_and_save_report(self, user_id: int, report_type: ReportType, 
                              title: str, **kwargs) -> Optional[int]:
        """
        Generate and save a report
        """
        try:
            # Create report record
            report = self.db_service.create_report(
                user_id=user_id,
                title=title,
                report_type=report_type,
                **kwargs
            )
            
            if not report:
                logger.error("Failed to create report record")
                return None
            
            # Start generation
            self.db_service.start_generation(report.id)
            
            # Generate report content based on type
            if report_type == ReportType.COMPREHENSIVE:
                # Get user data for comprehensive report
                user_data = self.db_service.get_user_dashboard_data(user_id)
                file_data = self._generate_comprehensive_report_content(user_data)
            else:
                # Generate other report types
                file_data = self._generate_other_report_content(user_id, report_type, **kwargs)
            
            # Complete report generation
            success = self.db_service.complete_generation(
                report_id=report.id,
                file_data=file_data,
                generation_time_ms=kwargs.get('generation_time_ms')
            )
            
            if success:
                logger.info(f"Report generated successfully: {report.id}")
                return report.id
            else:
                logger.error(f"Report generation failed: {report.id}")
                return report.id
                
        except Exception as e:
            logger.error(f"Error generating report: {e}")
            return None
    
    def _generate_comprehensive_report_content(self, user_data: Dict[str, Any]) -> bytes:
        """
        Generate comprehensive report content
        """
        try:
            # Use existing report generation service
            user_info = {
                'name': user_data.get('user', {}).get('full_name', 'User'),
                'email': user_data.get('user', {}).get('email', '')
            }
            
            analysis_results = {
                'depression_score': user_data.get('latest_scores', {}).get('DEPRESSION', {}).get('value', 0),
                'anxiety_score': user_data.get('latest_scores', {}).get('ANXIETY', {}).get('value', 0),
                'risk_level': 'MODERATE',  # Would be calculated
                'top_root_cause': 'general'
            }
            
            interventions = user_data.get('active_interventions', [])
            
            # Generate PDF using existing service
            from upgrade_pipeline.report_generator import generate_pdf_report
            
            return generate_pdf_report(
                user_info['name'],
                user_info['email'],
                analysis_results['depression_score'],
                analysis_results['anxiety_score'],
                analysis_results['risk_level'],
                {},
                interventions
            )
            
        except Exception as e:
            logger.error(f"Error generating comprehensive report content: {e}")
            return b"Report generation failed"
    
    def _generate_other_report_content(self, user_id: int, report_type: ReportType, **kwargs) -> bytes:
        """
        Generate other report types
        """
        try:
            # Implementation for other report types
            if report_type == ReportType.SUMMARY:
                return self._generate_summary_report_content(user_id, **kwargs)
            elif report_type == ReportType.TREND:
                return self._generate_trend_report_content(user_id, **kwargs)
            else:
                return b"Report type not implemented"
                
        except Exception as e:
            logger.error(f"Error generating {report_type} report: {e}")
            return f"Error generating {report_type} report".encode()
    
    def _generate_summary_report_content(self, user_id: int, **kwargs) -> bytes:
        """
        Generate summary report content
        """
        # Get user statistics
        stats = self.db_service.get_user_assessments(user_id)
        
        # Create simple text report
        content = f"""
        PRCI v2 Summary Report
        Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}
        
        User ID: {user_id}
        Total Assessments: {len(stats)}
        
        Recent Assessments:
        {chr(10).join([f"- {a.title} ({a.created_at})" for a in stats[-5:]])}
        """
        
        return content.encode('utf-8')
    
    def _generate_trend_report_content(self, user_id: int, **kwargs) -> bytes:
        """
        Generate trend report content
        """
        # Get score trends
        score_trends = self.db_service.score_repo.get_score_trends(user_id, ScoreType.OVERALL)
        
        # Create simple CSV content
        content = "Date,Overall Score,Risk Category\n"
        for trend in score_trends:
            content += f"{trend['date']},{trend['value']},{trend['risk_category']}\n"
        
        return content.encode('utf-8')
    
    def get_user_dashboard_data_persistent(self, user_id: int) -> Dict[str, Any]:
        """
        Get comprehensive dashboard data combining database and session data
        """
        try:
            with PerformanceTimer("dashboard_data_fetch"):
                # Get database data
                db_data = self.db_service.get_user_dashboard_data(user_id)
                
                # Get session data
                session_assessments = self.session_integration.get_session_assessments()
                session_conversations = {}
                session_interventions = {}
                
                # Get conversation contexts
                for conversation in db_data.get('recent_conversations', []):
                    context = self.session_integration.get_conversation_context(conversation['id'])
                    if context:
                        session_conversations[str(conversation['id'])] = context
                
                # Get intervention states
                for intervention in db_data.get('active_interventions', []):
                    state = self.session_integration.get_intervention_state(intervention['id'])
                    if state:
                        session_interventions[str(intervention['id'])] = state
                
                return {
                    **db_data,
                    'session_data': {
                        'assessments': session_assessments,
                        'conversations': session_conversations,
                        'interventions': session_interventions
                    }
                }
                
        except Exception as e:
            logger.error(f"Error getting persistent dashboard data: {e}")
            return {}
    
    # Data Export and Import
    
    def export_user_data(self, user_id: int, format_type: str = 'json') -> Optional[bytes]:
        """
        Export user data in specified format
        """
        try:
            dashboard_data = self.get_user_dashboard_data_persistent(user_id)
            
            if format_type.lower() == 'json':
                import json
                return json.dumps(dashboard_data, indent=2, default=str).encode('utf-8')
            
            elif format_type.lower() == 'csv':
                import csv
                import io
                
                output = io.StringIO()
                writer = csv.writer(output)
                
                # Write header
                writer.writerow(['Data Type', 'ID', 'Created At', 'Details'])
                
                # Write assessments
                for assessment in dashboard_data.get('recent_assessments', []):
                    writer.writerow([
                        'Assessment',
                        assessment['id'],
                        assessment['created_at'],
                        json.dumps(assessment)
                    ])
                
                # Write interventions
                for intervention in dashboard_data.get('active_interventions', []):
                    writer.writerow([
                        'Intervention',
                        intervention['id'],
                        intervention['recommended_at'],
                        json.dumps(intervention)
                    ])
                
                return output.getvalue().encode('utf-8')
            
            else:
                return b"Unsupported format"
                
        except Exception as e:
            logger.error(f"Error exporting user data: {e}")
            return None
    
    def cleanup_old_data(self, days: int = 90) -> Dict[str, int]:
        """
        Clean up old data based on retention policy
        """
        try:
            with PerformanceTimer("data_cleanup"):
                # Clean up expired sessions
                cleaned_sessions = self.db_service.cleanup_expired_sessions()
                
                # Clean up old reports (would be implemented in report service)
                # cleaned_reports = self.db_service.report_repo.cleanup_expired_reports()
                cleaned_reports = 0
                
                return {
                    'cleaned_sessions': cleaned_sessions,
                    'cleaned_reports': cleaned_reports,
                    'timestamp': datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error cleaning up old data: {e}")
            return {'error': str(e)}


# Global persistence service instance
_persistence_service = None


def get_persistence_service() -> PersistenceService:
    """
    Get the global persistence service instance
    """
    global _persistence_service
    if _persistence_service is None:
        _persistence_service = PersistenceService()
    return _persistence_service
