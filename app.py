import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from fpdf import FPDF
import base64
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
# Стили CSS (исправлено: rem → px)
# ------------------------------
st.markdown("""
<style>
    .stApp {
        background-color: #f8f9fa;
    }
    .main-header {
        text-align: center;
        padding: 20px 0;
        background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 20px;
    }
    .main-header h1 {
        font-size: 32px;
        margin-bottom: 10px;
    }
    .main-header p {
        font-size: 18px;
    }
    .pillar-card {
        background-color: white;
        color: #000000;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 15px;
        border-left: 4px solid #1e3a8a;
    }
    .pillar-card h2 {
        color: #1e3a8a;
        margin-top: 0;
        margin-bottom: 10px;
    }
    .pillar-card p {
        color: #4b5563;
        margin-bottom: 0;
    }
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
    .stButton button:hover {
        background-color: #3b82f6;
    }
    .stRadio label {
        color: #000000 !important;
        font-size: 16px;
    }
    .stRadio div {
        color: #000000 !important;
    }
    .stMarkdown {
        color: #000000;
    }
</style>
""", unsafe_allow_html=True)

# ------------------------------
# Заголовок
# ------------------------------
st.markdown("""
<div class="main-header">
    <h1>🧭 AVCS Structural Integrity Module</h1>
    <p>Diagnosing decision architecture before failure, not after</p>
</div>
""", unsafe_allow_html=True)

# ------------------------------
# Инициализация состояния сессии
# ------------------------------
if 'step' not in st.session_state:
    st.session_state.step = 1
if 'scores' not in st.session_state:
    st.session_state.scores = {
        'trigger_clarity': 0,
        'decision_ownership': 0,
        'protected_intervention': 0,
        'override_transparency': 0,
        'drift_detection': 0
    }
if 'answers' not in st.session_state:
    st.session_state.answers = {}

# ------------------------------
# Боковая панель с прогрессом
# ------------------------------
with st.sidebar:
    st.image("logo.png", width=200)
    st.markdown("## Progress")
    progress = (st.session_state.step - 1) / 6
    st.progress(progress)
    st.markdown(f"**Step {st.session_state.step} of 6**")
    
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

# ------------------------------
# Функции для расчёта скоров
# ------------------------------
def calculate_trigger_score(answers):
    score = 0
    if answers.get('q1_1') == "Yes, mandatory and enforced": score += 2
    elif answers.get('q1_1') == "Yes, but discretionary": score += 1
    
    if answers.get('q1_2') == "No, all deviations tracked": score += 2
    elif answers.get('q1_2') == "Sometimes noticed": score += 1
    
    if answers.get('q1_3') == "Automatic": score += 1
    return min(score, 5)

def calculate_ownership_score(answers):
    score = 0
    if answers.get('q2_1') == "Yes, singular owner defined": score += 2
    elif answers.get('q2_1') == "Shared but clear": score += 1
    
    if answers.get('q2_2') == "Yes, always present": score += 2
    elif answers.get('q2_2') == "Usually present": score += 1
    
    if answers.get('q2_3') == "No, never": score += 1
    return min(score, 5)

def calculate_intervention_score(answers):
    score = 0
    if answers.get('q3_1') == "Yes, formally codified and protected": score += 2
    elif answers.get('q3_1') == "Yes, but informally": score += 1
    
    if answers.get('q3_2') == "Always supported": score += 2
    elif answers.get('q3_2') == "Usually supported": score += 1
    
    if answers.get('q3_3') == "No, never": score += 1
    return min(score, 5)

def calculate_override_score(answers):
    score = 0
    if answers.get('q4_1') == "No, always documented": score += 2
    elif answers.get('q4_1') == "Sometimes documented": score += 1
    
    if answers.get('q4_2') == "Yes, always": score += 2
    elif answers.get('q4_2') == "Sometimes": score += 1
    
    if answers.get('q4_3') == "Yes, regularly": score += 1
    return min(score, 5)

