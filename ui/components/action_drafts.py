"""
RootSight — Action Drafts Component
"""

import streamlit as st


RISK_CONFIG = {
    "low":    {"color": "#30D158", "label": "LOW RISK"},
    "medium": {"color": "#FFD60A", "label": "MED RISK"},
    "high":   {"color": "#FF3B30", "label": "HIGH RISK"},
}


def render(brief: dict):
    actions_data = brief.get("actions") or {}

    st.markdown("""
    <h3 style="margin:0 0 16px 0; color:#f1f5f9; font-size:18px; font-weight:700;">
        🎯 Follow-Up Actions
    </h3>
    """, unsafe_allow_html=True)

    if not actions_data:
        st.markdown("""
        <div style="text-align:center; padding:40px; color:#64748b;">
            <div style="font-size:32px; margin-bottom:8px;">📋</div>
            <div>Actions not available</div>
        </div>
        """, unsafe_allow_html=True)
        return

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "⚡ Immediate Checks",
        "🛡️ Mitigation",
        "📋 Jira Draft",
        "💬 Slack Message",
        "📌 Follow-Up",
    ])

    with tab1:
        checks = actions_data.get("immediate_checks", [])
        if checks:
            for i, check in enumerate(checks, 1):
                st.markdown(f"""
                <div style="
                    background:rgba(30,41,59,0.6); border:1px solid rgba(148,163,184,0.1);
                    border-left:3px solid #6366f1; border-radius:0 10px 10px 0;
                    padding:12px 16px; margin-bottom:10px;
                    display:flex; align-items:flex-start; gap:12px;
                ">
                    <span style="color:#6366f1; font-weight:700; font-size:16px;">{i}.</span>
                    <span style="color:#e2e8f0; font-size:14px; line-height:1.5;">{check}</span>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No immediate checks generated")

    with tab2:
        mitigations = actions_data.get("mitigation", [])
        if mitigations:
            for m in mitigations:
                risk = m.get("risk_level", "medium")
                rcfg = RISK_CONFIG.get(risk, RISK_CONFIG["medium"])
                approval = m.get("approval_required", True)
                st.markdown(f"""
                <div style="
                    background:rgba(30,41,59,0.6); border:1px solid rgba(148,163,184,0.1);
                    border-left:3px solid {rcfg['color']}; border-radius:0 10px 10px 0;
                    padding:16px; margin-bottom:12px;
                ">
                    <div style="display:flex; justify-content:space-between; align-items:flex-start; flex-wrap:wrap; gap:8px; margin-bottom:10px;">
                        <div style="display:flex; gap:8px; align-items:center; flex-wrap:wrap;">
                            <span style="color:{rcfg['color']}; font-size:11px; font-weight:700;
                                         background:{rcfg['color']}20; border:1px solid {rcfg['color']}40;
                                         border-radius:4px; padding:2px 8px;">{rcfg['label']}</span>
                            {('<span style="color:#FF9500; font-size:11px; font-weight:700; background:rgba(255,149,0,0.15); '
                              'border:1px solid rgba(255,149,0,0.3); border-radius:4px; padding:2px 8px;">⚠️ APPROVAL REQUIRED</span>') if approval else ''}
                        </div>
                    </div>
                    <div style="color:#e2e8f0; font-size:14px; font-weight:600; margin-bottom:8px;">{m.get('action', '')}</div>
                    <div style="color:#94a3b8; font-size:13px; font-style:italic;">{m.get('reason', '')}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No mitigation actions generated")

    with tab3:
        jira = actions_data.get("jira_ticket") or {}
        if jira:
            # Styled Jira preview
            priority = jira.get("priority", "High")
            priority_color = "#FF3B30" if priority == "Highest" else "#FF9500" if priority == "High" else "#FFD60A"
            labels = jira.get("labels", [])
            labels_html = " ".join(
                f'<span style="background:rgba(99,102,241,0.15); color:#a5b4fc; border-radius:4px; '
                f'padding:2px 8px; font-size:12px; border:1px solid rgba(99,102,241,0.2);">{l}</span>'
                for l in labels
            )
            st.markdown(f"""
            <div style="
                background:#161b27; border:1px solid rgba(255,255,255,0.1); border-radius:12px; padding:20px;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            ">
                <div style="display:flex; align-items:center; gap:8px; margin-bottom:16px;">
                    <div style="width:8px; height:8px; background:#0052CC; border-radius:2px;"></div>
                    <span style="color:#64748b; font-size:13px;">Jira · {jira.get('project', 'INCIDENT')}</span>
                </div>
                <div style="
                    color:#ffffff; font-size:18px; font-weight:700;
                    margin-bottom:8px; line-height:1.4;
                ">{jira.get('summary', '')}</div>
                <div style="display:flex; gap:12px; align-items:center; flex-wrap:wrap; margin-bottom:16px;">
                    <span style="color:{priority_color}; font-size:12px; font-weight:700;
                                 background:{priority_color}20; border-radius:4px; padding:2px 8px;">⬆ {priority}</span>
                    {f'<span style="color:#94a3b8; font-size:12px;">Assignee: <strong>{jira.get("assignee_suggestion", "")}</strong></span>' if jira.get('assignee_suggestion') else ''}
                </div>
                <div style="color:#cbd5e1; font-size:14px; line-height:1.6; white-space:pre-wrap; margin-bottom:16px;">{jira.get('description', '')}</div>
                <div style="display:flex; gap:6px; flex-wrap:wrap;">{labels_html}</div>
            </div>
            """, unsafe_allow_html=True)

            st.code(jira.get("description", ""), language="markdown")
        else:
            st.info("No Jira ticket draft generated")

    with tab4:
        slack = actions_data.get("slack_message") or {}
        if slack:
            channel = slack.get("channel", "#incidents")
            text = slack.get("text", "")
            st.markdown(f"""
            <div style="
                background:#1a1d21; border:1px solid rgba(255,255,255,0.1); border-radius:12px; padding:20px;
                font-family: 'Slack-Lato', 'appleLogo', sans-serif;
            ">
                <div style="display:flex; align-items:center; gap:8px; margin-bottom:16px;">
                    <div style="width:8px; height:8px; background:#4A154B; border-radius:50%;"></div>
                    <span style="color:#94a3b8; font-size:13px; font-weight:600;">{channel}</span>
                </div>
                <div style="display:flex; gap:12px; align-items:flex-start;">
                    <div style="
                        width:36px; height:36px; background:linear-gradient(135deg, #6366f1, #a78bfa);
                        border-radius:8px; flex-shrink:0; display:flex; align-items:center; justify-content:center;
                        font-size:16px;
                    ">🤖</div>
                    <div>
                        <div style="display:flex; align-items:baseline; gap:8px; margin-bottom:6px;">
                            <span style="color:#e2e8f0; font-weight:700; font-size:15px;">RootSight</span>
                            <span style="color:#64748b; font-size:12px;">just now</span>
                        </div>
                        <div style="color:#e2e8f0; font-size:14px; line-height:1.7; white-space:pre-wrap;">{text}</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            st.code(text, language="text")
        else:
            st.info("No Slack message draft generated")

    with tab5:
        follow_ups = actions_data.get("follow_up", [])
        if follow_ups:
            for i, item in enumerate(follow_ups, 1):
                st.markdown(f"""
                <div style="
                    background:rgba(30,41,59,0.6); border:1px solid rgba(148,163,184,0.1);
                    border-left:3px solid #a78bfa; border-radius:0 10px 10px 0;
                    padding:12px 16px; margin-bottom:10px;
                    display:flex; align-items:flex-start; gap:12px;
                ">
                    <span style="color:#a78bfa; font-weight:700; font-size:16px;">{i}.</span>
                    <span style="color:#e2e8f0; font-size:14px; line-height:1.5;">{item}</span>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No follow-up items generated")
