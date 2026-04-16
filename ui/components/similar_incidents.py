"""
RootSight — Similar Incidents Component
"""

import streamlit as st


def render(brief: dict):
    sim_data = brief.get("similar_incidents") or {}
    matches = sim_data.get("matches", [])
    no_match_msg = sim_data.get("no_match_message")

    st.markdown("""
    <h3 style="margin:0 0 16px 0; color:#f1f5f9; font-size:18px; font-weight:700;">
        🧠 Historical Pattern Matching
    </h3>
    """, unsafe_allow_html=True)

    if not matches:
        st.markdown(f"""
        <div style="
            background:rgba(30,41,59,0.5); border:1px solid rgba(148,163,184,0.1);
            border-radius:12px; padding:24px; text-align:center;
        ">
            <div style="font-size:32px; margin-bottom:8px;">🔎</div>
            <div style="color:#94a3b8; font-size:14px;">{no_match_msg or 'No similar incidents found.'}</div>
        </div>
        """, unsafe_allow_html=True)
        return

    for match in matches:
        score = match.get("similarity_score", 0)
        score_pct = int(score * 100)
        applies = match.get("pattern_applies", False)

        score_color = "#30D158" if score_pct >= 75 else "#FFD60A" if score_pct >= 50 else "#94a3b8"
        border_color = "#30D158" if applies else "rgba(148,163,184,0.2)"

        st.markdown(f"""
        <div style="
            background:rgba(15,23,42,0.7); border:1px solid {border_color};
            border-radius:12px; padding:20px; margin-bottom:12px;
        ">
            <div style="display:flex; justify-content:space-between; align-items:flex-start; flex-wrap:wrap; gap:12px; margin-bottom:14px;">
                <div>
                    <div style="display:flex; align-items:center; gap:8px; margin-bottom:6px;">
                        <span style="color:#a5b4fc; font-size:13px; font-family:monospace; background:rgba(99,102,241,0.15);
                                     padding:2px 8px; border-radius:4px;">{match.get('matched_incident_id', '')}</span>
                        {f'<span style="color:#30D158; font-size:12px; background:rgba(48,209,88,0.1); padding:2px 8px; border-radius:4px;">✓ Pattern Applies</span>' if applies else ''}
                    </div>
                    <div style="color:#e2e8f0; font-size:16px; font-weight:600;">{match.get('title', '')}</div>
                </div>
                <div style="text-align:right;">
                    <div style="color:#94a3b8; font-size:11px; text-transform:uppercase; letter-spacing:0.08em;">Similarity</div>
                    <div style="color:{score_color}; font-size:28px; font-weight:800;">{score_pct}%</div>
                    <div style="background:rgba(148,163,184,0.1); border-radius:4px; height:4px; width:80px; margin-top:4px; margin-left:auto;">
                        <div style="background:{score_color}; width:{score_pct}%; height:4px; border-radius:4px;"></div>
                    </div>
                </div>
            </div>
            <div style="color:#94a3b8; font-size:13px; font-style:italic; margin-bottom:14px;">
                🔗 {match.get('similarity_reason', '')}
            </div>
            <div style="display:grid; grid-template-columns:1fr 1fr; gap:12px;">
                <div style="background:rgba(255,59,48,0.08); border:1px solid rgba(255,59,48,0.2); border-radius:8px; padding:12px;">
                    <div style="color:#94a3b8; font-size:11px; text-transform:uppercase; letter-spacing:0.05em; margin-bottom:6px;">Prior Root Cause</div>
                    <div style="color:#fca5a5; font-size:13px; line-height:1.5;">{match.get('previous_root_cause', 'Unknown')}</div>
                </div>
                <div style="background:rgba(48,209,88,0.08); border:1px solid rgba(48,209,88,0.2); border-radius:8px; padding:12px;">
                    <div style="color:#94a3b8; font-size:11px; text-transform:uppercase; letter-spacing:0.05em; margin-bottom:6px;">Prior Resolution</div>
                    <div style="color:#86efac; font-size:13px; line-height:1.5;">{match.get('previous_resolution', 'Unknown')}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