def calculate_drift_score(answers):
    score = 0
    if answers.get('q5_1') == "Yes, systematically": score += 2
    elif answers.get('q5_1') == "Sometimes": score += 1
    
    if answers.get('q5_2') == "Yes, regularly": score += 2
    elif answers.get('q5_2') == "Occasionally": score += 1
    
    if answers.get('q5_3') == "Yes, actively": score += 1
    return min(score, 5)

# ------------------------------
# Функция для создания радар-графика
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
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 5]
            )),
        showlegend=False,
        height=400,
        margin=dict(l=80, r=80, t=20, b=20)
    )
    return fig

# ------------------------------
# Функция для создания PDF-отчёта
# ------------------------------
def create_pdf(scores, total_score):
    pdf = FPDF()
    pdf.add_page()
    
    # Заголовок
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, 'AVCS Structural Integrity Module Report', 0, 1, 'C')
    pdf.ln(10)
    
    # Дата
    pdf.set_font('Arial', '', 10)
    pdf.cell(0, 10, f'Generated: {datetime.now().strftime("%Y-%m-%d %H:%M")}', 0, 1, 'R')
    pdf.ln(10)
    
    # Общий скор
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, f'Total Structural Integrity Score: {total_score} / 25', 0, 1)
    
    # Классификация
    if total_score <= 10:
        classification = "HIGH STRUCTURAL VULNERABILITY"
    elif total_score <= 17:
        classification = "CONDITIONAL STABILITY"
    elif total_score <= 22:
        classification = "STRUCTURALLY CONTROLLED"
    else:
        classification = "ARCHITECTURALLY RESILIENT"
    
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, f'Classification: {classification}', 0, 1)
    pdf.ln(10)
    
    # Детальные скоры
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, 'Pillar Scores:', 0, 1)
    pdf.set_font('Arial', '', 12)
    
    pillars = [
        ('Trigger Clarity', scores['trigger_clarity']),
        ('Decision Ownership', scores['decision_ownership']),
        ('Protected Intervention', scores['protected_intervention']),
        ('Override Transparency', scores['override_transparency']),
        ('Drift Detection', scores['drift_detection'])
    ]
    
    for name, score in pillars:
        pdf.cell(0, 10, f'{name}: {score}/5', 0, 1)
    
    # Сохраняем PDF в строку
    pdf_output = pdf.output(dest='S').encode('latin1')
    return base64.b64encode(pdf_output).decode('latin1')

# ------------------------------
# Основное приложение - по шагам
# ------------------------------

