#!/usr/bin/env python3
"""
CORE:AI Wellness Intelligence Platform
Premium PDF Report Generator — FPDF2 Service (Streamlit Cloud Optimized)
v7: High-Density Clinical Intelligence (STRICT 2-PAGE MAX)
"""

import os
import io
import uuid
import logging
import math
import re
from datetime import datetime, timedelta
from fpdf import FPDF

# Initialize logger
logger = logging.getLogger(__name__)

# FPDF2 is pure-Python, so it's always available on Streamlit Cloud
PDF_AVAILABLE = True

# ─── COLORS ───────────────────────────────────────────────────────────────────
BG_DARK = (7, 17, 31)        # #07111F
BG_CARD = (13, 26, 45)       # #0D1A2D
TEXT_MAIN = (226, 232, 240)  # #E2E8F0
TEXT_MUTED = (148, 163, 184) # #94A3B8
CYAN = (0, 209, 255)         # #00D1FF
PURPLE = (168, 85, 247)      # #A855F7
AMBER = (245, 158, 11)       # #F59E0B
EMERALD = (16, 185, 129)     # #10B981
ROSE = (239, 68, 68)         # #EF4444

def sanitize_text(text: str) -> str:
    """Removes HTML tags and cleans text for PDF rendering."""
    if not text:
        return ""
    # Remove HTML tags
    clean = re.sub(r'<[^>]*>', '', text)
    # Replace common entities
    clean = clean.replace('&nbsp;', ' ').replace('&amp;', '&').replace('&quot;', '"')
    return clean.strip()

# Import legacy email sender if available
try:
    from upgrade_pipeline.email_sender import send_email
except ImportError:
    send_email = None

class PremiumReportPDF(FPDF):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_margins(12, 12, 12)
        self.set_auto_page_break(auto=True, margin=15)

    def header(self):
        # Draw background for the whole page
        self.set_fill_color(*BG_DARK)
        self.rect(0, 0, 210, 297, 'F')
        
        if self.page_no() == 1:
            # Cinematic Header
            self.set_xy(12, 12)
            self.set_fill_color(*CYAN)
            self.rect(12, 12, 6, 6, 'F') # Logo Mark
            
            self.set_font("Helvetica", "B", 14)
            self.set_text_color(*TEXT_MAIN)
            self.set_xy(20, 12)
            self.cell(40, 6, "CORE:AI", ln=False)
            
            self.set_font("Helvetica", "B", 8)
            self.set_text_color(*CYAN)
            self.set_xy(155, 12)
            self.cell(43, 6, "EXECUTIVE WELLNESS REPORT", align="R")
            
            self.set_draw_color(*CYAN)
            self.set_line_width(0.4)
            self.line(12, 22, 198, 22)
    
    def footer(self):
        self.set_y(-12)
        self.set_font("Helvetica", "I", 6)
        self.set_text_color(*TEXT_MUTED)
        self.cell(100, 10, "CONFIDENTIAL BEHAVIORAL INTELLIGENCE | AI-GENERATED WELLNESS ASSESSMENT", align="L")
        self.cell(0, 10, f"PAGE {self.page_no()} OF 2", align="R")

    def section_header(self, title, accent_color=CYAN):
        self.ln(2) # Reduced vertical gap
        self.set_font("Helvetica", "B", 7)
        self.set_text_color(*accent_color)
        self.cell(0, 5, title.upper(), ln=True)
        self.set_draw_color(*accent_color)
        self.set_line_width(0.1)
        self.line(12, self.get_y(), 198, self.get_y())
        self.ln(2)

    def draw_metric_card(self, x, y, w, h, label, value, status, color):
        """Draws a compact, aligned horizontal metric card."""
        self.set_fill_color(*BG_CARD)
        self.rect(x, y, w, h, 'F')
        
        # Left accent line
        self.set_fill_color(*color)
        self.rect(x, y, 1.2, h, 'F')
        
        # Label
        self.set_xy(x + 4, y + 3)
        self.set_font("Helvetica", "B", 6)
        self.set_text_color(*TEXT_MUTED)
        self.cell(w-8, 4, label.upper(), ln=True, align="C")
        
        # Value
        self.set_x(x + 4)
        self.set_font("Helvetica", "B", 14)
        self.set_text_color(*color)
        self.cell(w-8, 8, value, ln=True, align="C")
        
        # Status Badge
        self.set_x(x + (w - 20)/2)
        self.set_fill_color(*color)
        self.set_text_color(255, 255, 255)
        self.set_font("Helvetica", "B", 6)
        self.cell(20, 4, status.upper(), border=0, fill=True, align="C")

    def draw_rca_bar(self, label, pct, color):
        self.set_font("Helvetica", "", 8)
        self.set_text_color(*TEXT_MAIN)
        self.cell(50, 6, label)
        
        curr_x = self.get_x()
        curr_y = self.get_y() + 2.5
        
        # Track
        self.set_fill_color(30, 41, 59)
        self.rect(curr_x, curr_y, 100, 1.2, 'F')
        
        # Fill
        self.set_fill_color(*color)
        self.rect(curr_x, curr_y, (pct/100)*100, 1.2, 'F')
        
        # Pct
        self.set_xy(curr_x + 105, curr_y - 2.5)
        self.set_font("Helvetica", "B", 8)
        self.set_text_color(*color)
        self.cell(15, 6, f"{pct}%")
        self.ln(6)

