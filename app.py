from __future__ import annotations

import pandas as pd
import streamlit as st

from neo4j_service import (
    get_dashboard_metrics,
    get_profile,
    get_users,
    graph_neighborhood,
    list_genres,
    ping,
    recommend_games,
    record_like,
    search_games,
    seed_demo_data,
)

st.set_page_config(
    page_title="GraphGame Recommender",
    page_icon="🎮",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    
    """,
    unsafe_allow_html=True,
)


def require_connection() -> None:
    try:
        if not ping():
            raise RuntimeError("Neo4j is unreachable")
    except Exception as exc:
        st.error("⚠️️ ยังเชื่อมต่อ Neo4j Aura ไม่สำเร็จ")
        st.code(
            '[neo4j]\nuri = "neo4j+s://YOUR_INSTANCE.databases.neo4j.io"\n'
            'username = "neo4j"\npassword = "YOUR_PASSWORD"\ndatabase = "neo4j"',
            language="toml",
        )
        st.caption("ตั้งค่าใน .streamlit/secrets.toml และห้าม commit password ลง GitHub")
        st.stop()


def user_selector(key: str = "user") -> str:
    users = get_users()
    if not users:
        st.info("ยังไม่มีข้อมูลผู้ใช้ กรุณาไปหน้า Admin / Setup เพื่อสร้างข้อมูลเริ่มต้น")
        st.stop()
    labels = {f"{x['username']} ({x['role']})": x["username"] for x in users}
    chosen = st.selectbox("เลือก User ที่ต้องการวิเคราะห์", list(labels), key=key)
    return labels[chosen]


def explain_reason(row: dict) -> str:
    parts = []
    if row.get("friend_count", 0):
        friends = ", ".join(row.get("friend_names") or [])
        parts.append(f"เพื่อน {row['friend_count']} คนชอบเกมนี้ ({friends})")
    if row.get("genre_matches", 0):
        genres = ", ".join(row.get("matched_genres") or [])
        parts.append(f"ตรงกับแนวเกมที่คุณชอบ ({genres})")
    if row.get("popularity", 0):
        parts.append(f"ความนิยมรวม {row['popularity']} ผู้เล่น")
    if row.get("avg_rating", 0):
        parts.append(f"คะแนนเฉลี่ย {row['avg_rating']:.1f}/5 ⭐")
    return " • ".join(parts) or "แนะนำจากแนวโน้มความนิยมในระบบ"


require_connection()

with st.sidebar:
    st.markdown("## 🎮 GameGraph")
    st.caption("Neo4j Aura + Streamlit Recommender")
    page = st.radio(
        "เมนูระบบ",
        ["Dashboard", "Game Recommendations", "Game Search", "Like / Rate Game", "Graph Explorer", "Admin / Setup"],
    )
    st.divider()
    st.caption("Graph Database Recommendation Engine")

st.markdown(
    """