"""
RootSight — Main Streamlit Application

Premium dark-themed incident analysis dashboard.
Run: streamlit run ui/app.py
"""

import sys
import json
import time
from pathlib import Path

import streamlit as st

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ui.components import (
    header as header_component,
    timeline_view,
    hypothesis_cards,
    impact_panel,
    similar_incidents,
    action_drafts,
)

# ─────────────────────────────────────────────────────────────────────────────
# Page config (must be first Streamlit call)
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="RootSight — AI Incident Intelligence",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
# Custom CSS
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

/* Root variables */
:root {
    --bg-primary: #0a0f1e;
    --bg-secondary: #0f172a;
    --bg-card: rgba(15, 23, 42, 0.8);
    --border: rgba(148, 163, 184, 0.12);
    --text-primary: #f1f5f9;
    --text-secondary: #94a3b8;
    --accent-primary: #6366f1;
    --accent-purple: #a78bfa;
}

/* App background */
.stApp {
    background: linear-gradient(135deg, #0a0f1e 0%, #0f172a 50%, #0d1529 100%);
    font-family: 'Inter', sans-serif;
}

/* Hide Streamlit branding */
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }
.stDeployButton { display: none; }

/* Sidebar */
[data-testid="stSidebar"] {
    background: rgba(10, 15, 30, 0.95) !important;
    border-right: 1px solid rgba(148, 163, 184, 0.1) !important;
}
[data-testid="stSidebar"] * { color: #cbd5e1 !important; }

/* Buttons */
.stButton > button {
    background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%) !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 10px 24px !important;
    font-weight: 600 !important;
    font-size: 15px !important;
    letter-spacing: 0.02em !important;
    transition: all 0.2s ease !important;
    box-shadow: 0 4px 15px rgba(99, 102, 241, 0.3) !important;
}
.stButton > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 20px rgba(99, 102, 241, 0.45) !important;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    background: rgba(15, 23, 42, 0.8) !important;
    border-radius: 10px !important;
    padding: 4px !important;
    border: 1px solid rgba(148, 163, 184, 0.1) !important;
}
.stTabs [data-baseweb="tab"] {
    color: #94a3b8 !important;
    border-radius: 8px !important;
    font-weight: 500 !important;
}
.stTabs [aria-selected="true"] {
    background: rgba(99, 102, 241, 0.2) !important;
    color: #a5b4fc !important;
}

/* Expanders */
.streamlit-expanderHeader {
    background: rgba(15, 23, 42, 0.6) !important;
    border-radius: 8px !important;
    color: #cbd5e1 !important;
}

