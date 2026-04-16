"""
RootSight — Incident Header Component
"""

import streamlit as st


SEVERITY_CONFIG = {
    "P1": {"color": "#FF3B30", "bg": "rgba(255,59,48,0.15)", "label": "P1 CRITICAL"},
    "P2": {"color": "#FF9500", "bg": "rgba(255,149,0,0.15)", "label": "P2 HIGH"},
    "P3": {"color": "#FFD60A", "bg": "rgba(255,214,10,0.15)", "label": "P3 MEDIUM"},
    "P4": {"color": "#30D158", "bg": "rgba(48,209,88,0.15)", "label": "P4 LOW"},
}


def render(brief: dict):
    header = brief.get("header") or {}
    severity = header.get("severity", "P3")
    cfg = SEVERITY_CONFIG.get(severity, SEVERITY_CONFIG["P3"])

    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, rgba(99,102,241,0.1) 0%, rgba(168,85,247,0.1) 100%);
        border: 1px solid rgba(99,102,241,0.3);
        border-radius: 16px;
        padding: 24px 28px;
        margin-bottom: 24px;
    ">
        <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 12px;">
            <div>
                <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 8px;">
                    <span style="
                        background: {cfg['bg']};
                        color: {cfg['color']};
                        border: 1px solid {cfg['color']};
                        border-radius: 6px;
                        padding: 4px 12px;
                        font-size: 13px;
                        font-weight: 700;
                        letter-spacing: 0.05em;
                        font-family: 'JetBrains Mono', monospace;
                    ">{cfg['label']}</span>
                    <span style="color: #94a3b8; font-size: 13px; font-family: monospace;">{header.get('incident_id', 'N/A')}</span>
                </div>
                <h2 style="margin: 0 0 8px 0; color: #f1f5f9; font-size: 22px; font-weight: 700; line-height: 1.3;">
                    {header.get('alert_title', 'Unknown Alert')}
                </h2>
                <p style="margin: 0; color: #94a3b8; font-size: 14px;">
                    {header.get('description', '')}
                </p>
            </div>
            <div style="text-align: right; min-width: 200px;">
                <div style="color: #94a3b8; font-size: 12px; margin-bottom: 4px;">PROCESSING TIME</div>
                <div style="color: #f1f5f9; font-size: 20px; font-weight: 700;">{brief.get('processing_time_seconds', 0):.1f}s</div>
                <div style="color: #94a3b8; font-size: 12px; margin-top: 8px;">OVERALL CONFIDENCE</div>
                <div style="color: {'#30D158' if brief.get('overall_confidence',0) >= 70 else '#FFD60A' if brief.get('overall_confidence',0) >= 40 else '#FF9500'}; font-size: 24px; font-weight: 700;">
                    {brief.get('overall_confidence', 0)}%
                </div>
            </div>
        </div>
        <div style="
            display: flex; gap: 20px; margin-top: 16px; padding-top: 16px;
            border-top: 1px solid rgba(148,163,184,0.15); flex-wrap: wrap;
        ">
            <span style="color: #94a3b8; font-size: 13px;">
                🖥️ <strong style="color: #cbd5e1;">Service:</strong> {header.get('service', 'N/A')}
            </span>
            <span style="color: #94a3b8; font-size: 13px;">
                🌍 <strong style="color: #cbd5e1;">Environment:</strong> {header.get('environment', 'production')}
            </span>
            <span style="color: #94a3b8; font-size: 13px;">
                📍 <strong style="color: #cbd5e1;">Region:</strong> {header.get('region', 'N/A')}
            </span>
            <span style="color: #94a3b8; font-size: 13px;">
                🕐 <strong style="color: #cbd5e1;">Alert time:</strong> {header.get('timestamp', 'N/A')}
            </span>
            <span style="color: #94a3b8; font-size: 13px;">
                📡 <strong style="color: #cbd5e1;">Source:</strong> {header.get('source', 'N/A')}
            </span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Agent pipeline status
    agent_status = brief.get("agent_status") or {}
    if isinstance(agent_status, dict):
        cols = st.columns(7)
        agents = ["trigger", "log", "timeline", "rca", "impact", "memory", "action"]
        icons = ["⚡", "📋", "⏱️", "🔍", "💥", "🧠", "🎯"]
        for i, (agent, icon) in enumerate(zip(agents, icons)):
            status = agent_status.get(agent, "pending")
            is_ok = status == "success"
            is_skip = "skipped" in str(status)
            with cols[i]:
                color = "#30D158" if is_ok else "#FFD60A" if is_skip else "#FF3B30"
                dot = "●" if is_ok else "◐" if is_skip else "○"
                st.markdown(f"""
                <div style="text-align:center; padding: 8px 4px;">
                    <div style="font-size: 20px;">{icon}</div>
                    <div style="font-size: 11px; color: #94a3b8; margin: 2px 0;">{agent.upper()}</div>
                    <div style="font-size: 16px; color: {color};">{dot}</div>
                </div>
                """, unsafe_allow_html=True)
