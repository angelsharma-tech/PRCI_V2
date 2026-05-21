# **PRCI : Procrastination Root Cause Identifier System**

**Overview**

PRCI v2 is an AI-powered mental health analysis system that detects depression and anxiety, identifies root causes of procrastination, and provides personalized recommendations.
The system integrates machine learning, deep learning, and an interactive dashboard for real-time analysis.

**Features**

1. Dual-Head BERT Model : Predicts Depression and Anxiety scores
2. Root Cause Detection : TF-IDF + Logistic Regression (multi-label) : DETECTS -> perfectionism, fear_of_failure, lack_of_interest, environment_distraction, dopamine_addiction
3. Risk Engine : Calculates overall risk score -> Outputs: LOW / MODERATE / HIGH
4. Interactive Dashboard: Built with Streamlit, Real-time analysis + charts
5. Trend Tracking: Sliding window analysis of user history
6. PDF Report Generator: Downloadable personalized report
7. Email Integration: Send report directly to user inbox

**System Architecture**

User Input → Preprocessing → BERT Model → Root Cause Model → Risk Engine → Tracker → Planner → Output (UI + PDF)

**Project Structure**

PRCI_v2/
│
├── app_upgrade.py
├── requirements.txt
│
├── upgrade_pipeline/
│   ├── preprocess.py
│   ├── root_cause_model.py
│   ├── risk_engine.py
│   ├── tracker.py
│   ├── explainability.py
│   └── report_generator.py
│
├── legacy_model_pipeline/
│   ├── train_two_heads.py
│   ├── model_infer.py
│   └── outputs/
│       └── twohead/
│           └── best.pt
│
├── phase_3_data/
│   └── raw/

**Setup & Run**

* Clone repo

git clone https://github.com/your-username/PRCI_v2.git
cd PRCI_v2

* Install dependencies
  
pip install -r requirements.txt

* Run app
  
streamlit run app_upgrade.py

**Environment Variables**

PRCI_TWOHEAD_CKPT=path_to_best.pt
SENDER_EMAIL=your_email@gmail.com
APP_PASSWORD=your_app_password

**Key Highlights**
1. Modular architecture (baseline + upgrade pipeline)
2. Real-time inference with BERT
3. Explainable AI (feature importance)
4. End-to-end pipeline: detection → analysis → action

**Future Improvements**
1. Cloud deployment optimization
2. Real-time monitoring dashboard
