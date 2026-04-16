"""
RootSight — Impact Panel Component
"""

import streamlit as st


SEVERITY_CONFIG = {
    "P1": {"color": "#FF3B30", "bg": "rgba(255,59,48,0.15)", "label": "P1 — Critical"},
    "P2": {"color": "#FF9500", "bg": "rgba(255,149,0,0.15)", "label": "P2 — High"},
    "P3": {"color": "#FFD60A", "bg": "rgba(255,214,10,0.15)", "label": "P3 — Medium"},
    "P4": {"color": "#30D158", "bg": "rgba(48,209,88,0.15)", "label": "P4 — Low"},
}


def render(brief: dict):
    impact = brief.get("impact") or {}

    st.markdown("""
    <h3 style="margin:0 0 16px 0; color:#f1f5f9; font-size:18px; font-weight:700;">
        💥 Impact Assessment
    </h3>
    """, unsafe_allow_html=True)

    if not impact:
        st.markdown("""
        <div style="text-align:center; padding:40px; color:#64748b;">
            <div style="font-size:32px; margin-bottom:8px;">📊</div>
            <div>Impact assessment not available</div>
        </div>
        """, unsafe_allow_html=True)
        return

    severity = impact.get("severity", "P3")
    cfg = SEVERITY_CONFIG.get(severity, SEVERITY_CONFIG["P3"])

    # Top metrics row
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""
        <div style="background:{cfg['bg']}; border:1px solid {cfg['color']}40; border-radius:12px; padding:16px; text-align:center;">
            <div style="color:#94a3b8; font-size:11px; text-transform:uppercase; letter-spacing:0.08em; margin-bottom:8px;">Severity</div>
            <div style="color:{cfg['color']}; font-size:22px; font-weight:800;">{cfg['label']}</div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        duration = impact.get("estimated_duration_minutes", 0)
        st.markdown(f"""
        <div style="background:rgba(30,41,59,0.6); border:1px solid rgba(148,163,184,0.1); border-radius:12px; padding:16px; text-align:center;">
            <div style="color:#94a3b8; font-size:11px; text-transform:uppercase; letter-spacing:0.08em; margin-bottom:8px;">Duration</div>
            <div style="color:#f1f5f9; font-size:22px; font-weight:800;">~{duration} min</div>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        dtr = impact.get("detection_to_response_minutes", 0)
        st.markdown(f"""
        <div style="background:rgba(30,41,59,0.6); border:1px solid rgba(148,163,184,0.1); border-radius:12px; padding:16px; text-align:center;">
            <div style="color:#94a3b8; font-size:11px; text-transform:uppercase; letter-spacing:0.08em; margin-bottom:8px;">Alert → Response</div>
            <div style="color:#f1f5f9; font-size:22px; font-weight:800;">~{dtr} min</div>
        </div>
        """, unsafe_allow_html=True)
    with c4:
        services = impact.get("affected_services", [])
        st.markdown(f"""
        <div style="background:rgba(30,41,59,0.6); border:1px solid rgba(148,163,184,0.1); border-radius:12px; padding:16px; text-align:center;">
            <div style="color:#94a3b8; font-size:11px; text-transform:uppercase; letter-spacing:0.08em; margin-bottom:8px;">Services Hit</div>
            <div style="color:#f1f5f9; font-size:22px; font-weight:800;">{len(services)}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='margin-top:16px'></div>", unsafe_allow_html=True)

    # Affected services
    if services:
        st.markdown("**🖥️ Affected Services**")
        services_html = " ".join(
            f'<span style="background:rgba(99,102,241,0.15); color:#a5b4fc; border:1px solid rgba(99,102,241,0.3); '
            f'border-radius:6px; padding:4px 10px; font-size:13px; font-family:monospace;">{s}</span>'
            for s in services
        )
        st.markdown(f"<div style='display:flex; gap:8px; flex-wrap:wrap; margin-bottom:16px;'>{services_html}</div>", unsafe_allow_html=True)

    # User impact
    user_impact = impact.get("user_impact") or {}
    biz_impact = impact.get("business_impact") or {}

    col1, col2 = st.columns(2)
    with col1:
        ui_confidence = user_impact.get("confidence", 0)
        ui_color = "#30D158" if ui_confidence >= 70 else "#FFD60A" if ui_confidence >= 40 else "#FF9500"
        st.markdown(f"""
        <div style="background:rgba(30,41,59,0.5); border:1px solid rgba(148,163,184,0.1); border-radius:12px; padding:16px;">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
                <strong style="color:#cbd5e1;">👤 User Impact</strong>
                <span style="color:{ui_color}; font-size:13px; font-weight:700;">{ui_confidence}% confidence</span>
            </div>
            <div style="color:#e2e8f0; font-size:14px; line-height:1.6; margin-bottom:8px;">
                {user_impact.get('description', 'Not assessed')}
            </div>
            {f'<div style="color:#94a3b8; font-size:12px; font-style:italic; border-top:1px solid rgba(148,163,184,0.1); padding-top:8px;">'
             f'⚠️ {user_impact.get("data_limitation", "")}</div>' if user_impact.get('data_limitation') else ''}
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div style="background:rgba(30,41,59,0.5); border:1px solid rgba(148,163,184,0.1); border-radius:12px; padding:16px;">
            <strong style="color:#cbd5e1;">💼 Business Impact</strong>
            <div style="color:#e2e8f0; font-size:14px; line-height:1.6; margin-top:10px; margin-bottom:8px;">
                {biz_impact.get('description', 'Not assessed')}
            </div>
            {f'<div style="background:rgba(99,102,241,0.1); border-radius:6px; padding:8px 12px; font-size:13px; color:#a5b4fc; margin-top:8px;">'
             f'📌 Blast radius: {biz_impact.get("blast_radius", "Unknown")}</div>' if biz_impact.get('blast_radius') else ''}
        </div>
        """, unsafe_allow_html=True)
