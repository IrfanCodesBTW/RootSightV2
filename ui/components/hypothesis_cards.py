"""
RootSight — Hypothesis Cards Component
"""

import streamlit as st


def _confidence_color(score: int) -> tuple[str, str]:
    """Returns (color, bg_color) based on confidence score."""
    if score >= 75:
        return "#30D158", "rgba(48,209,88,0.1)"
    elif score >= 50:
        return "#FFD60A", "rgba(255,214,10,0.1)"
    elif score >= 30:
        return "#FF9500", "rgba(255,149,0,0.1)"
    else:
        return "#FF3B30", "rgba(255,59,48,0.1)"


def _rank_badge(rank: int) -> str:
    badges = {1: "🥇 #1", 2: "🥈 #2", 3: "🥉 #3"}
    return badges.get(rank, f"#{rank}")


def render(brief: dict):
    hyp_data = brief.get("hypotheses") or {}
    hypotheses = hyp_data.get("hypotheses", [])
    overall = hyp_data.get("overall_confidence", 0)
    note = hyp_data.get("reasoning_note", "")

    st.markdown("""
    <h3 style="margin:0 0 16px 0; color:#f1f5f9; font-size:18px; font-weight:700;">
        🔍 Root Cause Hypotheses
    </h3>
    """, unsafe_allow_html=True)

    if not hypotheses:
        st.markdown("""
        <div style="text-align:center; padding:40px; color:#64748b;">
            <div style="font-size:32px; margin-bottom:8px;">🔎</div>
            <div>No hypotheses generated</div>
        </div>
        """, unsafe_allow_html=True)
        return

    # Overall confidence banner
    ov_color, ov_bg = _confidence_color(overall)
    st.markdown(f"""
    <div style="
        background:{ov_bg}; border:1px solid {ov_color}40;
        border-radius:10px; padding:12px 16px; margin-bottom:20px;
        display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px;
    ">
        <div>
            <span style="color:#94a3b8; font-size:12px;">ANALYSIS CONFIDENCE</span>
            <span style="color:{ov_color}; font-size:20px; font-weight:800; margin-left:12px;">{overall}%</span>
        </div>
        <div style="color:#94a3b8; font-size:13px; font-style:italic; max-width:60%;">{note}</div>
    </div>
    """, unsafe_allow_html=True)

    for hyp in hypotheses:
        rank = hyp.get("rank", 1)
        confidence = hyp.get("confidence", 0)
        color, bg = _confidence_color(confidence)

        with st.container():
            st.markdown(f"""
            <div style="
                background:rgba(15,23,42,0.7);
                border:1px solid rgba(148,163,184,0.15);
                border-left:4px solid {color};
                border-radius:0 12px 12px 0;
                padding:20px;
                margin-bottom:16px;
            ">
                <div style="display:flex; justify-content:space-between; align-items:flex-start; flex-wrap:wrap; gap:12px; margin-bottom:14px;">
                    <div style="display:flex; align-items:center; gap:10px; flex-wrap:wrap;">
                        <span style="font-size:18px;">{_rank_badge(rank)}</span>
                        <span style="color:#94a3b8; font-size:12px; background:rgba(148,163,184,0.1); padding:2px 8px; border-radius:4px;">
                            RANK {rank}
                        </span>
                    </div>
                    <div style="text-align:right;">
                        <span style="color:{color}; font-size:28px; font-weight:800;">{confidence}%</span>
                        <span style="color:#64748b; font-size:13px; margin-left:4px;">confidence</span>
                    </div>
                </div>
                <div style="
                    background:rgba(148,163,184,0.1); border-radius:4px; height:6px; margin-bottom:14px;
                ">
                    <div style="
                        background:linear-gradient(90deg, {color}aa, {color});
                        width:{confidence}%; height:6px; border-radius:4px;
                    "></div>
                </div>
                <div style="color:#e2e8f0; font-size:16px; font-weight:600; line-height:1.5; margin-bottom:10px;">
                    {hyp.get('statement', '')}
                </div>
                <div style="color:#94a3b8; font-size:13px; font-style:italic; line-height:1.5;">
                    {hyp.get('plausibility', '')}
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Evidence expander
            with st.expander("📋 View Evidence & Details", expanded=(rank == 1)):
                ecol1, ecol2, ecol3 = st.columns(3)

                with ecol1:
                    st.markdown("**✅ Supporting Evidence**")
                    supporting = hyp.get("supporting_evidence", [])
                    if supporting:
                        for item in supporting:
                            st.markdown(f"""
                            <div style="color:#30D158; background:rgba(48,209,88,0.08);
                                        border-left:2px solid #30D158; border-radius:0 6px 6px 0;
                                        padding:6px 10px; margin-bottom:6px; font-size:13px;">
                                {item}
                            </div>
                            """, unsafe_allow_html=True)
                    else:
                        st.markdown("<span style='color:#64748b'>None identified</span>", unsafe_allow_html=True)

                with ecol2:
                    st.markdown("**❌ Contradicting Evidence**")
                    contra = hyp.get("contradicting_evidence", [])
                    if contra:
                        for item in contra:
                            st.markdown(f"""
                            <div style="color:#FF3B30; background:rgba(255,59,48,0.08);
                                        border-left:2px solid #FF3B30; border-radius:0 6px 6px 0;
                                        padding:6px 10px; margin-bottom:6px; font-size:13px;">
                                {item}
                            </div>
                            """, unsafe_allow_html=True)
                    else:
                        st.markdown("<span style='color:#64748b'>None identified</span>", unsafe_allow_html=True)

                with ecol3:
                    st.markdown("**❓ Missing Information**")
                    missing = hyp.get("missing_information", [])
                    if missing:
                        for item in missing:
                            st.markdown(f"""
                            <div style="color:#FFD60A; background:rgba(255,214,10,0.08);
                                        border-left:2px solid #FFD60A; border-radius:0 6px 6px 0;
                                        padding:6px 10px; margin-bottom:6px; font-size:13px;">
                                {item}
                            </div>
                            """, unsafe_allow_html=True)
                    else:
                        st.markdown("<span style='color:#64748b'>None identified</span>", unsafe_allow_html=True)