/* Progress / spinner */
.stProgress > div > div {
    background: linear-gradient(90deg, #6366f1, #a78bfa) !important;
}

/* Selectbox */
[data-testid="stSelectbox"] > div > div {
    background: rgba(15, 23, 42, 0.8) !important;
    border: 1px solid rgba(148, 163, 184, 0.2) !important;
    color: #f1f5f9 !important;
    border-radius: 8px !important;
}

/* Code blocks */
.stCode {
    background: rgba(10, 15, 30, 0.8) !important;
    border: 1px solid rgba(148, 163, 184, 0.1) !important;
    border-radius: 8px !important;
}

/* Alerts */
.stAlert {
    border-radius: 10px !important;
}

/* Divider */
hr { border-color: rgba(148, 163, 184, 0.1) !important; }

/* Metric widget */
[data-testid="stMetric"] {
    background: rgba(15, 23, 42, 0.6) !important;
    border: 1px solid rgba(148, 163, 184, 0.1) !important;
    border-radius: 12px !important;
    padding: 16px !important;
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# Scenario definitions
# ─────────────────────────────────────────────────────────────────────────────
SCENARIOS = {
    "🔴 Payment Service — Stripe Failure (P1)": {
        "id": "01",
        "description": "High error rate on /api/checkout after deployment v2.14.3. Connection refused to stripe-gateway:443.",
        "scenario_id": "01",
        "webhook_override": None,  # Uses mock/pagerduty_webhook.json
    },
    "🟠 User Service — DB Connection Pool (P2)": {
        "id": "02",
        "description": "Authentication failures due to database connection pool exhausted after config change.",
        "scenario_id": "02",
        "webhook_override": {
            "incident_id": "INC-2024-0901",
            "service": "user-service",
            "alert_title": "High error rate on user authentication — DB connections exhausted",
            "severity": "P2",
            "timestamp": "2024-03-01T16:19:00Z",
            "source": "pagerduty",
            "environment": "production",
            "region": "us-east-1",
            "description": "user-service authentication endpoint returning 504 timeouts. DB connection pool exhausted after config change set max connections to 10.",
            "deploy_markers": [],
        },
    },
    "🟡 Content Delivery — CDN Cache Purge (P1)": {
        "id": "03",
        "description": "CDN full cache purge triggered thundering herd causing origin server overload and site outage.",
        "scenario_id": "03",
        "webhook_override": {
            "incident_id": "INC-2024-0801",
            "service": "content-delivery",
            "alert_title": "CDN origin servers returning 502 — site unavailable",
            "severity": "P1",
            "timestamp": "2024-03-10T10:57:00Z",
            "source": "pagerduty",
            "environment": "production",
            "region": "us-east-1",
            "description": "CDN origin servers at 100% CPU after accidental full cache purge. All edge nodes receiving 502 Bad Gateway. Homepage and static assets unavailable.",
            "deploy_markers": [],
        },
    },
}

# ─────────────────────────────────────────────────────────────────────────────
# Session state initialization
# ─────────────────────────────────────────────────────────────────────────────
if "brief" not in st.session_state:
    st.session_state.brief = None
if "running" not in st.session_state:
    st.session_state.running = False
if "selected_scenario" not in st.session_state:
    st.session_state.selected_scenario = list(SCENARIOS.keys())[0]
if "error_msg" not in st.session_state:
    st.session_state.error_msg = None

# ─────────────────────────────────────────────────────────────────────────────
# Sidebar
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="text-align: center; padding: 20px 0 10px 0;">
        <div style="font-size: 42px; margin-bottom: 8px;">🔍</div>
        <div style="font-size: 22px; font-weight: 800; color: #f1f5f9; letter-spacing: -0.02em;">RootSight</div>
        <div style="font-size: 12px; color: #64748b; margin-top: 4px; letter-spacing: 0.05em;">AI INCIDENT INTELLIGENCE</div>
    </div>
    <hr style="border-color: rgba(148,163,184,0.1); margin: 16px 0;">
    """, unsafe_allow_html=True)

    st.markdown("**📡 Select Demo Scenario**")
    selected_name = st.selectbox(
        "Scenario",
        list(SCENARIOS.keys()),
        index=list(SCENARIOS.keys()).index(st.session_state.selected_scenario),
        label_visibility="collapsed",
    )
    st.session_state.selected_scenario = selected_name
    scenario = SCENARIOS[selected_name]

    # Scenario description
    st.markdown(f"""
    <div style="
        background: rgba(99,102,241,0.08); border: 1px solid rgba(99,102,241,0.2);
        border-radius: 8px; padding: 12px; margin: 12px 0; font-size: 13px; color: #94a3b8;
        line-height: 1.5;
    ">
        {scenario['description']}
    </div>
    """, unsafe_allow_html=True)

    # Trigger button
    trigger_clicked = st.button(
        "⚡ Trigger Incident Analysis",
        use_container_width=True,
        disabled=st.session_state.running,
    )

    st.markdown("<hr style='border-color: rgba(148,163,184,0.1); margin: 20px 0;'>", unsafe_allow_html=True)

    # Status display
    if st.session_state.brief:
        brief = st.session_state.brief
        st.markdown("**📊 Pipeline Status**")
        agent_status = brief.get("agent_status") or {}
        if isinstance(agent_status, dict):
            for agent, status in agent_status.items():
                is_ok = status == "success"
                is_skip = "skipped" in str(status)
                color = "#30D158" if is_ok else "#FFD60A" if is_skip else "#FF3B30"
                dot = "●" if is_ok else "◐" if is_skip else "○"
                st.markdown(f"""
                <div style="display:flex; justify-content:space-between; align-items:center;
                            padding:4px 0; font-size:13px;">
                    <span style="color:#94a3b8;">{agent.upper()}</span>
                    <span style="color:{color};">{dot} {status.split(':')[0].upper()}</span>
                </div>
                """, unsafe_allow_html=True)

    st.markdown("<hr style='border-color: rgba(148,163,184,0.1); margin: 20px 0;'>", unsafe_allow_html=True)
    st.markdown("""
    <div style="font-size: 12px; color: #475569; line-height: 1.6;">
        <strong style="color: #64748b;">RootSight MVP</strong><br>
        Powered by Gemini AI + FAISS<br>
        All actions are drafts only.<br>
        No real API calls are made.
    </div>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# Trigger handler
# ─────────────────────────────────────────────────────────────────────────────
if trigger_clicked:
    st.session_state.running = True
    st.session_state.brief = None
    st.session_state.error_msg = None
    st.rerun()

if st.session_state.running:
    from src.agents.manager_agent import run_pipeline

    # Loading UI
    st.markdown("""
    <div style="text-align: center; padding: 80px 0 40px 0;">
        <div style="font-size: 48px; margin-bottom: 16px;">⚡</div>
        <h2 style="color: #f1f5f9; font-size: 24px; font-weight: 700; margin-bottom: 8px;">
            Analyzing Incident...
        </h2>
        <p style="color: #64748b; font-size: 15px;">Running all 7 agents through the pipeline</p>
    </div>
    """, unsafe_allow_html=True)

    progress_bar = st.progress(0, text="Initializing pipeline...")
    status_text = st.empty()

    steps = [
        (14, "⚡ Trigger Agent — parsing alert..."),
        (28, "📋 Log Agent — fetching and normalizing logs..."),
        (42, "⏱️ Timeline Agent — reconstructing incident timeline..."),
        (57, "🔍 RCA Agent — generating root cause hypotheses..."),
        (71, "💥 Impact Agent — estimating blast radius..."),
        (85, "🧠 Memory Agent — searching historical incidents..."),
        (95, "🎯 Action Agent — drafting follow-up actions..."),
    ]

    def update_progress(step_idx: int):
        pct, msg = steps[step_idx]
        progress_bar.progress(pct, text=msg)
        status_text.markdown(f"<div style='text-align:center; color:#94a3b8; font-size:13px;'>{msg}</div>", unsafe_allow_html=True)

    try:
        scenario = SCENARIOS[st.session_state.selected_scenario]
        payload = scenario.get("webhook_override")
        scenario_id = scenario.get("scenario_id")

        # Simulate staged updates (pipeline runs synchronously)
        update_progress(0)
        brief = run_pipeline(payload=payload, scenario_id=scenario_id)

        progress_bar.progress(100, text="✅ Analysis complete!")
        status_text.empty()

        st.session_state.brief = brief.model_dump()
        st.session_state.running = False
        time.sleep(0.5)
        st.rerun()

    except Exception as e:
        st.session_state.error_msg = str(e)
        st.session_state.running = False
        st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# Error display
# ─────────────────────────────────────────────────────────────────────────────
if st.session_state.error_msg:
    st.error(f"**Pipeline error:** {st.session_state.error_msg}")
    with st.expander("Debug info"):
        st.code(st.session_state.error_msg)

# ─────────────────────────────────────────────────────────────────────────────
# Main content area
# ─────────────────────────────────────────────────────────────────────────────
if st.session_state.brief:
    brief = st.session_state.brief

    # Header
    header_component.render(brief)

    st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

    # Timeline + Hypotheses (side by side on wide screens, stacked on narrow)
    col_left, col_right = st.columns([1, 1], gap="large")

    with col_left:
        with st.container():
            st.markdown("""
            <div style="background: rgba(15,23,42,0.6); border:1px solid rgba(148,163,184,0.1);
                        border-radius:16px; padding:24px; margin-bottom:16px;">
            """, unsafe_allow_html=True)
            timeline_view.render(brief)
            st.markdown("</div>", unsafe_allow_html=True)

    with col_right:
        with st.container():
            st.markdown("""
            <div style="background: rgba(15,23,42,0.6); border:1px solid rgba(148,163,184,0.1);
                        border-radius:16px; padding:24px; margin-bottom:16px;">
            """, unsafe_allow_html=True)
            hypothesis_cards.render(brief)
            st.markdown("</div>", unsafe_allow_html=True)

    # Impact + Similar Incidents
    col_a, col_b = st.columns([1, 1], gap="large")

    with col_a:
        st.markdown("""
        <div style="background: rgba(15,23,42,0.6); border:1px solid rgba(148,163,184,0.1);
                    border-radius:16px; padding:24px; margin-bottom:16px;">
        """, unsafe_allow_html=True)
        impact_panel.render(brief)
        st.markdown("</div>", unsafe_allow_html=True)

    with col_b:
        st.markdown("""
        <div style="background: rgba(15,23,42,0.6); border:1px solid rgba(148,163,184,0.1);
                    border-radius:16px; padding:24px; margin-bottom:16px;">
        """, unsafe_allow_html=True)
        similar_incidents.render(brief)
        st.markdown("</div>", unsafe_allow_html=True)

    # Action Drafts (full width)
    st.markdown("""
    <div style="background: rgba(15,23,42,0.6); border:1px solid rgba(148,163,184,0.1);
                border-radius:16px; padding:24px; margin-bottom:16px;">
    """, unsafe_allow_html=True)
    action_drafts.render(brief)
    st.markdown("</div>", unsafe_allow_html=True)

    # Raw JSON expander
    with st.expander("🗂️ View Raw Incident Brief (JSON)", expanded=False):
        st.json(brief)

else:
    # Landing state
    st.markdown("""
    <div style="
        display: flex; flex-direction: column; align-items: center; justify-content: center;
        padding: 80px 40px;
        text-align: center;
    ">
        <div style="font-size: 72px; margin-bottom: 24px; filter: drop-shadow(0 0 40px rgba(99,102,241,0.5));">🔍</div>
        <h1 style="
            font-size: 42px; font-weight: 800; color: #f1f5f9;
            margin: 0 0 16px 0; letter-spacing: -0.03em;
            background: linear-gradient(135deg, #f1f5f9 0%, #a5b4fc 100%);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        ">RootSight</h1>
        <p style="font-size: 20px; color: #64748b; max-width: 560px; line-height: 1.6; margin: 0 0 48px 0;">
            AI-powered incident understanding. From alert to structured brief in under 3 minutes.
        </p>
        <div style="display: flex; gap: 20px; flex-wrap: wrap; justify-content: center; margin-bottom: 48px;">
            <div style="text-align: center;">
                <div style="font-size: 32px; font-weight: 800; color: #6366f1;">7</div>
                <div style="font-size: 13px; color: #64748b;">AI Agents</div>
            </div>
            <div style="width: 1px; background: rgba(148,163,184,0.2); align-self: stretch;"></div>
            <div style="text-align: center;">
                <div style="font-size: 32px; font-weight: 800; color: #a78bfa;">&lt;3min</div>
                <div style="font-size: 13px; color: #64748b;">Analysis Time</div>
            </div>
            <div style="width: 1px; background: rgba(148,163,184,0.2); align-self: stretch;"></div>
            <div style="text-align: center;">
                <div style="font-size: 32px; font-weight: 800; color: #38bdf8;">100%</div>
                <div style="font-size: 13px; color: #64748b;">Evidence Backed</div>
            </div>
        </div>
        <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; max-width: 800px; width: 100%;">
            <div style="background: rgba(99,102,241,0.08); border: 1px solid rgba(99,102,241,0.2); border-radius: 12px; padding: 20px;">
                <div style="font-size: 24px; margin-bottom: 8px;">⏱️</div>
                <div style="color: #a5b4fc; font-weight: 600; margin-bottom: 4px;">Timeline</div>
                <div style="color: #64748b; font-size: 13px;">Chronological incident reconstruction from logs</div>
            </div>
            <div style="background: rgba(167,139,250,0.08); border: 1px solid rgba(167,139,250,0.2); border-radius: 12px; padding: 20px;">
                <div style="font-size: 24px; margin-bottom: 8px;">🔍</div>
                <div style="color: #c4b5fd; font-weight: 600; margin-bottom: 4px;">Root Cause</div>
                <div style="color: #64748b; font-size: 13px;">Evidence-backed hypotheses with confidence scores</div>
            </div>
            <div style="background: rgba(56,189,248,0.08); border: 1px solid rgba(56,189,248,0.2); border-radius: 12px; padding: 20px;">
                <div style="font-size: 24px; margin-bottom: 8px;">🎯</div>
                <div style="color: #7dd3fc; font-weight: 600; margin-bottom: 4px;">Actions</div>
                <div style="color: #64748b; font-size: 13px;">Jira tickets and Slack messages auto-drafted</div>
            </div>
        </div>
        <p style="color: #475569; font-size: 14px; margin-top: 48px;">
            👈 Select a demo scenario in the sidebar and click <strong style="color: #6366f1;">Trigger Incident Analysis</strong>
        </p>
    </div>
    """, unsafe_allow_html=True)
