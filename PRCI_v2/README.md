# PRCI v2.0 – Adaptive AI-Based Procrastination Prediction & Personalized Intervention System

## 🚨 CRITICAL DEPLOYMENT NOTES

### Model Version Compatibility
- **scikit-learn**: Must be exactly `1.6.1` (models trained on this version)
- **joblib**: Compatible version for model loading
- **Action**: Run `pip install -r requirements.txt` before deployment

### Current Implementation Status
- **Root Cause Analysis**: ✅ Fully operational (TF-IDF + Logistic Regression)
- **Emotional Classification**: ⏳ Placeholder (returns 0.0 baseline values)
- **Risk Assessment**: ✅ Functional through behavioral analysis
- **Academic Note**: RiskEngine primarily leverages behavioral root causes for meaningful assessment

## Project Overview

**Semester-8 Major Project**  
Bachelor of Technology/Computer Science Engineering  
Academic Year 2025-2026

PRCI v2.0 represents an advanced artificial intelligence system designed to predict procrastination tendencies in university students and deliver personalized intervention strategies. The system leverages machine learning algorithms to analyze behavioral patterns and provide proactive support for academic success.

## Development Methodology

This project follows a **phase-wise Software Development Life Cycle (SDLC)** approach, ensuring systematic development and comprehensive documentation throughout the academic semester.

## Project Structure

```
PRCI_v2/
│
├── phase_1_requirements/        ✅ COMPLETED
│   ├── project_overview.md
│   ├── problem_statement.md
│   ├── motivation_and_gap_analysis.md
│   ├── objectives_and_deliverables.md
│   ├── scope_and_boundaries.md
│   ├── assumptions_and_constraints.md
│   └── ethical_and_privacy_considerations.md
│
├── phase_2_architecture/         🔄 NEXT PHASE
├── phase_3_data/                 ⏳ PLANNED
├── phase_4_models/               ⏳ PLANNED
├── phase_5_risk_engine/          ⏳ PLANNED
├── phase_6_intervention/         ⏳ PLANNED
├── phase_7_personalization/      ⏳ PLANNED
├── phase_8_dashboard/            ⏳ PLANNED
├── phase_9_evaluation/           ⏳ PLANNED
└── phase_10_documentation/       ⏳ PLANNED
```

## Current Status

**Currently completed: Phase-2 (System Architecture & High-Level Design)**

Phase-1 has established the complete conceptual foundation for PRCI v2.0, including:

- ✅ Comprehensive project overview and system vision
- ✅ Detailed problem statement with clear boundaries
- ✅ Motivation analysis and gap identification
- ✅ Primary and secondary objectives definition
- ✅ System scope and boundary specifications
- ✅ Assumptions and constraints documentation
- ✅ Ethical and privacy framework establishment

Phase-2 has established the complete technical architecture and code scaffolding:

- ✅ System overview with layer-by-layer data flow
- ✅ ASCII architecture diagram showing closed-loop design
- ✅ Detailed module responsibilities and interfaces
- ✅ Clean Python code scaffolding with docstrings and TODOs
- ✅ Detection layer interface with multiple engine types
- ✅ Risk engine with temporal aggregation and scoring
- ✅ Intervention engine with ethical filtering
- ✅ Personalization engine with feedback learning

## System Vision

> *PRCI v2.0 aims to revolutionize procrastination management through an intelligent, predictive, and personalized AI system that anticipates behavioral challenges and delivers timely, contextually relevant interventions, thereby fostering sustainable productivity enhancement and academic success for university students while maintaining strict ethical boundaries and user autonomy.*

## Key Features

- **Predictive Analytics**: Advanced ML models for procrastination tendency prediction
- **Personalized Interventions**: Adaptive strategies tailored to individual user profiles
- **Closed-Loop Learning**: Continuous system improvement through user feedback
- **Ethical Framework**: Strict adherence to privacy and ethical guidelines
- **Academic Focus**: Specialized for university student procrastination management

## Ethical Boundaries

**Important**: This system does not perform medical diagnosis; it provides AI-assisted behavioral support. PRCI v2.0 operates strictly within academic productivity enhancement boundaries and maintains user autonomy as the highest priority.

## Next Steps

**Project Complete** ✅

All 10 phases of PRCI v2.0 have been successfully completed with comprehensive documentation, ethical compliance validation, and academic reporting. The system is ready for final evaluation and viva presentation.

## Project Structure Status

```
PRCI_v2/
│
├── phase_1_requirements/        ✅ COMPLETED
│   ├── project_overview.md
│   ├── problem_statement.md
│   ├── motivation_and_gap_analysis.md
│   ├── objectives_and_deliverables.md
│   ├── scope_and_boundaries.md
│   ├── assumptions_and_constraints.md
│   └── ethical_and_privacy_considerations.md
│
├── phase_2_architecture/         ✅ COMPLETED
│   ├── system_overview.md
│   ├── architecture_diagram.txt
│   └── module_responsibilities.md
│
├── phase_3_data/                 ✅ COMPLETED
│   ├── raw/
│   ├── processed/
│   ├── splits/
│   ├── data_description.md
│   ├── preprocessing_pipeline.md
│   ├── feature_overview.md
│   ├── text_cleaner.py
│   ├── dataset_builder.py
│   └── data_splitter.py
├── phase_4_models/               ✅ COMPLETED
│   ├── detection_interface.py
│   ├── modeling_strategy.md
│   ├── feature_representation.md
│   ├── feature_extractor.py
│   ├── emotion_model.py
│   ├── root_cause_model.py
│   ├── train_models.py
│   ├── detection_engine_impl.py
│   └── evaluation_notes.md
├── phase_5_risk_engine/          ✅ COMPLETED
│   ├── risk_engine.py
│   ├── risk_modeling_strategy.md
│   ├── risk_features.md
│   ├── procrastination_risk_engine.py
│   ├── temporal_utils.py
│   └── risk_evaluation_notes.md
├── phase_6_intervention/         ✅ COMPLETED
│   ├── intervention_engine.py
│   ├── intervention_design_strategy.md
│   ├── intervention_types.md
│   ├── prompt_templates.py
│   └── intervention_safety_notes.md
├── phase_7_personalization/      ✅ COMPLETED
│   ├── personalization_engine.py
│   ├── personalization_strategy.md
│   ├── feedback_types.md
│   └── personalization_safety_notes.md
├── phase_8_ui/                  ✅ COMPLETED
│   ├── console_app.py
│   ├── ui_flow_overview.md
│   ├── interaction_guidelines.md
│   └── disclaimer.md
├── phase_9_evaluation/           ✅ COMPLETED
│   ├── evaluation_strategy.md
│   ├── test_cases.md
│   ├── metrics_definition.md
│   ├── result_analysis.md
│   ├── limitations_and_threats.md
│   └── system_validation.py
└── phase_10_final_report/       ✅ COMPLETED
    ├── abstract.md
    ├── chapter_mapping.md
    ├── conclusion.md
    ├── future_work.md
    ├── viva_questions.md
    └── project_summary.md
```

## Project Team

- **Project Guide**: [Faculty Advisor Name]
- **Development Team**: [Student Names]
- **Academic Institution**: [University Name]
- **Department**: Computer Science Engineering

## Contact Information

For project inquiries and collaboration opportunities, please contact the project team through the university department.

---

**Last Updated**: January 2026  
**Phase**: 10 of 10 - Final Report Compilation & Viva Preparation (Completed)  
**Status**: Project Complete - Ready for Evaluation