# Шаг 1: Введение
if st.session_state.step == 1:
    st.markdown("""
    <div style="background-color: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
        <h2>Welcome to the AVCS Structural Integrity Module</h2>
        <p style="font-size: 16px; line-height: 1.6;">
        This diagnostic tool evaluates your organization's decision architecture across five critical pillars.
        </p>
        <p style="font-size: 16px; line-height: 1.6;">
        <strong>Deepwater Horizon scored 3/25.</strong> Not because of engineering failure, 
        but because structural decision weaknesses were embedded long before the explosion.
        </p>
        <p style="font-size: 16px; line-height: 1.6;">
        The assessment takes 5-10 minutes. You'll receive:
        </p>
        <ul style="font-size: 16px; line-height: 1.8;">
            <li>Structural Integrity Score (0-25)</li>
            <li>Visual radar chart of your five pillars</li>
            <li>PDF report with recommendations</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("Start Assessment →", use_container_width=True):
            st.session_state.step = 2
            st.rerun()

# Шаг 2: Trigger Clarity
elif st.session_state.step == 2:
    st.markdown("""
    <div class="pillar-card">
        <h2>1. Trigger Clarity</h2>
        <p>Are escalation conditions mandatory or interpretive?</p>
    </div>
    """, unsafe_allow_html=True)
    
    with st.form("trigger_form"):
        q1 = st.radio(
            "Are critical deviation thresholds mandatory and enforced, or discretionary?",
            ["Yes, mandatory and enforced", "Yes, but discretionary", "No clear thresholds"],
            key='q1_1'
        )
        
        q2 = st.radio(
            "Can deviations exist without crossing formal limits?",
            ["No, all deviations tracked", "Sometimes noticed", "Yes, often unnoticed"],
            key='q1_2'
        )
        
        q3 = st.radio(
            "Is escalation automatic or requires human decision?",
            ["Automatic", "Requires decision", "Often doesn't happen"],
            key='q1_3'
        )
        
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            submitted = st.form_submit_button("Next →", use_container_width=True)
        
        if submitted:
            st.session_state.answers.update(st.session_state)
            st.session_state.scores['trigger_clarity'] = calculate_trigger_score(st.session_state.answers)
            st.session_state.step = 3
            st.rerun()

# Шаг 3: Decision Ownership
elif st.session_state.step == 3:
    st.markdown("""
    <div class="pillar-card">
        <h2>2. Decision Ownership</h2>
        <p>Is accountability singular and real-time?</p>
    </div>
    """, unsafe_allow_html=True)
    
    with st.form("ownership_form"):
        q1 = st.radio(
            "Is a single accountable owner defined for critical decisions?",
            ["Yes, singular owner defined", "Shared but clear", "Collective/unclear"],
            key='q2_1'
        )
        
        q2 = st.radio(
            "Is the owner operationally present during risk exposure?",
            ["Yes, always present", "Usually present", "Rarely present"],
            key='q2_2'
        )
        
        q3 = st.radio(
            "Can ownership be overridden collectively without traceability?",
            ["No, never", "Sometimes", "Yes, commonly"],
            key='q2_3'
        )
        
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.form_submit_button("Next →", use_container_width=True):
                st.session_state.answers.update(st.session_state)
                st.session_state.scores['decision_ownership'] = calculate_ownership_score(st.session_state.answers)
                st.session_state.step = 4
                st.rerun()

# Шаг 4: Protected Intervention
elif st.session_state.step == 4:
    st.markdown("""
    <div class="pillar-card">
        <h2>3. Protected Intervention</h2>
        <p>Is stopping operations structurally safe?</p>
    </div>
    """, unsafe_allow_html=True)
    
    with st.form("intervention_form"):
        q1 = st.radio(
            "Is stop-work authority formally codified and protected?",
            ["Yes, formally codified and protected", "Yes, but informally", "No"],
            key='q3_1'
        )
        
        q2 = st.radio(
            "How are stop-work decisions reviewed?",
            ["Always supported", "Usually supported", "Questioned/criticized"],
            key='q3_2'
        )
        
        q3 = st.radio(
            "Does stopping operations negatively affect performance metrics?",
            ["No, never", "Sometimes", "Yes, often"],
            key='q3_3'
        )
        
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.form_submit_button("Next →", use_container_width=True):
                st.session_state.answers.update(st.session_state)
                st.session_state.scores['protected_intervention'] = calculate_intervention_score(st.session_state.answers)
                st.session_state.step = 5
                st.rerun()

# Шаг 5: Override Transparency
elif st.session_state.step == 5:
    st.markdown("""
    <div class="pillar-card">
        <h2>4. Override Transparency</h2>
        <p>Are deviations visible and traceable?</p>
    </div>
    """, unsafe_allow_html=True)
    
    with st.form("override_form"):
        q1 = st.radio(
            "Can procedures be bypassed informally without documentation?",
            ["No, always documented", "Sometimes documented", "Yes, commonly"],
            key='q4_1'
        )
        
        q2 = st.radio(
            "Are overrides traceable to a named decision-maker?",
            ["Yes, always", "Sometimes", "Rarely"],
            key='q4_2'
        )
        
        q3 = st.radio(
            "Are overrides reviewed periodically?",
            ["Yes, regularly", "Occasionally", "Never"],
            key='q4_3'
        )
        
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.form_submit_button("Next →", use_container_width=True):
                st.session_state.answers.update(st.session_state)
                st.session_state.scores['override_transparency'] = calculate_override_score(st.session_state.answers)
                st.session_state.step = 6
                st.rerun()

# Шаг 6: Drift Detection
elif st.session_state.step == 6:
    st.markdown("""
    <div class="pillar-card">
        <h2>5. Drift Detection</h2>
        <p>Is boundary movement tracked or ignored?</p>
    </div>
    """, unsafe_allow_html=True)
    
    with st.form("drift_form"):
        q1 = st.radio(
            "Are minor deviations recorded systematically?",
            ["Yes, systematically", "Sometimes", "Rarely"],
            key='q5_1'
        )
        
        q2 = st.radio(
            "Is deviation trend analyzed longitudinally?",
            ["Yes, regularly", "Occasionally", "Never"],
            key='q5_2'
        )
        
        q3 = st.radio(
            "Is normalization of deviation actively monitored?",
            ["Yes, actively", "Sometimes", "No"],
            key='q5_3'
        )
        
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.form_submit_button("Calculate Results →", use_container_width=True):
                st.session_state.answers.update(st.session_state)
                st.session_state.scores['drift_detection'] = calculate_drift_score(st.session_state.answers)
                st.session_state.step = 7
                st.rerun()

# Шаг 7: Результаты
elif st.session_state.step == 7:
    total_score = sum(st.session_state.scores.values())
    
    # Определение классификации
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
    
    # Заголовок
    st.markdown(f"""
    <div style="text-align: center; margin-bottom: 20px;">
        <h1 style="color: #1e3a8a;">Your Structural Integrity Results</h1>
    </div>
    """, unsafe_allow_html=True)
    
    # Общий скор
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
    
    # Два столбца: график и детальные скоры
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Radar Chart")
        fig = create_radar_chart(st.session_state.scores)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("### Pillar Scores")
        
        scores_df = pd.DataFrame({
            'Pillar': ['Trigger Clarity', 'Decision Ownership', 'Protected Intervention', 
                      'Override Transparency', 'Drift Detection'],
            'Score': [
                st.session_state.scores['trigger_clarity'],
                st.session_state.scores['decision_ownership'],
                st.session_state.scores['protected_intervention'],
                st.session_state.scores['override_transparency'],
                st.session_state.scores['drift_detection']
            ]
        })
        
        for idx, row in scores_df.iterrows():
            st.markdown(f"""
            <div style="margin-bottom: 10px;">
                <div style="display: flex; justify-content: space-between;">
                    <span><strong>{row['Pillar']}</strong></span>
                    <span>{row['Score']}/5</span>
                </div>
                <div style="width: 100%; background-color: #e0e0e0; height: 10px; border-radius: 5px;">
                    <div style="width: {(row['Score']/5)*100}%; background-color: #1e3a8a; height: 10px; border-radius: 5px;"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Интерпретация
    st.markdown("### Interpretation")
    
    weak_pillars = []
    for pillar, score in st.session_state.scores.items():
        if score <= 2:
            weak_pillars.append(pillar.replace('_', ' ').title())
    
    if weak_pillars:
        st.markdown(f"""
        <div style="background-color: #fee2e2; padding: 15px; border-radius: 10px; border-left: 4px solid #dc2626;">
            <strong>⚠️ Priority areas:</strong> Your weakest pillars are: {', '.join(weak_pillars)}. 
            These represent the highest structural vulnerability.
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("""
    <div style="background-color: #e6f7ff; padding: 15px; border-radius: 10px; margin-top: 10px;">
        <strong>💡 Note:</strong> This diagnostic identifies structural conditions. A full SIM audit includes 
        field interviews, document review, and detailed reinforcement planning.
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Кнопки действий
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # PDF Report
        pdf_data = create_pdf(st.session_state.scores, total_score)
        href = f'<a href="data:application/octet-stream;base64,{pdf_data}" download="AVCS_SIM_Report.pdf"><button style="background-color: #1e3a8a; color: white; padding: 8px 16px; border: none; border-radius: 5px; cursor: pointer;">📥 Download PDF Report</button></a>'
        st.markdown(href, unsafe_allow_html=True)
    
    with col2:
        if st.button("🔄 New Assessment", use_container_width=True):
            for key in ['step', 'scores', 'answers']:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()
    
    with col3:
        st.markdown("""
        <a href="https://www.linkedin.com/in/yeruslan-chihachyov-70a807126" target="_blank">
            <button style="background-color: #0a66c2; color: white; padding: 8px 16px; border: none; border-radius: 5px; cursor: pointer; width: 100%;">
            📞 Request Full Audit
            </button>
        </a>
        """, unsafe_allow_html=True)
