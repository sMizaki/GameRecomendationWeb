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

st.set_page_config(page_title="GraphGame Recommender", page_icon="🎮", layout="wide")

def require_connection() -> None:
    try:
        if not ping():
            raise RuntimeError()
    except Exception:
        st.error("ยังเชื่อมต่อ Neo4j ไม่สำเร็จ กรุณาตรวจสอบ .streamlit/secrets.toml")
        st.stop()

def user_selector(key: str = "user") -> str:
    users = get_users()
    if not users:
        st.info("ยังไม่มีข้อมูลผู้ใช้ กรุณาไปหน้า Admin / Setup เพื่อสร้างข้อมูลเริ่มต้น")
        st.stop()
    labels = {f"{x['username']} ({x['role']})": x["username"] for x in users}
    return labels[st.selectbox("เลือกผู้ใช้", list(labels), key=key)]

def explain_reason(row: dict) -> str:
    parts = []
    if row.get("friend_count", 0):
        parts.append(f"เพื่อน {row['friend_count']} คนชอบเกมนี้")
    if row.get("genre_matches", 0):
        parts.append(f"ตรงกับแนวเกมที่คุณชอบ ({', '.join(row.get('matched_genres') or [])})")
    if row.get("avg_rating", 0):
        parts.append(f"คะแนนเฉลี่ย {row['avg_rating']:.1f}/5")
    return " • ".join(parts) or "แนะนำจากความนิยมโดยรวม"

require_connection()

with st.sidebar:
    st.markdown("## 🎮 GameGraph")
    page = st.radio("เมนู", ["Dashboard", "Recommendations", "Game Search", "Like Game", "Graph Explorer", "Admin / Setup"])

st.title("🎮 Personalized Game Recommender")

if page == "Dashboard":
    st.subheader("ภาพรวมระบบ")
    m = get_dashboard_metrics()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Users", m.get("users", 0))
    c2.metric("Games", m.get("games", 0))
    c3.metric("Likes", m.get("likes", 0))
    c4.metric("Friendships", m.get("friendships", 0))

    st.divider()
    username = user_selector("dash_user")
    profile = get_profile(username)
    if profile:
        col1, col2 = st.columns([1, 2])
        with col1:
            st.markdown(f"### {profile['username']}")
            st.write(f"**สาย:** {profile['role']} (Lv.{profile['level']})")
            st.write("**แนวเกมที่สนใจ:** " + (", ".join(profile["interests"]) or "ยังไม่ระบุ"))
        with col2:
            st.markdown("### เกมที่เคยกด Like")
            st.dataframe(pd.DataFrame(profile["liked_games"]), use_container_width=True, hide_index=True) if profile["liked_games"] else st.info("ยังไม่มีข้อมูล")

elif page == "Recommendations":
    st.subheader("✨ แนะนำเกมสำหรับคุณ")
    username = user_selector("rec_user")
    top_n = st.slider("จำนวนคำแนะนำ", 2, 8, 4)
    rows = recommend_games(username, top_n)

    if not rows:
        st.info("ยังไม่มีคำแนะนำสำหรับผู้ใช้นี้")
    for i, row in enumerate(rows, start=1):
        col_img, col_info = st.columns([1, 3])
        with col_img:
            st.image(row.get("image_url") or "https://via.placeholder.com/300x200", use_container_width=True)
        with col_info:
            st.markdown(f"**#{i} · {row['game_name']}** ({row['year']}) — Score: `{row['score']:.2f}`")
            st.caption(f"แนวเกม: {', '.join(row.get('genres', []))} | พัฒนาโดย: {', '.join(row.get('developers', []))}")
            st.write(f"💡 **เหตุผล:** {explain_reason(row)}")
        st.divider()

elif page == "Game Search":
    st.subheader("🔎 ค้นหาเกม")
    c1, c2 = st.columns([2, 1])
    keyword = c1.text_input("ค้นหาชื่อเกม")
    genres = [""] + list_genres()
    genre = c2.selectbox("หมวดหมู่แนวเกม", genres, format_func=lambda x: "ทุกแนวเกม" if x == "" else x)
    rows = search_games(keyword, genre)
    st.write(f"พบ {len(rows)} เกม")
    if rows:
        cols = st.columns(3)
        for idx, g in enumerate(rows):
            with cols[idx % 3]:
                st.image(g.get("image_url") or "https://via.placeholder.com/300x200", use_container_width=True)
                st.markdown(f"**{g['game_name']}** ({g['year']})")
                st.caption(f"แนว: {', '.join(g.get('genres', []))}")

elif page == "Like Game":
    st.subheader("📝 บันทึกเกมที่ชอบ")
    username = user_selector("rate_user")
    games = search_games()
    if games:
        game_map = {g["game_name"]: g["game_name"] for g in games}
        selected = st.selectbox("เลือกเกม", list(game_map))
        rating = st.slider("ให้คะแนน", 1.0, 5.0, 4.5, 0.5)
        hours = st.number_input("จำนวนชั่วโมงที่เล่น", 1, 5000, 20)
        if st.button("บันทึก", type="primary", use_container_width=True):
            record_like(username, selected, rating, int(hours))
            st.success("บันทึกความสัมพันธ์ LIKES สำเร็จ")

elif page == "Graph Explorer":
    st.subheader("🕸️ Graph Explorer")
    username = user_selector("graph_user")
    rows = graph_neighborhood(username)
    if not rows:
        st.info("ไม่พบข้อมูลกราฟ")
    else:
        dot = ["digraph G {", 'rankdir="LR";', 'node [shape=box, style="rounded,filled", fillcolor="#f1f5f9"];']
        seen = set()
        for r in rows:
            for nid, label, name in [(r["source_id"], r["source_label"], r["source_name"]), (r["target_id"], r["target_label"], r["target_name"])]:
                if nid not in seen:
                    dot.append(f'"{nid}" [label="{str(name).replace(chr(34), chr(39))}\\n:{label}"];')
                    seen.add(nid)
            dot.append(f'"{r["source_id"]}" -> "{r["target_id"]}" [label="{r["relationship"]}"];')
        dot.append("}")
        st.graphviz_chart("\n".join(dot), use_container_width=True)

elif page == "Admin / Setup":
    st.subheader("⚙️️ Setup ข้อมูลตัวอย่าง")
    if st.button("สร้าง Constraint + Demo Data", type="primary", use_container_width=True):
        with st.spinner("กำลังสร้างข้อมูล..."):
            seed_demo_data()
        st.success("สร้างข้อมูลตัวอย่างเกมสำเร็จ")
        st.rerun()