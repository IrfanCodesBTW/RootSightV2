"""
RootSight — Timeline View Component
"""

import streamlit as st


EVENT_TYPE_CONFIG = {
    "deploy":         {"icon": "🚀", "color": "#6366f1", "label": "Deploy"},
    "error_spike":    {"icon": "🔴", "color": "#FF3B30", "label": "Error Spike"},
    "latency_spike":  {"icon": "⚡", "color": "#FF9500", "label": "Latency"},
    "config_change":  {"icon": "⚙️", "color": "#a78bfa", "label": "Config Change"},
    "recovery":       {"icon": "✅", "color": "#30D158", "label": "Recovery"},
    "alert":          {"icon": "🔔", "color": "#FFD60A", "label": "Alert"},
    "cascade":        {"icon": "🌊", "color": "#f97316", "label": "Cascade"},
    "db_failure":     {"icon": "🗄️", "color": "#ef4444", "label": "DB Failure"},
    "network_error":  {"icon": "🌐", "color": "#f59e0b", "label": "Network"},
    "other":          {"icon": "📌", "color": "#64748b", "label": "Event"},
}

SEVERITY_COLOR = {
    "critical": "#FF3B30",
    "high":     "#FF9500",
    "warning":  "#FFD60A",
    "info":     "#94a3b8",
}


def render(brief: dict):
    timeline = brief.get("timeline") or {}
    events = timeline.get("events", [])
    confidence = timeline.get("timeline_confidence", 0)
    gaps = timeline.get("gaps", [])

    st.markdown("""
    <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:16px;">
        <h3 style="margin:0; color:#f1f5f9; font-size:18px; font-weight:700;">⏱️ Incident Timeline</h3>
    </div>
    """, unsafe_allow_html=True)

    # Confidence + event count row
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        conf_color = "#30D158" if confidence >= 70 else "#FFD60A" if confidence >= 40 else "#FF9500"
        st.markdown(f"""
        <div style="background:rgba(30,41,59,0.6); border-radius:10px; padding:12px 16px; border:1px solid rgba(148,163,184,0.1);">
            <div style="color:#94a3b8; font-size:11px; text-transform:uppercase; letter-spacing:0.08em;">Timeline Confidence</div>
            <div style="color:{conf_color}; font-size:28px; font-weight:800; margin-top:4px;">{confidence}%</div>
            <div style="background:rgba(148,163,184,0.1); border-radius:4px; height:4px; margin-top:8px;">
                <div style="background:{conf_color}; width:{confidence}%; height:4px; border-radius:4px; transition:width 0.5s;"></div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div style="background:rgba(30,41,59,0.6); border-radius:10px; padding:12px 16px; border:1px solid rgba(148,163,184,0.1);">
            <div style="color:#94a3b8; font-size:11px; text-transform:uppercase; letter-spacing:0.08em;">Events Found</div>
            <div style="color:#f1f5f9; font-size:28px; font-weight:800; margin-top:4px;">{len(events)}</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        gap_color = "#30D158" if not gaps else "#FFD60A"
        st.markdown(f"""
        <div style="background:rgba(30,41,59,0.6); border-radius:10px; padding:12px 16px; border:1px solid rgba(148,163,184,0.1);">
            <div style="color:#94a3b8; font-size:11px; text-transform:uppercase; letter-spacing:0.08em;">Gaps</div>
            <div style="color:{gap_color}; font-size:28px; font-weight:800; margin-top:4px;">{len(gaps)}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='margin-top:20px;'></div>", unsafe_allow_html=True)

    if not events:
        st.markdown("""
        <div style="text-align:center; padding:40px; color:#64748b;">
            <div style="font-size:32px; margin-bottom:8px;">📭</div>
            <div>No timeline events available</div>
        </div>
        """, unsafe_allow_html=True)
        return

    # Timeline events
    for i, event in enumerate(events):
        evt_type = event.get("event_type", "other")
        cfg = EVENT_TYPE_CONFIG.get(evt_type, EVENT_TYPE_CONFIG["other"])
        sev = event.get("severity", "info")
        sev_color = SEVERITY_COLOR.get(sev, "#94a3b8")
        is_last = i == len(events) - 1

        connector = "" if is_last else f"""
        <div style="width:2px; height:20px; background:linear-gradient(to bottom, {cfg['color']}40, transparent);
                    margin: 0 19px;"></div>
        """

        st.markdown(f"""
        <div style="display:flex; gap:0; align-items:flex-start;">
            <div style="display:flex; flex-direction:column; align-items:center; flex-shrink:0;">
                <div style="
                    width:40px; height:40px; border-radius:50%;
                    background:rgba({','.join(str(int(cfg['color'].lstrip('#')[i:i+2], 16)) for i in (0,2,4))},0.15);
                    border:2px solid {cfg['color']};
                    display:flex; align-items:center; justify-content:center;
                    font-size:16px; flex-shrink:0;
                ">{cfg['icon']}</div>
                {connector}
            </div>
            <div style="
                flex:1; margin-left:16px; margin-bottom: {'8px' if not is_last else '0'};
                background:rgba(30,41,59,0.5);
                border:1px solid rgba(148,163,184,0.1);
                border-left: 3px solid {sev_color};
                border-radius:0 10px 10px 0;
                padding:12px 16px;
            ">
                <div style="display:flex; justify-content:space-between; align-items:flex-start; flex-wrap:wrap; gap:8px;">
                    <div style="display:flex; align-items:center; gap:8px; flex-wrap:wrap;">
                        <span style="
                            background:rgba({','.join(str(int(cfg['color'].lstrip('#')[i:i+2], 16)) for i in (0,2,4))},0.15);
                            color:{cfg['color']}; border-radius:4px; padding:2px 8px;
                            font-size:11px; font-weight:600; text-transform:uppercase; letter-spacing:0.05em;
                        ">{cfg['label']}</span>
                        <span style="color:#64748b; font-size:11px; font-family:monospace;">{event.get('evidence_source', '')}</span>
                    </div>
                    <span style="color:#64748b; font-size:12px; font-family:monospace; white-space:nowrap;">
                        {event.get('timestamp', '')[:19].replace('T', ' ')}
                    </span>
                </div>
                <div style="color:#e2e8f0; font-size:14px; margin-top:6px; line-height:1.5;">
                    {event.get('description', '')}
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Gaps
    if gaps:
        st.markdown("<div style='margin-top:16px'></div>", unsafe_allow_html=True)
        with st.expander(f"⚠️ Timeline Gaps ({len(gaps)})", expanded=False):
            for gap in gaps:
                st.markdown(f"""
                <div style="color:#FFD60A; background:rgba(255,214,10,0.08); border:1px solid rgba(255,214,10,0.2);
                            border-radius:8px; padding:10px 14px; margin-bottom:8px; font-size:13px;">
                    ⚠️ {gap}
                </div>
                """, unsafe_allow_html=True)
