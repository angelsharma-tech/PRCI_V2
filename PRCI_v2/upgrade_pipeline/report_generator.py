from io import BytesIO
from typing import Dict, List, Optional
import logging

# Import the new Premium Report Service
try:
    from services.report_service import get_report_service
except ImportError:
    # Fallback for different directory structures if needed
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from services.report_service import get_report_service

logger = logging.getLogger(__name__)

def generate_pdf_report(
    name: str,
    email: str,
    depression: float,
    anxiety: float,
    risk_level: str,
    root_causes: Dict[str, float],
    interventions: Optional[List[str]] = None,
    planner: Optional[Dict[str, List[str]]] = None,
    suggestions: Optional[List[str]] = None,
) -> bytes:
    """Generate a PDF report using the Premium Report Service (FPDF2).
    
    This replaces the legacy reportlab implementation with the high-density
    executive report architecture.
    """
    try:
        service = get_report_service()
        
        user_data = {
            "name": name,
            "email": email
        }
        
        # Map parameters to the new ReportService analysis_results structure
        analysis_results = {
            "depression_score": depression,
            "anxiety_score": anxiety,
            "risk_level": risk_level,
            "root_causes": root_causes,
            "ai_summary": suggestions[0] if suggestions else "Assessment reveals patterns of cognitive load impacting emotional stability.",
            "conversational_insight": "",
            "final_status": f"{risk_level} RISK · ACTIVE",
            "recommendations": interventions or []
        }
        
        # Generate the report
        result = service.generate_comprehensive_report(
            user_data=user_data,
            analysis_results=analysis_results,
            interventions=interventions or []
        )
        
        if result["status"] == "success":
            with open(result["file_path"], "rb") as f:
                return f.read()
        else:
            logger.error(f"Report generation failed: {result.get('error')}")
            return b"Report generation failed"
            
    except Exception as e:
        logger.error(f"Error in legacy wrapper for report generation: {e}")
        # Return a very basic error PDF or bytes if everything fails
        return b"Critical error during report generation"
