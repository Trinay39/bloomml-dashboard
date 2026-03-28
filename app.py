# app.py — Cloud-ready version of step4_dashboard.py
# Only change from original: model path uses Claude API only (no local model on cloud)

import streamlit as st
import pandas as pd
import json
import os
import random
import time
from pathlib import Path
from datetime import datetime

st.set_page_config(
    page_title="BloomML — Advanced Question Generator",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');
    :root {
        --bg: #0a0a0f; --surface: #12121a; --surface2: #1a1a26;
        --border: #2a2a40; --accent: #6366f1; --accent2: #8b5cf6;
        --text: #e2e8f0; --muted: #94a3b8;
    }
    .stApp { background: var(--bg); color: var(--text); font-family: 'Syne', sans-serif; }
    [data-testid="stSidebar"] { background: var(--surface) !important; border-right: 1px solid var(--border); }
    [data-testid="stSidebar"] * { color: var(--text) !important; }
    .bloom-header {
        background: linear-gradient(135deg, #0f0f1e 0%, #1a1030 50%, #0f1520 100%);
        border: 1px solid var(--border); border-radius: 16px;
        padding: 2rem 2.5rem; margin-bottom: 1.5rem;
    }
    .bloom-header h1 {
        font-size: 2.4rem; font-weight: 800;
        background: linear-gradient(135deg, #818cf8, #c084fc);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        margin: 0;
    }
    .bloom-header p { color: var(--muted); margin: 0.5rem 0 0; }
    .question-card {
        background: var(--surface); border: 1px solid var(--border);
        border-radius: 12px; padding: 1.5rem; margin: 1rem 0;
        position: relative;
    }
    .question-card:hover { border-color: var(--accent); }
    .bloom-badge {
        display: inline-block; padding: 0.25rem 0.75rem; border-radius: 999px;
        font-size: 0.75rem; font-weight: 700;
        font-family: 'JetBrains Mono', monospace;
        text-transform: uppercase; margin-bottom: 0.75rem;
    }
    .question-text { font-size: 1.05rem; line-height: 1.7; color: var(--text); }
    .scenario-tag {
        font-size: 0.8rem; color: var(--muted);
        font-family: 'JetBrains Mono', monospace;
        border-left: 3px solid var(--border);
        padding-left: 0.75rem; margin-top: 1rem;
    }
    .q-number {
        position: absolute; top: 1.5rem; right: 1.5rem;
        font-size: 2rem; font-weight: 800;
        color: rgba(255,255,255,0.06);
        font-family: 'JetBrains Mono', monospace;
    }
    .badge-remember  { background: rgba(59,130,246,0.2);  color: #93c5fd; border: 1px solid rgba(59,130,246,0.4); }
    .badge-understand{ background: rgba(6,182,212,0.2);   color: #67e8f9; border: 1px solid rgba(6,182,212,0.4); }
    .badge-apply     { background: rgba(16,185,129,0.2);  color: #6ee7b7; border: 1px solid rgba(16,185,129,0.4); }
    .badge-analyze   { background: rgba(245,158,11,0.2);  color: #fcd34d; border: 1px solid rgba(245,158,11,0.4); }
    .badge-evaluate  { background: rgba(239,68,68,0.2);   color: #fca5a5; border: 1px solid rgba(239,68,68,0.4); }
    .badge-create    { background: rgba(168,85,247,0.2);  color: #d8b4fe; border: 1px solid rgba(168,85,247,0.4); }
    .metric-card {
        background: var(--surface2); border: 1px solid var(--border);
        border-radius: 10px; padding: 1rem; text-align: center;
    }
    .metric-value { font-size: 2rem; font-weight: 800; color: var(--accent); }
    .metric-label { font-size: 0.75rem; color: var(--muted); text-transform: uppercase; }
    .stButton > button {
        background: linear-gradient(135deg, #6366f1, #8b5cf6) !important;
        color: white !important; border: none !important;
        border-radius: 10px !important; font-size: 1rem !important;
        font-weight: 700 !important; width: 100% !important;
        font-family: 'Syne', sans-serif !important;
    }
    .info-box {
        background: rgba(99,102,241,0.1); border: 1px solid rgba(99,102,241,0.3);
        border-radius: 8px; padding: 0.75rem 1rem;
        font-size: 0.85rem; color: #a5b4fc; margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

# ── Constants ──
BLOOM_LEVELS = ["Remember", "Understand", "Apply", "Analyze", "Evaluate", "Create"]
BLOOM_DESCRIPTIONS = {
    "Remember":   "Recall facts, terminology, and fundamental concepts",
    "Understand": "Interpret, explain, and articulate mechanisms",
    "Apply":      "Implement procedures in real-world contexts",
    "Analyze":    "Decompose, diagnose, and critically compare",
    "Evaluate":   "Assess, judge, and formulate defensible positions",
    "Create":     "Architect, design, and synthesize novel systems",
}
TOPICS = [
    "Linear Regression", "Logistic Regression", "Decision Trees", "Random Forests",
    "Support Vector Machines", "K-Means Clustering", "Neural Networks",
    "Convolutional Neural Networks", "Recurrent Neural Networks",
    "Natural Language Processing", "Deep Learning", "Reinforcement Learning",
    "Gradient Boosting", "Principal Component Analysis", "Bayesian Networks",
    "Autoencoders", "Generative Adversarial Networks", "K-Nearest Neighbors",
    "Naive Bayes", "Hierarchical Clustering"
]
BADGE_CLASS = {
    "Remember": "badge-remember", "Understand": "badge-understand",
    "Apply": "badge-apply", "Analyze": "badge-analyze",
    "Evaluate": "badge-evaluate", "Create": "badge-create",
}
BLOOM_PROMPTS = {
    "Remember":   "enumerate, catalogue, specify, classify the key components",
    "Understand": "articulate, interpret, construct a conceptual explanation",
    "Apply":      "implement, design the pipeline, outline concrete steps",
    "Analyze":    "diagnose, decompose, critically compare, examine interactions",
    "Evaluate":   "assess fitness, formulate a judgment with evidence, critique",
    "Create":     "architect a novel system, formulate a research agenda, design",
}
INDUSTRY_POOL = [
    "healthcare and clinical AI under FDA regulations",
    "financial risk management and algorithmic trading",
    "autonomous vehicle safety-critical systems",
    "pharmaceutical R&D and drug discovery pipelines",
    "industrial cybersecurity and threat detection",
    "edge AI in resource-constrained IoT environments",
]

# ── Load dataset ──
@st.cache_data
def load_dataset():
    path = Path("data/bloom_ml_advanced_dataset.csv")
    if path.exists():
        return pd.read_csv(path)
    return pd.DataFrame(columns=["Topic","Context","Bloom_Level","Scenario","Question"])

# ── Generation ──
def build_prompt(topic, bloom_level, scenario, context, prev_questions):
    bloom_action = BLOOM_PROMPTS[bloom_level]
    industry = random.choice(INDUSTRY_POOL)
    prev_block = ""
    if prev_questions:
        prev_block = "\n\nAVOID REPEATING THESE:\n" + \
                     "\n".join(f"• {q[:120]}" for q in prev_questions[-3:])
    return f"""You are a world-class ML academic assessment designer for PhD and senior-practitioner level.

TOPIC: {topic}
BLOOM LEVEL: {bloom_level} — actions: {bloom_action}
INDUSTRY DOMAIN: {industry}
CONTEXT: {context[:400]}
SCENARIO: {scenario}
{prev_block}

RULES:
1. Generate exactly ONE question grounded in the scenario.
2. Do NOT start with: What, Why, How, When, Who, Define, List, Explain.
3. Must be 3-5 sentences, analytically rich, professional level.
4. Must reflect {bloom_level}-level cognitive depth.
5. Use specific {topic} technical terminology.
6. Suitable for senior technical interview or PhD examination.

Output question text only:"""

def generate_with_claude(topic, bloom_level, n_questions, api_key, df, temperature):
    try:
        import anthropic
    except ImportError:
        st.error("anthropic package not found. Check requirements.txt")
        return []

    client = anthropic.Anthropic(api_key=api_key)
    rows = df[(df["Topic"] == topic) & (df["Bloom_Level"] == bloom_level)]

    if rows.empty:
        scenarios = [f"A production ML system using {topic} in a critical enterprise environment."]
        context   = f"Advanced ML topic: {topic}"
    else:
        scenarios = rows["Scenario"].tolist()
        context   = rows.iloc[0]["Context"]

    results, seen = [], []
    progress = st.progress(0)
    status   = st.empty()

    for i in range(n_questions):
        scenario = scenarios[i % len(scenarios)]
        prompt   = build_prompt(topic, bloom_level, scenario, context, seen)
        status.markdown(
            f"<div class='info-box'>⚡ Generating question {i+1} of {n_questions}...</div>",
            unsafe_allow_html=True
        )
        best = None
        for attempt in range(3):
            try:
                response = client.messages.create(
                    model="claude-haiku-4-5-20251001",
                    max_tokens=350,
                    temperature=min(temperature + attempt * 0.05, 1.0),
                    messages=[{"role": "user", "content": prompt}]
                )
                candidate = response.content[0].text.strip()
                bad_starts = ["what is","why is","how is","define ","list ","explain ","when ","who "]
                if len(candidate.split()) >= 25 and not any(
                    candidate.lower().startswith(s) for s in bad_starts
                ):
                    best = candidate
                    break
            except Exception as e:
                if "overloaded" in str(e).lower():
                    time.sleep(2)
                else:
                    st.error(f"API error: {e}")
                    break
        if best:
            results.append({
                "topic": topic, "bloom_level": bloom_level,
                "scenario": scenario, "question": best,
                "timestamp": datetime.now().isoformat(),
            })
            seen.append(best)
        progress.progress((i + 1) / n_questions)

    status.empty()
    progress.empty()
    return results

def generate_from_dataset(topic, bloom_level, n_questions, df):
    rows = df[(df["Topic"] == topic) & (df["Bloom_Level"] == bloom_level)]
    if rows.empty:
        return []
    sampled = rows.sample(min(n_questions, len(rows)), replace=False)
    return [{
        "topic": r["Topic"], "bloom_level": r["Bloom_Level"],
        "scenario": r["Scenario"], "question": r["Question"],
        "timestamp": datetime.now().isoformat(),
    } for _, r in sampled.iterrows()]

# ── Session state ──
if "generated_questions" not in st.session_state:
    st.session_state.generated_questions = []
if "history" not in st.session_state:
    st.session_state.history = []

# ── Sidebar ──
with st.sidebar:
    st.markdown("## 🧠 BloomML")
    st.markdown("**Advanced Question Generator**")
    st.divider()

    st.markdown("### ⚙️ Configuration")

    # Try to get API key from Streamlit secrets first, then let user enter
    default_key = ""
    try:
        default_key = st.secrets["ANTHROPIC_API_KEY"]
    except:
        pass

    api_key = st.text_input(
        "Anthropic API Key",
        value=default_key,
        type="password",
        placeholder="sk-ant-...",
        help="Get free key at console.anthropic.com"
    )
    use_api = bool(api_key)
    if use_api:
        st.success("✅ Claude API enabled")
    else:
        st.info("📂 Using pre-built dataset")

    st.divider()
    st.markdown("### 📐 Bloom's Taxonomy")
    pyramid_colors = {
        "Remember":   ("#3b82f6","15%"), "Understand": ("#06b6d4","20%"),
        "Apply":      ("#10b981","25%"), "Analyze":    ("#f59e0b","30%"),
        "Evaluate":   ("#ef4444","35%"), "Create":     ("#a855f7","40%"),
    }
    for level in reversed(BLOOM_LEVELS):
        color, margin = pyramid_colors[level]
        st.markdown(
            f'<div style="background:{color}22;border:1px solid {color}66;'
            f'margin-left:{margin};color:{color};font-size:0.8rem;'
            f'padding:0.3rem 0.6rem;border-radius:6px;margin-bottom:2px;">'
            f'▸ {level}</div>',
            unsafe_allow_html=True
        )
    st.divider()
    st.markdown("### 📊 Session Stats")
    c1, c2 = st.columns(2)
    c1.metric("Generated", len(st.session_state.generated_questions))
    c2.metric("Topics", len(set(q.get("topic","") for q in st.session_state.generated_questions)))
    if st.button("🗑️ Clear Session"):
        st.session_state.generated_questions = []
        st.session_state.history = []
        st.rerun()

# ── Main ──
st.markdown("""
<div class="bloom-header">
    <h1>BloomML</h1>
    <p>Advanced Scenario-Based Question Generator · Machine Learning · Bloom's Taxonomy</p>
</div>
""", unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns([3,2,1,1])
with col1:
    selected_topic = st.selectbox("🎯 ML Topic", TOPICS, index=6)
with col2:
    selected_bloom = st.selectbox("📐 Bloom Level", BLOOM_LEVELS, index=4)
    st.markdown(
        f'<div style="font-size:0.75rem;color:#94a3b8;margin-top:-0.5rem;">'
        f'{BLOOM_DESCRIPTIONS[selected_bloom]}</div>',
        unsafe_allow_html=True
    )
with col3:
    n_questions = st.slider("# Questions", 1, 10, 4)
with col4:
    temperature = st.slider("🌡️ Creativity", 0.5, 1.0, 0.82, 0.05)

st.markdown("---")

gen_col, exp_col = st.columns([3,1])
with gen_col:
    generate_clicked = st.button(
        f"⚡ Generate {n_questions} Advanced {selected_bloom} Questions"
    )
with exp_col:
    if st.session_state.generated_questions:
        st.download_button(
            "⬇️ Export JSON",
            data=json.dumps(st.session_state.generated_questions, indent=2),
            file_name=f"bloomml_{selected_topic.replace(' ','_')}_{selected_bloom}.json",
            mime="application/json"
        )

df = load_dataset()

if generate_clicked:
    with st.spinner(""):
        if use_api:
            new_qs = generate_with_claude(
                selected_topic, selected_bloom, n_questions, api_key, df, temperature
            )
        else:
            new_qs = generate_from_dataset(selected_topic, selected_bloom, n_questions, df)
            if not new_qs:
                st.warning("Dataset not found. Add an API key for live generation.")
        if new_qs:
            st.session_state.generated_questions = new_qs + st.session_state.generated_questions
            st.session_state.history.append({
                "topic": selected_topic, "bloom": selected_bloom,
                "count": len(new_qs), "ts": datetime.now().strftime("%H:%M:%S"),
            })
            st.success(f"✅ Generated {len(new_qs)} questions")

if st.session_state.generated_questions:
    st.markdown("### 📋 Generated Questions")

    f1, f2 = st.columns(2)
    with f1:
        filter_topic = st.multiselect(
            "Filter by Topic",
            list(set(q["topic"] for q in st.session_state.generated_questions))
        )
    with f2:
        filter_bloom = st.multiselect("Filter by Bloom Level", BLOOM_LEVELS)

    qs = st.session_state.generated_questions
    if filter_topic: qs = [q for q in qs if q["topic"] in filter_topic]
    if filter_bloom: qs = [q for q in qs if q["bloom_level"] in filter_bloom]

    for i, q in enumerate(qs):
        badge = BADGE_CLASS.get(q["bloom_level"], "badge-remember")
        scenario_preview = q["scenario"][:200] + ("..." if len(q["scenario"]) > 200 else "")
        st.markdown(f"""
        <div class="question-card">
            <div class="q-number">Q{i+1:02d}</div>
            <span class="bloom-badge {badge}">{q['bloom_level']}</span>
            <div style="font-size:0.8rem;color:#64748b;margin-bottom:0.75rem;
                        font-family:'JetBrains Mono',monospace;">🎯 {q['topic']}</div>
            <div class="question-text">{q['question']}</div>
            <div class="scenario-tag"><strong>Scenario:</strong> {scenario_preview}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 📊 Quality Metrics")
    m1,m2,m3,m4,m5 = st.columns(5)
    qt = [q["question"] for q in qs]
    avg_w = round(sum(len(q.split()) for q in qt) / max(len(qt),1), 1)
    all_w = " ".join(qt).lower().split()
    ttr   = round(len(set(all_w)) / max(len(all_w),1), 3)
    bloom_counts = {}
    for q in qs: bloom_counts[q["bloom_level"]] = bloom_counts.get(q["bloom_level"],0)+1
    top_bloom = max(bloom_counts, key=bloom_counts.get) if bloom_counts else "-"

    for col, val, label in [
        (m1, len(qs),       "Total Questions"),
        (m2, avg_w,         "Avg Word Count"),
        (m3, ttr,           "Lexical Diversity"),
        (m4, top_bloom,     "Top Level"),
        (m5, len(set(q["topic"] for q in qs)), "Topics Covered"),
    ]:
        col.markdown(f"""<div class="metric-card">
            <div class="metric-value" style="font-size:{'2rem' if str(val).isdigit() or isinstance(val,float) else '1.3rem'};">{val}</div>
            <div class="metric-label">{label}</div>
        </div>""", unsafe_allow_html=True)

    if st.session_state.history:
        with st.expander("📜 Generation History"):
            for h in reversed(st.session_state.history):
                st.markdown(f"**{h['ts']}** · `{h['topic']}` · `{h['bloom']}` · {h['count']} questions")
else:
    st.markdown("""
    <div style="text-align:center;padding:4rem 2rem;color:#475569;">
        <div style="font-size:4rem;">🧠</div>
        <div style="font-size:1.3rem;font-weight:700;color:#64748b;margin-bottom:0.5rem;">
            No questions generated yet
        </div>
        <div style="font-size:0.95rem;">Select a topic and Bloom level, then click Generate.</div>
    </div>
    """, unsafe_allow_html=True)
