"""
AVCS STRUCTURAL INTEGRITY MODULE (SIM) — LITE
Diagnostic Instrument for Decision Architecture

Version: 1.4
Companion Documents: Charter v1.1, CORE v2.1, Code of Ethics v1.1,
                    Code of Practice v1.1, SIM v1.1
License: CC BY-NC-ND 4.0

Changelog:
v1.4:
- Professional PDF report:
  * AVCS logo in header
  * Radar chart (matplotlib)
  * Executive Summary
  * Structural Vulnerability Map
  * Structural Risk Forecast
  * Priority Reinforcement Plan
  * Evidence Appendix
  * Report ID (unique)
  * Page numbers (footer on each page)
  * Color-coded score
  * AVCS quote (CORE v2.1)
  * Links to full documentation
v1.3:
- Migrated from fpdf to fpdf2 (Unicode-safe)
- All em dashes replaced with hyphens
- pdf.output() used directly
- Radar chart optimized (height=350, no toolbar)
v1.2:
- 15 → 20 questions
- 6 reformulated, 5 new
- Sidebar: Step X of 5
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from fpdf import FPDF
import base64
import uuid
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from datetime import datetime

# ------------------------------
# Конфигурация страницы
# ------------------------------
st.set_page_config(
    page_title="AVCS Structural Integrity Module",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ------------------------------
# Стили CSS
# ------------------------------
st.markdown("""
<style>
    .stApp { background-color: #f8f9fa; }
    .main-header {
        text-align: center;
        padding: 20px 0;
        background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 20px;
    }
    .main-header h1 { font-size: 32px; margin-bottom: 10px; }
    .main-header p { font-size: 18px; }
    .pillar-card {
        background-color: white;
        color: #000000;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 15px;
        border-left: 4px solid #1e3a8a;
    }
    .pillar-card h2 { color: #1e3a8a; margin-top: 0; margin-bottom: 10px; }
    .pillar-card p { color: #4b5563; margin-bottom: 0; }
    .score-box {
        background-color: #1e3a8a;
        color: white;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
        font-size: 48px;
        font-weight: bold;
        margin: 15px 0;
    }
    .stButton button {
        background-color: #1e3a8a;
        color: white;
        font-weight: bold;
        border-radius: 5px;
        padding: 8px 20px;
        border: none;
    }
    .stButton button:hover { background-color: #3b82f6; }
    .stRadio label { color: #000000 !important; font-size: 16px; }
    .stRadio div { color: #000000 !important; }
    .stMarkdown { color: #000000; }
    .info-box {
        background-color: #e6f7ff;
        padding: 15px;
        border-radius: 10px;
        border-left: 4px solid #1e3a8a;
        margin: 10px 0;
    }
    .warning-box {
        background-color: #fee2e2;
        padding: 15px;
        border-radius: 10px;
        border-left: 4px solid #dc2626;
        margin: 10px 0;
    }
    .benchmark-box {
        background-color: #f0f9ff;
        padding: 15px;
        border-radius: 10px;
        border-left: 4px solid #0ea5e9;
        margin: 10px 0;
    }
    .welcome-box {
        background-color: white;
        padding: 25px;
        border-radius: 10px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

# ------------------------------
# Инициализация состояния сессии
# ------------------------------
defaults = {
    'welcome_shown': False,
    'step': 1,
    'scores': {
        'trigger_clarity': 0,
        'decision_ownership': 0,
        'protected_intervention': 0,
        'override_transparency': 0,
        'drift_detection': 0
    },
    'answers': {},
    'justifications': {
        'trigger_clarity': '',
        'decision_ownership': '',
        'protected_intervention': '',
        'override_transparency': '',
        'drift_detection': ''
    }
}
for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# ------------------------------
# Функции для расчёта скоров
# ------------------------------
def calculate_trigger_score(answers):
    score = 0
    if answers.get('q1_1') == "Mandatory and enforced": score += 2
    elif answers.get('q1_1') == "Defined but discretionary": score += 1

    if answers.get('q1_2') == "Yes, systematically tracked": score += 2
    elif answers.get('q1_2') == "Sometimes noticed": score += 1

    if answers.get('q1_3') == "Automatic (mandatory)": score += 1
    return min(score, 5)


def calculate_ownership_score(answers):
    score = 0
    if answers.get('q2_1') == "Yes, singular owner defined": score += 2
    elif answers.get('q2_1') == "Shared but clear": score += 1

    if answers.get('q2_2') == "Yes, always present": score += 2
    elif answers.get('q2_2') == "Usually present": score += 1

    if answers.get('q2_3') == "Yes, always": score += 1
    return min(score, 5)


def calculate_intervention_score(answers):
    score = 0
    if answers.get('q3_1') == "Yes, formally codified and protected": score += 2
    elif answers.get('q3_1') == "Yes, but informally": score += 1

    if answers.get('q3_2') == "Always supported": score += 2
    elif answers.get('q3_2') == "Usually supported": score += 1

    if answers.get('q3_3') == "No, never": score += 1

    if answers.get('q3_4') == "Yes, formally codified and protected": score += 2
    elif answers.get('q3_4') == "Yes, but informal": score += 1

    if answers.get('q3_5') == "Yes, evidence exists (records, logs, procedures)": score += 1

    return min(score, 5)


def calculate_override_score(answers):
    score = 0
    if answers.get('q4_1') == "Yes, always": score += 2
    elif answers.get('q4_1') == "Sometimes": score += 1

    if answers.get('q4_2') == "Yes, always": score += 2
    elif answers.get('q4_2') == "Sometimes": score += 1

    if answers.get('q4_3') == "Yes, regularly": score += 1

    if answers.get('q4_4') == "Yes, always": score += 1

    if answers.get('q4_5') == "Yes, evidence exists": score += 1

    return min(score, 5)


def calculate_drift_score(answers):
    score = 0
    if answers.get('q5_1') == "Yes, systematically": score += 2
    elif answers.get('q5_1') == "Sometimes": score += 1

    if answers.get('q5_2') == "Yes, regularly": score += 2
    elif answers.get('q5_2') == "Occasionally": score += 1

    if answers.get('q5_3') == "Yes, actively": score += 1

    if answers.get('q5_4') == "Yes, evidence exists": score += 1

    return min(score, 5)


# ------------------------------
# Функции для обоснования скоров
# ------------------------------
def justify_trigger(score, answers):
    if score >= 4:
        return "Triggers are mandatory and documented. Deviations reliably activate escalation."
    elif score >= 3:
        return "Triggers are defined and mostly applied, but not consistently mandatory."
    elif score >= 2:
        return "Triggers are defined but discretionary - escalation depends on interpretation."
    elif score >= 1:
        return "Triggers are informal or inconsistent. Deviations often pass unnoticed."
    else:
        return "No defined escalation triggers. System relies entirely on individual judgment."


def justify_ownership(score, answers):
    if score >= 4:
        return "Singular, traceable ownership is documented and operationally present."
    elif score >= 3:
        return "Owner is defined and generally respected, though authority may be diluted."
    elif score >= 2:
        return "Owner is defined but authority is diluted in practice."
    elif score >= 1:
        return "Owner is named but not operationally present in real time."
    else:
        return "Responsibility is collective or unclear. No single accountable owner."


def justify_intervention(score, answers):
    if score >= 4:
        return "Intervention is formally protected and reviewed positively. Operator fitness is structurally supported."
    elif score >= 3:
        return "Intervention is formally protected, but may carry friction."
    elif score >= 2:
        return "Intervention is allowed but carries friction. Stopping may affect metrics."
    elif score >= 1:
        return "Intervention is allowed but informally punished."
    else:
        return "Intervention is culturally discouraged. Stopping carries personal risk."


def justify_override(score, answers):
    if score >= 4:
        return "Overrides are logged, traceable, audited. Residual risk is assigned to named owner."
    elif score >= 3:
        return "Overrides are logged with a named owner, but not always audited."
    elif score >= 2:
        return "Overrides are logged but incomplete. Traceability is partial."
    elif score >= 1:
        return "Overrides occur but are not consistently documented."
    else:
        return "Informal override is common. Deviations leave no trace."


def justify_drift(score, answers):
    if score >= 4:
        return "Drift is actively monitored and structurally countered. Evidence of past drift detection exists."
    elif score >= 3:
        return "Deviations are tracked and periodically reviewed."
    elif score >= 2:
        return "Deviations are logged but not analyzed."
    elif score >= 1:
        return "Minor deviations are noted but not tracked."
    else:
        return "No drift visibility. Normalization of deviation goes undetected."


# ------------------------------
# Радар-график (Plotly, для UI)
# ------------------------------
def create_radar_chart(scores):
    categories = ['Trigger Clarity', 'Decision Ownership', 'Protected Intervention',
                  'Override Transparency', 'Drift Detection']
    values = [
        scores['trigger_clarity'],
        scores['decision_ownership'],
        scores['protected_intervention'],
        scores['override_transparency'],
        scores['drift_detection']
    ]

    fig = go.Figure(data=go.Scatterpolar(
        r=values + [values[0]],
        theta=categories + [categories[0]],
        fill='toself',
        line_color='#1e3a8a',
        fillcolor='rgba(30, 58, 138, 0.3)'
    ))

    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 5])),
        showlegend=False,
        height=350,
        margin=dict(l=60, r=60, t=20, b=20)
    )
    return fig


# ------------------------------
# PDF class (footer on each page)
# ------------------------------
class AVCSFPDF(FPDF):
    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(138, 138, 138)
        self.cell(0, 10,
                  f'SIM Lite v1.4 | Page {self.page_no()} | 2026 Yeruslan Chihachyov',
                  0, 0, 'C')


# ------------------------------
# Helpers for PDF
# ------------------------------
def generate_report_id():
    now = datetime.now()
    return f"SIM-{now.strftime('%Y%m%d-%H%M')}-{uuid.uuid4().hex[:5].upper()}"


def generate_executive_summary(total_score, scores, justifications):
    if total_score <= 10:
        cls = "HIGH STRUCTURAL VULNERABILITY"
        return (f"This system demonstrates {cls} ({total_score}/25). "
                f"Multiple conditions of control fail. "
                f"The system may appear stable under normal conditions, "
                f"but is structurally unprepared for pressure.")
    elif total_score <= 17:
        cls = "CONDITIONAL STABILITY"
        weak = [k.replace('_', ' ').title() for k, v in scores.items() if v <= 2]
        summary = (f"This system demonstrates {cls} ({total_score}/25). "
                   f"Some pillars are structurally sound, but critical weaknesses exist. ")
        if weak:
            summary += f"Priority areas: {', '.join(weak)}."
        return summary
    elif total_score <= 22:
        cls = "STRUCTURALLY CONTROLLED"
        return (f"This system demonstrates {cls} ({total_score}/25). "
                f"All conditions of control are satisfied. "
                f"Targeted improvements will strengthen further.")
    else:
        cls = "ARCHITECTURALLY RESILIENT"
        return (f"This system demonstrates {cls} ({total_score}/25). "
                f"All conditions of control are satisfied and verified. "
                f"The system is designed to protect good decisions under pressure.")


def create_radar_image(scores, filename="radar_temp.png"):
    categories = ['Trigger', 'Ownership', 'Intervention', 'Override', 'Drift']
    values = [
        scores['trigger_clarity'],
        scores['decision_ownership'],
        scores['protected_intervention'],
        scores['override_transparency'],
        scores['drift_detection']
    ]
    values += values[:1]

    angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=False).tolist()
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
    ax.plot(angles, values, 'o-', linewidth=2, color='#1e3a8a')
    ax.fill(angles, values, alpha=0.25, color='#1e3a8a')
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories, fontsize=11)
    ax.set_ylim(0, 5)
    ax.set_yticks([1, 2, 3, 4, 5])
    ax.set_yticklabels(['1', '2', '3', '4', '5'], fontsize=9, color='#666666')
    ax.grid(True, color='#cccccc')
    ax.set_facecolor('#f8f9fa')

    plt.tight_layout()
    plt.savefig(filename, dpi=100, bbox_inches='tight', facecolor='white')
    plt.close()
    return filename


# ------------------------------
# PDF report (v1.4.1 — fpdf2 safe)
# ------------------------------
def create_pdf(scores, total_score, justifications):
    pdf = AVCSFPDF()
    pdf.set_margins(10, 10, 10)
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    report_id = generate_report_id()

    # --- LOGO ---
    try:
        pdf.image("logo.png", x=170, y=8, w=25)
    except:
        pass

    # --- HEADER ---
    pdf.set_x(10)
    pdf.set_font('Helvetica', 'B', 20)
    pdf.set_text_color(30, 58, 138)
    pdf.cell(0, 12, 'AVCS Structural Integrity Report', 0, 1, 'C')
    pdf.set_x(10)
    pdf.set_font('Helvetica', 'I', 10)
    pdf.set_text_color(75, 85, 99)
    pdf.cell(0, 6, 'SIM Lite v1.4 - Adaptive Vector Control System', 0, 1, 'C')
    pdf.ln(4)

    # --- METADATA ---
    pdf.set_x(10)
    pdf.set_font('Helvetica', '', 9)
    pdf.set_text_color(75, 85, 99)
    pdf.cell(0, 5, f'Report ID: {report_id}', 0, 1)
    pdf.set_x(10)
    pdf.cell(0, 5, f'Generated: {datetime.now().strftime("%Y-%m-%d %H:%M")}', 0, 1)
    pdf.set_x(10)
    pdf.cell(0, 5, 'Assessed by: SIM Lite v1.4 (automated diagnostic)', 0, 1)
    pdf.ln(6)

    # --- SCORE ---
    if total_score <= 10:
        classification = "HIGH STRUCTURAL VULNERABILITY"
        color = (220, 38, 38)
    elif total_score <= 17:
        classification = "CONDITIONAL STABILITY"
        color = (245, 158, 11)
    elif total_score <= 22:
        classification = "STRUCTURALLY CONTROLLED"
        color = (59, 130, 246)
    else:
        classification = "ARCHITECTURALLY RESILIENT"
        color = (16, 185, 129)

    pdf.set_x(10)
    pdf.set_text_color(*color)
    pdf.set_font('Helvetica', 'B', 28)
    pdf.cell(0, 15, f'{total_score} / 25', 0, 1, 'C')
    pdf.set_x(10)
    pdf.set_font('Helvetica', 'B', 14)
    pdf.cell(0, 10, classification, 0, 1, 'C')
    pdf.set_text_color(0, 0, 0)
    pdf.ln(6)

    # --- EXECUTIVE SUMMARY ---
    pdf.set_x(10)
    pdf.set_font('Helvetica', 'B', 13)
    pdf.set_text_color(30, 58, 138)
    pdf.cell(0, 10, 'Executive Summary', 0, 1)
    pdf.set_x(10)
    pdf.set_font('Helvetica', '', 10)
    pdf.set_text_color(31, 41, 55)
    summary = generate_executive_summary(total_score, scores, justifications)
    pdf.multi_cell(0, 6, summary)
    pdf.ln(6)

    # --- RADAR CHART ---
    pdf.set_x(10)
    pdf.set_font('Helvetica', 'B', 13)
    pdf.set_text_color(30, 58, 138)
    pdf.cell(0, 10, 'Structural Profile', 0, 1)
    try:
        radar_file = create_radar_image(scores)
        chart_y = pdf.get_y()
        pdf.image(radar_file, x=60, y=chart_y, w=90)
        pdf.set_y(chart_y + 95)
    except Exception as e:
        pdf.set_x(10)
        pdf.set_font('Helvetica', 'I', 9)
        pdf.set_text_color(138, 138, 138)
        pdf.cell(0, 6, f'(Radar chart unavailable)', 0, 1)
    pdf.ln(4)

    # --- PILLAR SCORES ---
    pdf.set_x(10)
    pdf.set_font('Helvetica', 'B', 13)
    pdf.set_text_color(30, 58, 138)
    pdf.cell(0, 10, 'Pillar Scores and Justifications', 0, 1)
    pdf.ln(2)

    pillars = [
        ('Trigger Clarity', scores['trigger_clarity'], justifications['trigger_clarity']),
        ('Decision Ownership', scores['decision_ownership'], justifications['decision_ownership']),
        ('Protected Intervention', scores['protected_intervention'], justifications['protected_intervention']),
        ('Override Transparency', scores['override_transparency'], justifications['override_transparency']),
        ('Drift Detection', scores['drift_detection'], justifications['drift_detection'])
    ]

    for name, score, just in pillars:
        pdf.set_x(10)
        pdf.set_font('Helvetica', 'B', 11)
        pdf.set_text_color(30, 58, 138)
        pdf.cell(0, 7, f'{name}: {score}/5', 0, 1)
        pdf.set_x(10)
        pdf.set_font('Helvetica', '', 10)
        pdf.set_text_color(31, 41, 55)
        pdf.multi_cell(0, 5, just)
        pdf.ln(2)

    # --- VULNERABILITY MAP ---
    pdf.add_page()
    pdf.set_x(10)
    pdf.set_font('Helvetica', 'B', 13)
    pdf.set_text_color(30, 58, 138)
    pdf.cell(0, 10, 'Structural Vulnerability Map', 0, 1)
    pdf.ln(2)

    weak_pillars = [
        (name, score, just)
        for name, score, just in pillars
        if score <= 3
    ]

    if not weak_pillars:
        pdf.set_x(10)
        pdf.set_font('Helvetica', 'I', 10)
        pdf.set_text_color(31, 41, 55)
        pdf.multi_cell(0, 6, "No critical vulnerabilities identified. All pillars score above 3/5.")
    else:
        for i, (name, score, just) in enumerate(weak_pillars, 1):
            pdf.set_x(10)
            pdf.set_font('Helvetica', 'B', 11)
            pdf.set_text_color(220, 38, 38)
            pdf.cell(0, 7, f'Priority {i}: {name} ({score}/5)', 0, 1)
            pdf.ln(1)
            pdf.set_x(10)
            pdf.set_font('Helvetica', '', 10)
            pdf.set_text_color(31, 41, 55)
            pdf.multi_cell(0, 5, just)
            pdf.ln(3)

    # --- RISK FORECAST ---
    pdf.ln(4)
    pdf.set_x(10)
    pdf.set_font('Helvetica', 'B', 13)
    pdf.set_text_color(30, 58, 138)
    pdf.cell(0, 10, 'Structural Risk Forecast', 0, 1)
    pdf.set_x(10)
    pdf.set_font('Helvetica', '', 10)
    pdf.set_text_color(31, 41, 55)
    pdf.multi_cell(0, 6,
                   "If no corrective action is taken, the system is most likely to fail through:\n\n"
                   "1. Escalation delay - signals visible but not acted upon.\n"
                   "2. Override normalization - deviations logged but not audited.\n"
                   "3. Ownership diffusion - responsibility diluted under pressure.")
    pdf.ln(4)
    pdf.set_x(10)
    pdf.set_font('Helvetica', 'I', 10)
    pdf.multi_cell(0, 6, 'Not "if an incident happens." But how.')
    pdf.ln(4)

    # --- REINFORCEMENT PLAN ---
    pdf.set_x(10)
    pdf.set_font('Helvetica', 'B', 13)
    pdf.set_text_color(30, 58, 138)
    pdf.cell(0, 10, 'Priority Reinforcement Plan', 0, 1)
    pdf.set_x(10)
    pdf.set_font('Helvetica', '', 10)
    pdf.set_text_color(31, 41, 55)

    if weak_pillars:
        for i, (name, score, just) in enumerate(weak_pillars[:3], 1):
            pdf.set_x(10)
            pdf.set_font('Helvetica', 'B', 10)
            pdf.cell(0, 6, f'{i}. {name}', 0, 1)
            pdf.set_x(10)
            pdf.set_font('Helvetica', '', 10)
            pdf.multi_cell(0, 5, f'   Objective: Address weakness (current score: {score}/5).')
            pdf.set_x(10)
            pdf.multi_cell(0, 5, f'   Timeline: {30 * i} days.')
            pdf.ln(2)
    else:
        pdf.set_x(10)
        pdf.multi_cell(0, 6, 'No priority actions required. Maintain current structural integrity.')

    # --- EVIDENCE APPENDIX ---
    pdf.add_page()
    pdf.set_x(10)
    pdf.set_font('Helvetica', 'B', 13)
    pdf.set_text_color(30, 58, 138)
    pdf.cell(0, 10, 'Evidence Appendix', 0, 1)
    pdf.set_x(10)
    pdf.set_font('Helvetica', 'I', 9)
    pdf.set_text_color(138, 138, 138)
    pdf.multi_cell(0, 5,
                   'Evidence is self-reported through the SIM Lite diagnostic. '
                   'A full SIM audit is required for evidence verification.')
    pdf.ln(4)

    for name, score, just in pillars:
        pdf.set_x(10)
        pdf.set_font('Helvetica', 'B', 11)
        pdf.set_text_color(30, 58, 138)
        pdf.cell(0, 7, f'{name}', 0, 1)
        pdf.set_x(10)
        pdf.set_font('Helvetica', '', 10)
        pdf.set_text_color(31, 41, 55)
        pdf.multi_cell(0, 5,
                       f'Score: {score}/5\n'
                       f'Evidence: Self-reported\n'
                       f'Full audit recommended for evidence verification.')
        pdf.ln(2)

    # --- BENCHMARKS ---
    pdf.ln(4)
    pdf.set_x(10)
    pdf.set_font('Helvetica', 'B', 13)
    pdf.set_text_color(30, 58, 138)
    pdf.cell(0, 10, 'Benchmarks', 0, 1)
    pdf.set_x(10)
    pdf.set_font('Helvetica', '', 10)
    pdf.set_text_color(31, 41, 55)
    pdf.cell(0, 6, 'Deepwater Horizon: 3/25 - High Structural Vulnerability', 0, 1)
    pdf.set_x(10)
    pdf.cell(0, 6, 'Bhopal: 4/25 - High Structural Vulnerability', 0, 1)
    pdf.set_x(10)
    pdf.cell(0, 6, 'Industry average (estimated): 12/25 - Conditional Stability', 0, 1)
    pdf.ln(6)

    # --- DISCLAIMER ---
    pdf.set_x(10)
    pdf.set_font('Helvetica', 'I', 9)
    pdf.set_text_color(75, 85, 99)
    pdf.multi_cell(0, 5,
                   'This diagnostic identifies structural conditions. It does not replace '
                   'a full SIM audit (field interviews, document review, evidence verification). '
                   'AI may assist; human judgment remains binding.')
    pdf.ln(4)

    pdf.set_x(10)
    pdf.multi_cell(0, 5,
                   'AVCS - Adaptive Vector Control System. '
                   'Charter v1.1 / CORE v2.1 / Code of Ethics v1.1 / Code of Practice v1.1.')
    pdf.ln(4)

    # --- QUOTE ---
    pdf.set_x(10)
    pdf.set_font('Helvetica', 'I', 10)
    pdf.set_text_color(30, 58, 138)
    pdf.multi_cell(0, 6,
                   '"Continuation without control is a managed risk - not a controlled one."')
    pdf.set_x(10)
    pdf.set_font('Helvetica', '', 9)
    pdf.set_text_color(75, 85, 99)
    pdf.cell(0, 5, '- AVCS CORE v2.1', 0, 1)
    pdf.ln(6)

    # --- LINKS ---
    pdf.set_x(10)
    pdf.set_font('Helvetica', 'B', 10)
    pdf.set_text_color(30, 58, 138)
    pdf.cell(0, 6, 'Full AVCS documentation:', 0, 1)
    pdf.set_x(10)
    pdf.set_font('Helvetica', '', 9)
    pdf.set_text_color(31, 41, 55)
    pdf.multi_cell(0, 5,
                   'https://github.com/yeruslan72-svg/AVCS-VIRTUAL-COMPANY/tree/main/docs')
    pdf.ln(2)
    pdf.set_x(10)
    pdf.set_font('Helvetica', 'B', 10)
    pdf.set_text_color(30, 58, 138)
    pdf.cell(0, 6, 'System Navigator:', 0, 1)
    pdf.set_x(10)
    pdf.set_font('Helvetica', '', 9)
    pdf.set_text_color(31, 41, 55)
    pdf.multi_cell(0, 5,
                   'https://github.com/yeruslan72-svg/AVCS-VIRTUAL-COMPANY/blob/main/docs/System_Navigator.md')

    pdf_output = pdf.output()
    return base64.b64encode(pdf_output).decode('latin1')


# ------------------------------
# Вспомогательные функции
# ------------------------------
def save_answers(keys):
    for key in keys:
        if key in st.session_state:
            st.session_state.answers[key] = st.session_state[key]


def all_answered(keys):
    return all(st.session_state.get(k) is not None for k in keys)


# ------------------------------
# WELCOME SCREEN
# ------------------------------
if not st.session_state.welcome_shown:
    try:
        st.image("north_is_not_negotiable.png", use_container_width=True)
    except:
        try:
            st.image("logo.png", use_container_width=True)
        except:
            st.markdown("# 🧭 AVCS")

    st.markdown("---")

    st.markdown("""
    <div style="text-align: center; padding: 20px 0;">
        <h1 style="color: #1e3a8a; font-size: 40px; margin-bottom: 10px;">
            AVCS Structural Integrity Module
        </h1>
        <p style="color: #4b5563; font-size: 19px; font-style: italic;">
            Diagnosing decision architecture before failure, not after
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    st.markdown("""
    <div class="welcome-box">
        <p style="font-size: 18px; line-height: 1.7; color: #1f2937;">
            <strong>Deepwater Horizon scored 3/25.</strong>
        </p>
        <p style="font-size: 16px; line-height: 1.7; color: #4b5563;">
            Not because of engineering failure - because structural decision
            weaknesses were embedded long before the explosion.
        </p>
        <p style="font-size: 16px; line-height: 1.7; color: #4b5563;">
            Most systems don't fail because people are incompetent.
            They fail because structural weaknesses remain invisible until it's too late.
        </p>
        <p style="font-size: 16px; line-height: 1.7; color: #1e3a8a; font-weight: bold;">
            SIM makes the invisible visible.
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="info-box">
        <p style="font-size: 16px; color: #1e3a8a; font-weight: bold; margin-bottom: 10px;">
            This assessment takes 5-10 minutes. You will receive:
        </p>
        <ul style="font-size: 15px; line-height: 1.9; color: #1f2937;">
            <li>Structural Integrity Score (0-25)</li>
            <li>Visual radar chart of five pillars</li>
            <li>Score justification for each pillar</li>
            <li>Benchmarks (Deepwater Horizon, Bhopal)</li>
            <li>Professional PDF report</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("▸ ENTER DIAGNOSTIC", use_container_width=True):
        st.session_state.welcome_shown = True
        st.rerun()

    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #8a8a8a; font-size: 13px; padding: 10px 0;">
        <p>SIM Lite v1.4 - AVCS - Adaptive Vector Control System</p>
        <p>2026 Yeruslan Chihachyov | CC BY-NC-ND 4.0</p>
        <p>
            <a href="https://github.com/yeruslan72-svg/AVCS-VIRTUAL-COMPANY/tree/main/docs" target="_blank">
            Full AVCS documentation
            </a>
            &nbsp;|&nbsp;
            <a href="https://github.com/yeruslan72-svg/AVCS-VIRTUAL-COMPANY/blob/main/docs/System_Navigator.md" target="_blank">
            System Navigator
            </a>
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.stop()

# ------------------------------
# Sidebar
# ------------------------------
with st.sidebar:
    try:
        st.image("logo.png", width=200)
    except:
        st.markdown("### 🧭 AVCS")

    st.markdown("## Progress")
    progress = (st.session_state.step - 1) / 5
    st.progress(min(progress, 1.0))
    st.markdown(f"**Step {st.session_state.step} of 5**")

    if st.session_state.step > 1:
        st.markdown("---")
        st.markdown("### Current Scores")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Trigger", st.session_state.scores['trigger_clarity'])
            st.metric("Ownership", st.session_state.scores['decision_ownership'])
            st.metric("Intervention", st.session_state.scores['protected_intervention'])
        with col2:
            st.metric("Override", st.session_state.scores['override_transparency'])
            st.metric("Drift", st.session_state.scores['drift_detection'])

    st.markdown("---")
    st.caption("SIM Lite v1.4")
    st.caption("2026 Yeruslan Chihachyov")
    st.caption("CC BY-NC-ND 4.0")


# ------------------------------
# ШАГ 1 — Trigger Clarity
# ------------------------------
if st.session_state.step == 1:
    st.markdown("""
    <div class="pillar-card">
        <h2>1. Trigger Clarity</h2>
        <p>Are escalation conditions mandatory or interpretive?</p>
    </div>
    """, unsafe_allow_html=True)

    with st.form("trigger_form"):
        st.radio(
            "Are critical deviation thresholds mandatory and enforced, or discretionary?",
            ["Mandatory and enforced", "Defined but discretionary", "No defined thresholds"],
            index=None,
            key='q1_1'
        )

        st.radio(
            "Are trend-based deviations (not just threshold breaches) tracked and escalated?",
            ["Yes, systematically tracked", "Sometimes noticed", "No, only threshold breaches trigger attention"],
            index=None,
            key='q1_2'
        )

        st.radio(
            "Is escalation automatic or does it require human decision?",
            ["Automatic (mandatory)", "Requires decision (discretionary)", "Often doesn't happen"],
            index=None,
            key='q1_3'
        )

        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            submitted = st.form_submit_button("Next →", use_container_width=True)

        if submitted:
            keys = ['q1_1', 'q1_2', 'q1_3']
            if not all_answered(keys):
                st.error("Please answer all questions before proceeding.")
            else:
                save_answers(keys)
                st.session_state.scores['trigger_clarity'] = calculate_trigger_score(st.session_state.answers)
                st.session_state.justifications['trigger_clarity'] = justify_trigger(
                    st.session_state.scores['trigger_clarity'], st.session_state.answers)
                st.session_state.step = 2
                st.rerun()

# ------------------------------
# ШАГ 2 — Decision Ownership
# ------------------------------
elif st.session_state.step == 2:
    st.markdown("""
    <div class="pillar-card">
        <h2>2. Decision Ownership</h2>
        <p>Is accountability singular and real-time?</p>
    </div>
    """, unsafe_allow_html=True)

    with st.form("ownership_form"):
        st.radio(
            "Is a single accountable owner defined for critical decisions?",
            ["Yes, singular owner defined", "Shared but clear", "Collective/unclear"],
            index=None,
            key='q2_1'
        )

        st.radio(
            "Is the owner operationally present during risk exposure?",
            ["Yes, always present", "Usually present", "Rarely present"],
            index=None,
            key='q2_2'
        )

        st.radio(
            "Is ownership always traceable to a named decision-maker?",
            ["Yes, always", "Sometimes", "Rarely / never"],
            index=None,
            key='q2_3'
        )

        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            back = st.form_submit_button("← Back", use_container_width=True)
        with col3:
            submitted = st.form_submit_button("Next →", use_container_width=True)

        if back:
            st.session_state.step = 1
            st.rerun()

        if submitted:
            keys = ['q2_1', 'q2_2', 'q2_3']
            if not all_answered(keys):
                st.error("Please answer all questions before proceeding.")
            else:
                save_answers(keys)
                st.session_state.scores['decision_ownership'] = calculate_ownership_score(st.session_state.answers)
                st.session_state.justifications['decision_ownership'] = justify_ownership(
                    st.session_state.scores['decision_ownership'], st.session_state.answers)
                st.session_state.step = 3
                st.rerun()

# ------------------------------
# ШАГ 3 — Protected Intervention
# ------------------------------
elif st.session_state.step == 3:
    st.markdown("""
    <div class="pillar-card">
        <h2>3. Protected Intervention</h2>
        <p>Is stopping operations structurally safe?</p>
    </div>
    """, unsafe_allow_html=True)

    with st.form("intervention_form"):
        st.radio(
            "Is stop-work authority formally codified and protected?",
            ["Yes, formally codified and protected", "Yes, but informally", "No"],
            index=None,
            key='q3_1'
        )

        st.radio(
            "What happens to someone who initiates a stop-work decision?",
            ["Always supported", "Usually supported", "Questioned / criticized"],
            index=None,
            key='q3_2'
        )

        st.radio(
            "Does stopping operations negatively affect performance metrics?",
            ["No, never", "Sometimes", "Yes, often"],
            index=None,
            key='q3_3'
        )

        st.markdown("---")
        st.markdown("**Operator Fitness Protection**")

        st.radio(
            "Does the system provide a formal, protected mechanism for an operator to refuse duty when unfit?",
            ["Yes, formally codified and protected", "Yes, but informal", "No"],
            index=None,
            key='q3_4'
        )

        st.markdown("---")
        st.markdown("**Evidence Before Status**")

        st.radio(
            "If stop-work authority is claimed, can you show evidence it was actually available at the moment of decision?",
            ["Yes, evidence exists (records, logs, procedures)", "Partial evidence", "No, status is claimed but not evidenced"],
            index=None,
            key='q3_5'
        )

        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            back = st.form_submit_button("← Back", use_container_width=True)
        with col3:
            submitted = st.form_submit_button("Next →", use_container_width=True)

        if back:
            st.session_state.step = 2
            st.rerun()

        if submitted:
            keys = ['q3_1', 'q3_2', 'q3_3', 'q3_4', 'q3_5']
            if not all_answered(keys):
                st.error("Please answer all questions before proceeding.")
            else:
                save_answers(keys)
                st.session_state.scores['protected_intervention'] = calculate_intervention_score(st.session_state.answers)
                st.session_state.justifications['protected_intervention'] = justify_intervention(
                    st.session_state.scores['protected_intervention'], st.session_state.answers)
                st.session_state.step = 4
                st.rerun()

# ------------------------------
# ШАГ 4 — Override Transparency
# ------------------------------
elif st.session_state.step == 4:
    st.markdown("""
    <div class="pillar-card">
        <h2>4. Override Transparency</h2>
        <p>Are deviations visible and traceable?</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="info-box">
        <strong>Controlled degradation vs drift:</strong>
        Not every reduction of margin requires an immediate stop.
        The structural difference is whether the reduction is
        <em>declared, owned, documented, and reviewable</em> - or silently normalized.
    </div>
    """, unsafe_allow_html=True)

    with st.form("override_form"):
        st.radio(
            "Are procedural deviations always documented?",
            ["Yes, always", "Sometimes", "No, commonly informal"],
            index=None,
            key='q4_1'
        )

        st.radio(
            "Are overrides traceable to a named decision-maker?",
            ["Yes, always", "Sometimes", "Rarely"],
            index=None,
            key='q4_2'
        )

        st.radio(
            "Are overrides reviewed periodically?",
            ["Yes, regularly", "Occasionally", "Never"],
            index=None,
            key='q4_3'
        )

        st.markdown("---")
        st.markdown("**Controlled Degradation**")

        st.radio(
            "When a deviation is allowed to continue, is the residual risk assigned to a named decision owner?",
            ["Yes, always", "Sometimes", "No, continuation is not assigned"],
            index=None,
            key='q4_4'
        )

        st.markdown("---")
        st.markdown("**Evidence Before Status**")

        st.radio(
            "If overrides are claimed to be documented, can you produce evidence of the last three overrides?",
            ["Yes, evidence exists", "Partial evidence", "No, status is claimed but not evidenced"],
            index=None,
            key='q4_5'
        )

        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            back = st.form_submit_button("← Back", use_container_width=True)
        with col3:
            submitted = st.form_submit_button("Next →", use_container_width=True)

        if back:
            st.session_state.step = 3
            st.rerun()

        if submitted:
            keys = ['q4_1', 'q4_2', 'q4_3', 'q4_4', 'q4_5']
            if not all_answered(keys):
                st.error("Please answer all questions before proceeding.")
            else:
                save_answers(keys)
                st.session_state.scores['override_transparency'] = calculate_override_score(st.session_state.answers)
                st.session_state.justifications['override_transparency'] = justify_override(
                    st.session_state.scores['override_transparency'], st.session_state.answers)
                st.session_state.step = 5
                st.rerun()

# ------------------------------
# ШАГ 5 — Drift Detection
# ------------------------------
elif st.session_state.step == 5:
    st.markdown("""
    <div class="pillar-card">
        <h2>5. Drift Detection</h2>
        <p>Is boundary movement tracked or ignored?</p>
    </div>
    """, unsafe_allow_html=True)

    with st.form("drift_form"):
        st.radio(
            "Are minor deviations recorded systematically?",
            ["Yes, systematically", "Sometimes", "Rarely"],
            index=None,
            key='q5_1'
        )

        st.radio(
            "Is deviation trend analyzed longitudinally?",
            ["Yes, regularly", "Occasionally", "Never"],
            index=None,
            key='q5_2'
        )

        st.radio(
            "Is normalization of deviation actively monitored?",
            ["Yes, actively", "Sometimes", "No"],
            index=None,
            key='q5_3'
        )

        st.markdown("---")
        st.markdown("**Evidence Before Status**")

        st.radio(
            "If the system claims to detect drift, can you produce evidence of a drift that was detected and acted upon?",
            ["Yes, evidence exists", "Partial evidence", "No, status is claimed but not evidenced"],
            index=None,
            key='q5_4'
        )

        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            back = st.form_submit_button("← Back", use_container_width=True)
        with col3:
            submitted = st.form_submit_button("Calculate Results →", use_container_width=True)

        if back:
            st.session_state.step = 4
            st.rerun()

        if submitted:
            keys = ['q5_1', 'q5_2', 'q5_3', 'q5_4']
            if not all_answered(keys):
                st.error("Please answer all questions before proceeding.")
            else:
                save_answers(keys)
                st.session_state.scores['drift_detection'] = calculate_drift_score(st.session_state.answers)
                st.session_state.justifications['drift_detection'] = justify_drift(
                    st.session_state.scores['drift_detection'], st.session_state.answers)
                st.session_state.step = 6
                st.rerun()

# ------------------------------
# ШАГ 6 — Результаты
# ------------------------------
elif st.session_state.step == 6:
    total_score = sum(st.session_state.scores.values())

    if total_score <= 10:
        classification = "HIGH STRUCTURAL VULNERABILITY"
        color = "#dc2626"
        message = "Your system shows significant structural weaknesses. Drift may already be normalized."
    elif total_score <= 17:
        classification = "CONDITIONAL STABILITY"
        color = "#f59e0b"
        message = "Some pillars are strong, but vulnerabilities exist. Focus on weakest areas."
    elif total_score <= 22:
        classification = "STRUCTURALLY CONTROLLED"
        color = "#3b82f6"
        message = "Good structural health. Targeted improvements will strengthen further."
    else:
        classification = "ARCHITECTURALLY RESILIENT"
        color = "#10b981"
        message = "Excellent structural integrity. Your system is designed to protect good decisions."

    st.markdown(f"""
    <div style="text-align: center; margin-bottom: 20px;">
        <h1 style="color: #1e3a8a;">Your Structural Integrity Results</h1>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown(f"""
        <div class="score-box" style="background-color: {color};">
            {total_score} / 25
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div style="text-align: center; padding: 15px; background-color: white; border-radius: 10px; margin-bottom: 20px;">
            <h3 style="color: {color};">{classification}</h3>
            <p>{message}</p>
        </div>
        """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Radar Chart")
        fig = create_radar_chart(st.session_state.scores)
        st.plotly_chart(
            fig,
            use_container_width=True,
            config={'displayModeBar': False}
        )

    with col2:
        st.markdown("### Pillar Scores")

        pillar_labels = {
            'trigger_clarity': 'Trigger Clarity',
            'decision_ownership': 'Decision Ownership',
            'protected_intervention': 'Protected Intervention',
            'override_transparency': 'Override Transparency',
            'drift_detection': 'Drift Detection'
        }

        for key, label in pillar_labels.items():
            score = st.session_state.scores[key]
            st.markdown(f"""
            <div style="margin-bottom: 10px;">
                <div style="display: flex; justify-content: space-between;">
                    <span><strong>{label}</strong></span>
                    <span>{score}/5</span>
                </div>
                <div style="width: 100%; background-color: #e0e0e0; height: 10px; border-radius: 5px;">
                    <div style="width: {(score/5)*100}%; background-color: #1e3a8a; height: 10px; border-radius: 5px;"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")

    st.markdown("### Score Justification")

    for key, label in pillar_labels.items():
        st.markdown(f"**{label}:** {st.session_state.justifications[key]}")

    st.markdown("---")

    st.markdown("### Benchmarks")

    st.markdown("""
    <div class="benchmark-box">
        <strong>Reference points:</strong><br>
        Deepwater Horizon: <strong>3/25</strong> - High Structural Vulnerability<br>
        Bhopal: <strong>4/25</strong> - High Structural Vulnerability<br>
        Industry average (estimated): <strong>12/25</strong> - Conditional Stability
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    st.markdown("### Interpretation")

    weak_pillars = []
    for pillar, score in st.session_state.scores.items():
        if score <= 2:
            weak_pillars.append(pillar_labels[pillar])

    if weak_pillars:
        st.markdown(f"""
        <div class="warning-box">
            <strong>Priority areas:</strong> Your weakest pillars are: {', '.join(weak_pillars)}.
            These represent the highest structural vulnerability.
        </div>
        """, unsafe_allow_html=True)

    st.markdown("""
    <div class="info-box">
        <strong>Note:</strong> This diagnostic identifies structural conditions.
        A full SIM audit includes field interviews, document review,
        and evidence verification. See the full AVCS documentation for the complete standard.
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    col1, col2, col3 = st.columns(3)

    with col1:
        pdf_data = create_pdf(
            st.session_state.scores,
            total_score,
            st.session_state.justifications
        )
        href = f'<a href="data:application/octet-stream;base64,{pdf_data}" download="AVCS_SIM_Report.pdf"><button style="background-color: #1e3a8a; color: white; padding: 8px 16px; border: none; border-radius: 5px; cursor: pointer;">Download PDF Report</button></a>'
        st.markdown(href, unsafe_allow_html=True)

    with col2:
        if st.button("New Assessment", use_container_width=True):
            for key in ['step', 'scores', 'answers', 'justifications', 'welcome_shown']:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()

    with col3:
        linkedin_url = "https://www.linkedin.com/in/yeruslan-chihachyov-70a807126"
        st.markdown(f'''
        <a href="{linkedin_url}" target="_blank">
            <button style="background-color: #0a66c2; color: white; padding: 8px 16px; border: none; border-radius: 5px; cursor: pointer; width: 100%;">
            Request Full Audit
            </button>
        </a>
        ''', unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #8a8a8a; font-size: 13px; padding: 10px 0;">
        <p>SIM Lite v1.4 - AVCS - Adaptive Vector Control System</p>
        <p>2026 Yeruslan Chihachyov | CC BY-NC-ND 4.0</p>
        <p>
            <a href="https://github.com/yeruslan72-svg/AVCS-VIRTUAL-COMPANY/tree/main/docs" target="_blank">
            Full AVCS documentation
            </a>
            &nbsp;|&nbsp;
            <a href="https://github.com/yeruslan72-svg/AVCS-VIRTUAL-COMPANY/blob/main/docs/System_Navigator.md" target="_blank">
            System Navigator
            </a>
        </p>
    </div>
    """, unsafe_allow_html=True)