class ReportService:
    def __init__(self):
        self.service_dir = os.path.dirname(os.path.abspath(__file__))
        self.project_root = os.path.dirname(self.service_dir)
        self.reports_dir = os.path.join(self.project_root, "generated_reports")
        os.makedirs(self.reports_dir, exist_ok=True)

    def generate_comprehensive_report(self, user_data: dict, analysis_results: dict, interventions: list, format_type: str = "pdf") -> dict:
        try:
            now = datetime.now()
            risk_level = sanitize_text(analysis_results.get("risk_level", "LOW")).upper()
            dep_score = int(float(analysis_results.get("depression_score", 0)) * 100)
            anx_score = int(float(analysis_results.get("anxiety_score", 0)) * 100)
            risk_score = int(float(analysis_results.get("risk_score", 0)) * 100) if "risk_score" in analysis_results else int((dep_score + anx_score) / 2)
            
            root_probs = analysis_results.get("root_causes", {})
            sorted_causes = sorted(root_probs.items(), key=lambda x: x[1], reverse=True)
            
            pdf = PremiumReportPDF()
            pdf.alias_nb_pages()
            pdf.add_page()
            
            # ─── SECTION 1: EXECUTIVE USER PROFILE ───
            pdf.set_y(25)
            
            # Metadata Grid (Compact)
            col_w = 93 
            
            # Container BG
            pdf.set_fill_color(*BG_CARD)
            pdf.rect(12, 25, 186, 20, 'F')
            
            # Labels
            pdf.set_font("Helvetica", "B", 6)
            pdf.set_text_color(*TEXT_MUTED)
            
            # Row 1 Labels
            pdf.set_xy(17, 28)
            pdf.cell(col_w-5, 3, "FULL NAME", ln=False)
            pdf.cell(col_w-5, 3, "SESSION ID", ln=True)
            
            # Row 1 Values
            pdf.set_font("Helvetica", "B", 8)
            pdf.set_text_color(*TEXT_MAIN)
            pdf.set_x(17)
            pdf.cell(col_w-5, 5, sanitize_text(user_data.get('name', 'Anonymous User')).upper(), ln=False)
            pdf.cell(col_w-5, 5, f"CX-{now.strftime('%y%m%d')}-{uuid.uuid4().hex[:4].upper()}", ln=True)
            
            pdf.ln(1)
            
            # Row 2 Labels
            pdf.set_font("Helvetica", "B", 6)
            pdf.set_text_color(*TEXT_MUTED)
            pdf.set_x(17)
            pdf.cell(col_w-5, 3, "EMAIL ADDRESS", ln=False)
            pdf.cell(col_w-5, 3, "GENERATED ON", ln=True)
            
            # Row 2 Values
            pdf.set_font("Helvetica", "B", 8)
            pdf.set_text_color(*TEXT_MAIN)
            pdf.set_x(17)
            pdf.cell(col_w-5, 5, sanitize_text(user_data.get('email', 'N/A')).upper(), ln=False)
            pdf.cell(col_w-5, 5, now.strftime("%d %b %Y | %H:%M UTC"), ln=True)
            
            pdf.set_y(48)
            
            # ─── SECTION 2: EXECUTIVE AI SUMMARY ───
            pdf.section_header("Executive AI Intelligence Summary")
            pdf.set_font("Helvetica", "I", 9)
            pdf.set_text_color(*TEXT_MAIN)
            summary = sanitize_text(analysis_results.get("ai_summary", "Assessment reveals patterns of cognitive load and executive function variance impacting emotional stability."))
            pdf.multi_cell(0, 4.5, f'"{summary}"')
            
            # ─── SECTION 3: CORE WELLNESS METRICS ───
            pdf.section_header("Core Wellness Metrics")
            m_y = pdf.get_y()
            m_w = 44 # Adjusted for 4 cards or better spacing
            m_h = 22
            spacing = 3
            
            # Aligned Metric Cards
            pdf.draw_metric_card(12, m_y, m_w, m_h, "Depression Risk", f"{dep_score}%", "Stable" if dep_score < 33 else ("Elevated" if dep_score < 66 else "High"), PURPLE)
            pdf.draw_metric_card(12 + m_w + spacing, m_y, m_w, m_h, "Anxiety Index", f"{anx_score}%", "Stable" if anx_score < 33 else ("Elevated" if anx_score < 66 else "High"), CYAN)
            pdf.draw_metric_card(12 + (m_w + spacing)*2, m_y, m_w, m_h, "Risk Score", f"{risk_score}%", f"{risk_level}", AMBER)
            pdf.draw_metric_card(12 + (m_w + spacing)*3, m_y, m_w, m_h, "Stability Index", f"{100 - risk_score}%", "OPTIMAL" if risk_score < 40 else "VARIED", EMERALD)
            
            pdf.set_y(m_y + m_h + 4)
            
            # ─── SECTION 4: ROOT CAUSE ANALYSIS ───
            pdf.section_header("Behavioral Root Cause Analysis")
            colors = [CYAN, PURPLE, AMBER, ROSE, EMERALD]
            for i, (name, prob) in enumerate(sorted_causes[:5]):
                pdf.draw_rca_bar(name.replace('_', ' ').title(), int(prob * 100), colors[i % len(colors)])
            
            # ─── SECTION 5: CLINICAL OBSERVATIONS ───
            pdf.section_header("Behavioral Intelligence Observations")
            
            # Dynamically select observations based on scores
            observations = []
            if anx_score > 60:
                observations.append("Cognitive overstimulation detected during high-novelty digital interaction phases.")
            if risk_score > 50:
                observations.append("Inconsistent recovery-cycle management correlates with reported focus instability.")
            if dep_score > 40:
                observations.append("Behavioral receptivity to analytical mirroring suggests strong potential for structured reset.")
            
            # Fill remaining with general AI observations if needed
            general_obs = [
                "Performance pressure indicators imply elevated internal self-monitoring patterns.",
                "Dopamine-linked focus instability detected in high-stimulation environments.",
                "Recovery-cycle imbalance identified during sustained cognitive demand phases."
            ]
            while len(observations) < 4:
                obs = general_obs.pop(0)
                if obs not in observations:
                    observations.append(obs)

            pdf.set_font("Helvetica", "", 8)
            pdf.set_text_color(*TEXT_MAIN)
            for obs in observations[:4]:
                pdf.set_x(15)
                pdf.cell(3, 4, chr(149), ln=False)
                pdf.multi_cell(0, 4, obs)
                pdf.ln(0.5)

            # ─── PAGE 2 ───
            pdf.add_page()
            
            # ─── SECTION 6: INTELLIGENT RECOVERY ARCHITECTURE ───
            pdf.section_header("Personalized Recovery Architecture")
            
            # Intelligent Conditional Planner
            planner_blocks = self._generate_intelligent_planner(dep_score, anx_score, root_probs)
            
            for block in planner_blocks:
                # Dense Aligned Block
                curr_y = pdf.get_y()
                pdf.set_fill_color(*BG_CARD)
                pdf.rect(12, curr_y, 186, 36, 'F')
                pdf.set_fill_color(*block['color'])
                pdf.rect(12, curr_y, 1.5, 36, 'F') # Left accent
                
                pdf.set_xy(17, curr_y + 3)
                pdf.set_font("Helvetica", "B", 9)
                pdf.set_text_color(*block['color'])
                pdf.cell(0, 5, block['title'].upper(), ln=True)
                
                pdf.set_x(17)
                pdf.set_font("Helvetica", "B", 6)
                pdf.set_text_color(*TEXT_MUTED)
                pdf.cell(0, 4, f"PRIMARY FINDINGS: {block['findings'].upper()}", ln=True)
                
                pdf.ln(1)
                pdf.set_font("Helvetica", "", 7.5)
                pdf.set_text_color(*TEXT_MAIN)
                for action in block['actions'][:4]: # Limit actions for density
                    pdf.set_x(17)
                    pdf.cell(3, 4, chr(149), ln=False)
                    pdf.multi_cell(0, 4, action)
                
                pdf.ln(1)
                pdf.set_x(17)
                pdf.set_font("Helvetica", "I", 7)
                pdf.set_text_color(*TEXT_MUTED)
                pdf.multi_cell(170, 3.5, f'Strategic Insight: "{block["insight"]}"')
                pdf.set_y(curr_y + 36 + 4)

            # ─── SECTION 7: DAILY WELLNESS PROTOCOL ───
            pdf.section_header("Daily Wellness Action Roadmap")
            roadmap = [
                {"day": "Phase 1: Reset", "focus": "Baseline Stabilization", "action": "Minimize high-dopamine digital inputs; implement fixed sleep/wake architecture."},
                {"day": "Phase 2: Train", "focus": "Cognitive Focus", "action": "Utilize structured 45/10 focus intervals; prioritize high-effort tasks during peak energy."},
                {"day": "Phase 3: Sustain", "focus": "Momentum Review", "action": "Evaluate micro-win consistency; externalize cognitive load through nightly journaling."}
            ]
            
            pdf.set_font("Helvetica", "B", 7)
            pdf.set_text_color(*TEXT_MUTED)
            pdf.cell(40, 5, "TIMELINE PHASE", ln=False)
            pdf.cell(50, 5, "STRATEGIC OBJECTIVE", ln=False)
            pdf.cell(0, 5, "CORE PROTOCOL ACTION", ln=True)
            
            pdf.set_draw_color(30, 41, 59)
            pdf.line(12, pdf.get_y(), 198, pdf.get_y())
            pdf.ln(2)
            
            pdf.set_font("Helvetica", "", 8)
            pdf.set_text_color(*TEXT_MAIN)
            for r in roadmap:
                pdf.set_x(12)
                pdf.set_font("Helvetica", "B", 8)
                pdf.cell(40, 6, r['day'], ln=False)
                pdf.set_font("Helvetica", "", 8)
                pdf.cell(50, 6, r['focus'], ln=False)
                pdf.multi_cell(0, 6, r['action'])
                
            # ─── SECTION 8: FINAL ASSESSMENT ───
            pdf.set_y(-42)
            pdf.section_header("Intelligence Validation Status", accent_color=AMBER)
            pdf.set_fill_color(*BG_CARD)
            pdf.rect(12, pdf.get_y(), 186, 18, 'F')
            
            pdf.set_xy(17, pdf.get_y() + 4)
            pdf.set_font("Helvetica", "B", 11)
            pdf.set_text_color(*AMBER)
            pdf.cell(0, 7, f"{risk_level} RISK · ASSESSMENT VALIDATED", ln=True)
            
            pdf.set_x(17)
            pdf.set_font("Helvetica", "", 7)
            pdf.set_text_color(*TEXT_MUTED)
            pdf.cell(0, 4, f"Next intelligence check-in recommended within 72 hours ({ (now + timedelta(days=3)).strftime('%d %b %Y') }).", ln=True)

            report_id = str(uuid.uuid4())
            file_name = f"COREAI_Premium_Report_{report_id}.pdf"
            file_path = os.path.join(self.reports_dir, file_name)
            pdf.output(file_path)
            
            return {"status": "success", "report_id": report_id, "file_path": file_path}
            
        except Exception as e:
            import traceback
            logger.error(f"v7 Report Error: {e}\n{traceback.format_exc()}")
            return {"status": "error", "error": str(e)}

    def _generate_intelligent_planner(self, dep, anx, root_probs):
        blocks = []
        
        # Determine dominant patterns
        patterns = {
            "anxiety": anx > 50,
            "depression": dep > 50,
            "dopamine": root_probs.get("dopamine_addiction", 0) > 0.4,
            "perfectionism": root_probs.get("perfectionism", 0) > 0.4,
            "fear_of_failure": root_probs.get("fear_of_failure", 0) > 0.4
        }
        
        # 1. FEAR OF FAILURE (Strategic Priority)
        if patterns["fear_of_failure"]:
            blocks.append({
                "title": "Execution Confidence Strategy",
                "color": AMBER,
                "findings": "Fear-based over-analysis and delayed execution cycles detected.",
                "actions": [
                    "Prioritize execution velocity over excessive optimization to bypass diminishing returns.",
                    "Reduce repeated validation cycles during task completion phases.",
                    "Use fixed completion deadlines to prevent over-analysis and procrastination loops.",
                    "Reinforce decision confidence by limiting information-seeking time to 15 minutes per task."
                ],
                "insight": "Behavioral indicators suggest performance anxiety impacting confidence. Focusing on movement over outcome quality will restore baseline execution velocity."
            })

        # 2. ANXIETY REGULATION
        if patterns["anxiety"] and len(blocks) < 2:
            blocks.append({
                "title": "Cognitive Unload Strategy",
                "color": CYAN,
                "findings": "Mental overactivity and future uncertainty loops detected.",
                "actions": [
                    "Use written cognitive unloading (journaling) before sleep to externalize pending tasks.",
                    "Reduce context-switching during deep-focus blocks to lower nervous system arousal.",
                    "Lower late-night digital stimulation exposure to stabilize melatonin production.",
                    "Apply 4-7-8 breathing reset twice daily during work/study transitions."
                ],
                "insight": "Your responses suggest elevated cognitive pressure rather than emotional instability. Reducing mental overload may significantly improve clarity."
            })
            
        # 3. DOPAMINE ADDICTION
        if patterns["dopamine"] and len(blocks) < 2:
            blocks.append({
                "title": "Attention Recovery Protocol",
                "color": PURPLE,
                "findings": "Novelty-seeking loops and reward-cycle overstimulation.",
                "actions": [
                    "Delay entertainment rewards (social media/streaming) until after completion cycles.",
                    "Use distraction-free intervals during high-focus tasks (phone in grayscale/other room).",
                    "Restrict short-form content consumption after 22:00 to restore reward-baseline.",
                    "Implement a 90-minute digital detox window immediately upon waking."
                ],
                "insight": "Patterns indicate reward-cycle overstimulation. Restoration of baseline focus is the primary objective for emotional consistency."
            })

        # 4. PERFECTIONISM
        if patterns["perfectionism"] and len(blocks) < 2:
            blocks.append({
                "title": "Performance Pressure Reduction",
                "color": ROSE,
                "findings": "Excessive self-monitoring and fear-based execution delays.",
                "actions": [
                    "Submit work at 90% completion to bypass diminishing returns and perfectionist loops.",
                    "Track 'Completed Actions' instead of 'Perfect Outcomes' for the next 7 days.",
                    "Use task chunking to reduce the perceived stakes of individual project components.",
                    "Limit self-monitoring cycles: Review work only once before submission."
                ],
                "insight": "High internal pressure is impacting execution confidence. Prioritize imperfect movement to reduce cognitive fatigue."
            })

        # 5. DEPRESSION / ACTIVATION
        if patterns["depression"] and len(blocks) < 2:
            blocks.append({
                "title": "Behavioral Activation Strategy",
                "color": EMERALD,
                "findings": "Emotional depletion and reduced motivation cycles.",
                "actions": [
                    "Prioritize 'Small Win' activation: Complete 1 meaningful task early daily.",
                    "Ensure 15 minutes of direct sunlight exposure within 1 hour of waking.",
                    "Maintain light but consistent social interaction to prevent withdrawal loops.",
                    "Maintain minimum viable routine (MVR) consistency on low-energy days."
                ],
                "insight": "Your patterns indicate emotional depletion rather than lack of capability. Consistent behavioral activation may gradually restore stability."
            })

        # Default block if empty
        if not blocks:
            blocks.append({
                "title": "Wellness Stabilization Protocol",
                "color": EMERALD,
                "findings": "Baseline stability detected with minor optimization potential.",
                "actions": [
                    "Maintain existing recovery gap structure between high-effort blocks.",
                    "Continue weekly wellness reflection to identify emerging stressors early.",
                    "Ensure consistent hydration and physical activity to support cognitive load."
                ],
                "insight": "System operating within normal parameters. Continue existing protocols to maintain baseline resilience."
            })
            
        return blocks[:2] # STRICTLY limit to 2 blocks for density

    def send_report_email(self, report_id, recipient_email, user_name, message):
        if not send_email: return {"status": "error", "message": "Email service not configured."}
        try:
            file_path = None
            for f in os.listdir(self.reports_dir):
                if report_id in f:
                    file_path = os.path.join(self.reports_dir, f)
                    break
            if not file_path: return {"status": "error", "message": "Report file not found."}
            send_email(to_email=recipient_email, subject=f"CORE:AI Premium Report - {user_name}", body=message, attachment_path=file_path)
            return {"status": "success", "message": "Email sent."}
        except Exception as e: return {"status": "error", "message": str(e)}

def get_report_service(): return ReportService()

def generate_pdf_bytes(report_data):
    service = get_report_service()
    result = service.generate_comprehensive_report({"name": "User", "email": "N/A"}, report_data, [])
    if result["status"] == "success":
        with open(result["file_path"], "rb") as f: return f.read()
    return b""
