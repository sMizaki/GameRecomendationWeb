from __future__ import annotations

from datetime import date
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
    record_play,
    search_games,
    seed_demo_data,
)

st.set_page_config(
    page_title="GraphGame Recommender",
    page_icon="🎮",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
.block-container {padding-top:1.3rem;padding-bottom:2rem;}
.hero {padding:1.4rem 1.6rem;border-radius:22px;background:linear-gradient(120deg,#111827,#1f2937 55%,#0f766e);color:white;margin-bottom:1rem;}
.hero h1 {margin:0;font-size:2.15rem;}
.hero p {opacity:.88;margin:.35rem 0 0;}
.game-card {padding:1rem 1.1rem;border:1px solid rgba(128,128,128,.25);border-radius:16px;margin-bottom:.75rem;}
.score-pill {display:inline-block;padding:.2rem .55rem;border-radius:999px;background:#0f766e;color:white;font-size:.8rem;font-weight:700;}
.muted {opacity:.72;font-size:.9rem;}
</style>
""", unsafe_allow_html=True)


def require_connection():
    try:
        if not ping():
            raise RuntimeError("Neo4j did not return a healthy response")
    except Exception as exc:
        st.error("ยังเชื่อมต่อ Neo4j Aura ไม่สำเร็จ")
        st.code(
            '[neo4j]\nuri = "neo4j+s://YOUR_INSTANCE.databases.neo4j.io"\n'
            'username = "neo4j"\npassword = "YOUR_PASSWORD"\ndatabase = "neo4j"',
            language="toml",
        )
        st.caption("ให้นำค่าไปใส่ใน Streamlit Secrets และห้าม commit password ลง GitHub")
        st.exception(exc)
        st.stop()


def user_selector(key="user"):
    users = get_users()
    if not users:
        st.info("ยังไม่มีข้อมูลผู้ใช้ กรุณาไปหน้า Admin / Setup")
        st.stop()
    labels = {f"{x['user_id']} — {x['name']}": x["user_id"] for x in users}
    chosen = st.selectbox("เลือกเกมเมอร์", list(labels), key=key)
    return labels[chosen]


def explain_reason(row):
    parts = []
    if row.get("friend_count", 0):
        friends = ", ".join(row.get("friend_names") or [])
        parts.append(f"เพื่อน {row['friend_count']} คนเคยเล่น" + (f" ({friends})" if friends else ""))
    if row.get("interest_matches", 0):
        genres = ", ".join(row.get("matched_genres") or [])
        parts.append(f"ตรงกับแนวที่ชอบ {row['interest_matches']} หมวด" + (f" ({genres})" if genres else ""))
    if row.get("popularity", 0):
        parts.append(f"มีคนเล่นแล้ว {row['popularity']} ครั้ง")
    if row.get("avg_rating", 0):
        parts.append(f"คะแนนเฉลี่ย {row['avg_rating']:.2f}/5")
    return " • ".join(parts) or "แนะนำจากแนวโน้มโดยรวมของระบบ"


require_connection()

with st.sidebar:
    st.markdown("## 🎮 GraphGame")
    st.caption("Neo4j Aura + Streamlit")
    page = st.radio(
        "เมนู",
        ["Dashboard", "Recommendations", "Game Search", "Play / Rate", "Graph Explorer", "Admin / Setup"],
    )
    st.divider()
    st.caption("Game Recommendation System")

st.markdown("""
<div class="hero">
<h1>🎮 GraphGame Recommendation System</h1>
<p>ระบบแนะนำเกมด้วย Graph Database พร้อมระบบอธิบายเหตุผลและแสดงภาพประกอบ</p>
</div>
""", unsafe_allow_html=True)


if page == "Dashboard":
    st.subheader("ภาพรวมระบบ")
    m = get_dashboard_metrics()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Users", m.get("users", 0))
    c2.metric("Games", m.get("games", 0))
    c3.metric("Play Records", m.get("plays", 0))
    c4.metric("Friendships", m.get("friendships", 0))
    st.divider()

    user_id = user_selector("dash_user")
    profile = get_profile(user_id)
    if profile:
        left, right = st.columns([1, 2])
        with left:
            st.markdown(f"### {profile['name']}")
            st.write(f"**รหัส:** {profile['user_id']}")
            st.write(f"**แพลตฟอร์มหลัก:** {profile.get('platform', 'N/A')}")
            st.write("**แนวเกมที่ชอบ:** " + (", ".join(profile.get("interests", [])) or "ยังไม่ระบุ"))
        with right:
            st.markdown("### ประวัติการเล่นเกม")
            if profile.get("played"):
                st.dataframe(pd.DataFrame(profile["played"]), use_container_width=True, hide_index=True)
            else:
                st.info("ยังไม่มีประวัติการเล่นเกม")


elif page == "Recommendations":
    st.subheader("✨ เกมที่แนะนำสำหรับคุณ")
    user_id = user_selector("rec_user")
    top_n = st.slider("จำนวนคำแนะนำ", 2, 10, 4)
    rows = recommend_games(user_id, top_n)
    st.caption("น้ำหนักคะแนน = เพื่อนเล่น (×3) + แนวที่ชอบ (×2) + ความนิยม (×0.2) + เรตติ้งเฉลี่ย (×0.5)")

    if not rows:
        st.info("ยังไม่มีคำแนะนำสำหรับผู้ใช้นี้")

    for i, row in enumerate(rows, start=1):
        devs = ", ".join(row.get("developers") or []) or "ไม่ระบุผู้พัฒนา"
        genres = ", ".join(row.get("genres") or []) or "ทั่วไป"
        img_url = row.get("image_url") or "https://via.placeholder.com/300x400?text=No+Cover"

        with st.container():
            col_img, col_info = st.columns([1, 4])
            with col_img:
                st.image(img_url, use_container_width=True)
            with col_info:
                st.markdown(
                    f"""<div class="game-card">
                    <span class="score-pill">#{i} · Score {row.get('score', 0):.2f}</span>
                    <h3 style="margin:.55rem 0 .2rem 0">{row.get('title', 'Unknown Game')}</h3>
                    <div class="muted">ผู้พัฒนา: {devs}<br>แนวเกม: {genres}</div>
                    <p><b>เหตุผลที่แนะนำ:</b> {explain_reason(row)}</p>
                    </div>""",
                    unsafe_allow_html=True,
                )


elif page == "Game Search":
    st.subheader("🔎 ค้นหาเกมในคลัง")
    c1, c2 = st.columns([2, 1])
    keyword = c1.text_input("ชื่อเกมหรือผู้พัฒนา", placeholder="เช่น Elden Ring, FromSoftware")
    genres = [""] + list_genres()
    genre = c2.selectbox("แนวเกม", genres, format_func=lambda x: "ทุกแนว" if x == "" else x)
    rows = search_games(keyword, genre)
    st.write(f"พบ {len(rows)} เกม")
    if rows:
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    else:
        st.info("ไม่พบเกมที่ตรงกับเงื่อนไข")


elif page == "Play / Rate":
    st.subheader("📝 บันทึกประวัติการเล่นและให้คะแนน")
    user_id = user_selector("play_user")
    games = search_games()

    if not games:
        st.info("ยังไม่มีข้อมูลเกมในระบบ")
        st.stop()

    game_labels = {f"{g['game_id']} — {g['title']}": g["game_id"] for g in games}
    selected = st.selectbox("เลือกเกม", list(game_labels))
    play_date = st.date_input("วันที่เล่น", value=date.today())
    use_rating = st.checkbox("ให้คะแนนเกมนี้ด้วย")
    rating = st.slider("คะแนนความพึงพอใจ", 1.0, 5.0, 4.5, 0.5, disabled=not use_rating)

    if st.button("บันทึกประวัติ", type="primary", use_container_width=True):
        record_play(
            user_id,
            game_labels[selected],
            play_date.isoformat(),
            rating if use_rating else None,
        )
        st.success("บันทึกความสัมพันธ์ PLAYED สำเร็จ!")


elif page == "Graph Explorer":
    st.subheader("🕸️ กราฟความสัมพันธ์รอบตัว (Graph Neighborhood)")
    user_id = user_selector("graph_user")
    rows = graph_neighborhood(user_id)

    if not rows:
        st.info("ไม่มีข้อมูลโหนดความสัมพันธ์สำหรับผู้ใช้นี้")
    else:
        dot = [
            "digraph G {",
            'rankdir="LR";',
            'node [shape=box, style="rounded,filled", fillcolor="#f8fafc"];',
        ]
        seen_nodes = set()

        for r in rows:
            for nid, label, name in [
                (r["source_id"], r["source_label"], r["source_name"]),
                (r["target_id"], r["target_label"], r["target_name"]),
            ]:
                if nid not in seen_nodes:
                    safe_name = str(name).replace('"', "'")
                    dot.append(f'"{nid}" [label="{safe_name}\\n:{label}"];')
                    seen_nodes.add(nid)

            dot.append(
                f'"{r["source_id"]}" -> "{r["target_id"]}" '
                f'[label="{r["relationship"]}"];'
            )

        dot.append("}")
        st.graphviz_chart("\n".join(dot), use_container_width=True)

        with st.expander("ดูข้อมูลความสัมพันธ์ (Edges) แบบตาราง"):
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


elif page == "Admin / Setup":
    st.subheader("⚙️ จัดการข้อมูลเริ่มต้น (Demo Data)")
    st.warning("ปุ่มนี้ใช้คำสั่ง MERGE จึงสามารถกดซ้ำได้โดยไม่สร้างข้อมูลซ้ำซ้อน")

    st.markdown("""
    **โครงสร้างกราฟ (Graph Schema):**
    - `(:User)-[:FRIEND_OF]-(:User)`
    - `(:User)-[:PLAYED {play_date, rating}]->(:Game)`
    - `(:User)-[:LIKES_GENRE]->(:Genre)`
    - `(:Game)-[:IN_GENRE]->(:Genre)`
    - `(:Developer)-[:DEVELOPED]->(:Game)`
    """)

    if st.button("สร้าง Constraint + Demo Data (Games)", type="primary", use_container_width=True):
        with st.spinner("กำลังเตรียม Schema และใส่ข้อมูลเกมตัวอย่าง..."):
            seed_demo_data()
        st.success("สร้างข้อมูลจำลองเรียบร้อยแล้ว!")
        st.rerun()
