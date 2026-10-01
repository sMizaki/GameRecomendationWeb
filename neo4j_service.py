from __future__ import annotations

from pathlib import Path
from typing import Any
import streamlit as st
from neo4j import GraphDatabase, RoutingControl

CYPHER_DIR = Path(__file__).resolve().parent / "cypher"


def _config() -> tuple[str, str, str, str]:
    cfg = st.secrets["neo4j"]
    return (
        cfg["uri"],
        cfg["username"],
        cfg["password"],
        cfg.get("database", "b9b3be4a"),
    )


@st.cache_resource(show_spinner=False)
def get_driver():
    uri, username, password, _ = _config()
    driver = GraphDatabase.driver(uri, auth=(username, password))
    driver.verify_connectivity()
    return driver


def query(
    cypher: str, parameters: dict[str, Any] | None = None, *, write: bool = False
) -> list[dict[str, Any]]:
    _, _, _, database = _config()
    clean_cypher = cypher.replace("\u00a0", " ").strip().rstrip(";")

    try:
        records, _, _ = get_driver().execute_query(
            clean_cypher,
            parameters_=parameters or {},
            database_=database,
            routing_=RoutingControl.WRITE if write else RoutingControl.READ,
        )
        return [record.data() for record in records]
    except Exception as exc:
        st.error(f"❌ Neo4j Cypher Error: {exc}")
        st.code(clean_cypher, language="cypher")
        raise exc

def ping() -> bool:
    rows = query("RETURN 1 AS ok")
    return bool(rows and rows[0]["ok"] == 1)


def create_schema() -> None:
    schema_file = CYPHER_DIR / "schema.cypher"
    if schema_file.exists():
        statements = [
            s.strip() for s in schema_file.read_text(encoding="utf-8").split(";") if s.strip()
        ]
        for stmt in statements:
            query(stmt, write=True)
    else:
        statements = [
            "CREATE CONSTRAINT user_id_unique IF NOT EXISTS FOR (u:User) REQUIRE u.user_id IS UNIQUE",
            "CREATE CONSTRAINT game_id_unique IF NOT EXISTS FOR (g:Game) REQUIRE g.game_id IS UNIQUE",
            "CREATE CONSTRAINT dev_id_unique IF NOT EXISTS FOR (d:Developer) REQUIRE d.developer_id IS UNIQUE",
            "CREATE CONSTRAINT genre_unique IF NOT EXISTS FOR (g:Genre) REQUIRE g.name IS UNIQUE",
        ]
        for stmt in statements:
            query(stmt, write=True)


def seed_demo_data() -> None:
    create_schema()

    # 1. ข้อมูลผู้ใช้ 10 คน (Alice - Jack)
    users = [
        {"user_id": "U001", "name": "Alice", "platform": "PC", "year": 2026},
        {"user_id": "U002", "name": "Bob", "platform": "PC", "year": 2026},
        {"user_id": "U003", "name": "Charlie", "platform": "PlayStation 5", "year": 2025},
        {"user_id": "U004", "name": "David", "platform": "PC", "year": 2026},
        {"user_id": "U005", "name": "Emma", "platform": "Nintendo Switch", "year": 2025},
        {"user_id": "U006", "name": "Frank", "platform": "PC", "year": 2026},
        {"user_id": "U007", "name": "Grace", "platform": "PlayStation 5", "year": 2024},
        {"user_id": "U008", "name": "Henry", "platform": "Xbox Series X", "year": 2025},
        {"user_id": "U009", "name": "Ivy", "platform": "PC", "year": 2026},
        {"user_id": "U010", "name": "Jack", "platform": "PC", "year": 2024},
    ]

    # 2. ข้อมูลเกม 10 เกม พร้อมลิงก์รูปภาพปก
    games = [
        {
            "game_id": "G101",
            "title": "Elden Ring",
            "year": 2022,
            "image_url": "https://images.igdb.com/igdb/image/upload/t_cover_big/co4jni.jpg",
        },
        {
            "game_id": "G102",
            "title": "Cyberpunk 2077",
            "year": 2020,
            "image_url": "https://images.igdb.com/igdb/image/upload/t_cover_big/co2mvt.jpg",
        },
        {
            "game_id": "G103",
            "title": "Minecraft",
            "year": 2011,
            "image_url": "https://images.igdb.com/igdb/image/upload/t_cover_big/co8436.jpg",
        },
        {
            "game_id": "G104",
            "title": "Valorant",
            "year": 2020,
            "image_url": "https://images.igdb.com/igdb/image/upload/t_cover_big/co2b5x.jpg",
        },
        {
            "game_id": "G105",
            "title": "Genshin Impact",
            "year": 2020,
            "image_url": "https://images.igdb.com/igdb/image/upload/t_cover_big/co2a05.jpg",
        },
        {
            "game_id": "G106",
            "title": "Honkai: Star Rail",
            "year": 2023,
            "image_url": "https://images.igdb.com/igdb/image/upload/t_cover_big/co6b79.jpg",
        },
        {
            "game_id": "G107",
            "title": "The Witcher 3",
            "year": 2015,
            "image_url": "https://images.igdb.com/igdb/image/upload/t_cover_big/co1wyy.jpg",
        },
        {
            "game_id": "G108",
            "title": "GTA V",
            "year": 2013,
            "image_url": "https://images.igdb.com/igdb/image/upload/t_cover_big/co1x77.jpg",
        },
        {
            "game_id": "G109",
            "title": "Apex Legends",
            "year": 2019,
            "image_url": "https://images.igdb.com/igdb/image/upload/t_cover_big/co2k1e.jpg",
        },
        {
            "game_id": "G110",
            "title": "Project Zomboid",
            "year": 2013,
            "image_url": "https://images.igdb.com/igdb/image/upload/t_cover_big/co1ybs.jpg",
        },
    ]

    developers = [
        {"dev_id": "D01", "name": "FromSoftware"},
        {"dev_id": "D02", "name": "CD Projekt Red"},
        {"dev_id": "D03", "name": "Mojang Studios"},
        {"dev_id": "D04", "name": "Riot Games"},
        {"dev_id": "D05", "name": "HoYoverse"},
        {"dev_id": "D06", "name": "Rockstar Games"},
        {"dev_id": "D07", "name": "Respawn Entertainment"},
        {"dev_id": "D08", "name": "The Indie Stone"},
    ]

    genres = ["Action RPG", "Open World", "Survival", "FPS", "Sandbox", "Turn-Based RPG"]

    # บันทึกโหนดพื้นฐาน
    query(
        "UNWIND $rows AS row MERGE (u:User {user_id: row.user_id}) SET u.name = row.name, u.platform = row.platform, u.year = row.year",
        {"rows": users},
        write=True,
    )
    query(
        "UNWIND $rows AS row MERGE (g:Game {game_id: row.game_id}) SET g.title = row.title, g.year = row.year, g.image_url = row.image_url",
        {"rows": games},
        write=True,
    )
    query(
        "UNWIND $rows AS row MERGE (d:Developer {developer_id: row.dev_id}) SET d.name = row.name",
        {"rows": developers},
        write=True,
    )
    query(
        "UNWIND $rows AS name MERGE (:Genre {name: name})",
        {"rows": genres},
        write=True,
    )

    # 3. โครงข่ายเพื่อน (Friendships)
    friendships = [
        ["U001", "U002"],  # Alice - Bob
        ["U001", "U003"],  # Alice - Charlie
        ["U001", "U004"],  # Alice - David
        ["U002", "U003"],  # Bob - Charlie
        ["U002", "U005"],  # Bob - Emma
        ["U003", "U004"],  # Charlie - David
        ["U004", "U006"],  # David - Frank
        ["U005", "U007"],  # Emma - Grace
        ["U006", "U008"],  # Frank - Henry
        ["U007", "U009"],  # Grace - Ivy
        ["U008", "U010"],  # Henry - Jack
    ]
    query(
        "UNWIND $rows AS r MATCH (a:User {user_id: r[0]}), (b:User {user_id: r[1]}) MERGE (a)-[:FRIEND_OF]->(b)",
        {"rows": friendships},
        write=True,
    )

    # 4. ประวัติการเล่น (PLAYED) ออกแบบให้เพื่อนของ Alice เล่นเกมร่วมกันเพื่อไม่ให้แต้มเสมอ
    # Alice (U001) เคยเล่น: Elden Ring (G101), The Witcher 3 (G107)
    plays = [
        {"u": "U001", "g": "G101", "date": "2026-08-01", "rating": 5.0}, # Alice: Elden Ring
        {"u": "U001", "g": "G107", "date": "2026-08-10", "rating": 4.5}, # Alice: The Witcher 3

        # เพื่อนของ Alice: Bob (U002), Charlie (U003), David (U004)
        {"u": "U002", "g": "G103", "date": "2026-08-02", "rating": 4.5}, # Bob: Minecraft
        {"u": "U002", "g": "G104", "date": "2026-08-05", "rating": 4.0}, # Bob: Valorant
        {"u": "U002", "g": "G108", "date": "2026-08-12", "rating": 4.0}, # Bob: GTA V

        {"u": "U003", "g": "G103", "date": "2026-08-03", "rating": 5.0}, # Charlie: Minecraft (เพื่อนชอบซ้ำคนที่ 2!)
        {"u": "U003", "g": "G105", "date": "2026-08-08", "rating": 5.0}, # Charlie: Genshin Impact
        {"u": "U003", "g": "G106", "date": "2026-08-15", "rating": 4.5}, # Charlie: Honkai: Star Rail

        {"u": "U004", "g": "G103", "date": "2026-08-04", "rating": 5.0}, # David: Minecraft (เพื่อนชอบซ้ำคนที่ 3!)
        {"u": "U004", "g": "G110", "date": "2026-08-09", "rating": 4.5}, # David: Project Zomboid
        {"u": "U004", "g": "G102", "date": "2026-08-14", "rating": 4.0}, # David: Cyberpunk 2077

        # ผู้เล่นคนอื่นๆ ช่วยเพิ่มคะแนน Popularity ทั่วไป
        {"u": "U005", "g": "G103", "date": "2026-08-06", "rating": 5.0}, # Emma: Minecraft
        {"u": "U005", "g": "G110", "date": "2026-08-11", "rating": 4.0}, # Emma: Project Zomboid
        {"u": "U006", "g": "G104", "date": "2026-08-07", "rating": 4.5}, # Frank: Valorant
        {"u": "U006", "g": "G109", "date": "2026-08-13", "rating": 4.0}, # Frank: Apex Legends
        {"u": "U007", "g": "G105", "date": "2026-08-08", "rating": 4.5}, # Grace: Genshin Impact
        {"u": "U008", "g": "G108", "date": "2026-08-09", "rating": 4.5}, # Henry: GTA V
        {"u": "U009", "g": "G106", "date": "2026-08-10", "rating": 4.0}, # Ivy: Honkai: Star Rail
        {"u": "U010", "g": "G109", "date": "2026-08-11", "rating": 4.5}, # Jack: Apex Legends
    ]
    query(
        "UNWIND $rows AS row MATCH (u:User {user_id: row.u}), (g:Game {game_id: row.g}) MERGE (u)-[r:PLAYED]->(g) SET r.play_date = date(row.date), r.rating = row.rating",
        {"rows": plays},
        write=True,
    )

    # 5. ความชอบแนวเกมของผู้ใช้ (LIKES_GENRE)
    interests = [
        ["U001", "Action RPG"], ["U001", "Open World"], ["U001", "Sandbox"],  # Alice
        ["U002", "FPS"], ["U002", "Open World"],
        ["U003", "Turn-Based RPG"], ["U003", "Open World"], ["U003", "Sandbox"],
        ["U004", "Survival"], ["U004", "Action RPG"],
        ["U005", "Sandbox"], ["U005", "Survival"],
        ["U006", "FPS"], ["U007", "Open World"],
        ["U008", "Open World"], ["U009", "Turn-Based RPG"], ["U010", "FPS"],
    ]
    query(
        "UNWIND $rows AS r MATCH (u:User {user_id: r[0]}), (c:Genre {name: r[1]}) MERGE (u)-[:LIKES_GENRE]->(c)",
        {"rows": interests},
        write=True,
    )

    # 6. หมวดหมู่แนวเกมของแต่ละเกม (IN_GENRE)
    game_genres = [
        ["G101", "Action RPG"], ["G101", "Open World"],
        ["G102", "Action RPG"], ["G102", "Open World"],
        ["G103", "Sandbox"], ["G103", "Survival"], ["G103", "Open World"],
        ["G104", "FPS"],
        ["G105", "Action RPG"], ["G105", "Open World"],
        ["G106", "Turn-Based RPG"],
        ["G107", "Action RPG"], ["G107", "Open World"],
        ["G108", "Open World"],
        ["G109", "FPS"],
        ["G110", "Survival"], ["G110", "Open World"],
    ]
    query(
        "UNWIND $rows AS r MATCH (g:Game {game_id: r[0]}), (c:Genre {name: r[1]}) MERGE (g)-[:IN_GENRE]->(c)",
        {"rows": game_genres},
        write=True,
    )

    # 7. ค่ายผู้พัฒนา (DEVELOPED)
    dev_games = [
        ["D01", "G101"],  # FromSoftware -> Elden Ring
        ["D02", "G102"],  # CD Projekt Red -> Cyberpunk 2077
        ["D03", "G103"],  # Mojang Studios -> Minecraft
        ["D04", "G104"],  # Riot Games -> Valorant
        ["D05", "G105"],  # HoYoverse -> Genshin Impact
        ["D05", "G106"],  # HoYoverse -> Honkai: Star Rail
        ["D02", "G107"],  # CD Projekt Red -> The Witcher 3
        ["D06", "G108"],  # Rockstar Games -> GTA V
        ["D07", "G109"],  # Respawn Entertainment -> Apex Legends
        ["D08", "G110"],  # The Indie Stone -> Project Zomboid
    ]
    query(
        "UNWIND $rows AS r MATCH (d:Developer {developer_id: r[0]}), (g:Game {game_id: r[1]}) MERGE (d)-[:DEVELOPED]->(g)",
        {"rows": dev_games},
        write=True,
    )

def get_users() -> list[dict[str, Any]]:
    return query(
        "MATCH (u:User) RETURN u.user_id AS user_id, u.name AS name ORDER BY u.user_id"
    )


def get_dashboard_metrics() -> dict[str, int]:
    rows = query(
        """
        MATCH (u:User) WITH count(u) AS users
        MATCH (g:Game) WITH users, count(g) AS games
        MATCH ()-[r:PLAYED]->() WITH users, games, count(r) AS plays
        MATCH ()-[f:FRIEND_OF]->()
        RETURN users, games, plays, count(f) AS friendships
        """
    )
    return rows[0] if rows else {"users": 0, "games": 0, "plays": 0, "friendships": 0}


def get_profile(user_id: str) -> dict[str, Any] | None:
    rows = query(
        """
        MATCH (u:User {user_id:$user_id})
        OPTIONAL MATCH (u)-[:LIKES_GENRE]->(c:Genre)
        OPTIONAL MATCH (u)-[:PLAYED]->(g:Game)
        RETURN u.user_id AS user_id, u.name AS name, u.platform AS platform,
               collect(DISTINCT c.name) AS interests,
               collect(DISTINCT {game_id:g.game_id, title:g.title}) AS played
        """,
        {"user_id": user_id},
    )
    if not rows:
        return None
    rows[0]["played"] = [x for x in rows[0]["played"] if x.get("game_id")]
    return rows[0]


def recommend_games(user_id: str, limit: int = 8) -> list[dict[str, Any]]:
    query_file = CYPHER_DIR / "recommendation.cypher"
    cypher_query = query_file.read_text(encoding="utf-8")
    return query(cypher_query, {"user_id": user_id, "limit": int(limit)})


def search_games(keyword: str = "", genre: str | None = None) -> list[dict[str, Any]]:
    clean_kw = (keyword or "").strip().lower()
    clean_genre = (genre or "").strip()

    cypher = """
    MATCH (g:Game)
    OPTIONAL MATCH (d:Developer)-[:DEVELOPED]->(g)
    OPTIONAL MATCH (g)-[:IN_GENRE]->(c:Genre)
    WITH g, collect(DISTINCT d.name) AS developers, collect(DISTINCT c.name) AS genres
    """
    conditions = []
    params = {}

    if clean_kw:
        conditions.append(
            "(toLower(g.title) CONTAINS \(keyword OR any(dev IN developers WHERE toLower(dev) CONTAINS\)keyword))"
        )
        params["keyword"] = clean_kw

    if clean_genre:
        conditions.append("$genre IN genres")
        params["genre"] = clean_genre

    if conditions:
        cypher += " WHERE " + " AND ".join(conditions)

    cypher += """
    RETURN g.game_id AS game_id, g.title AS title, g.year AS year, g.image_url AS image_url, developers, genres
    ORDER BY g.title ASC
    """
    return query(cypher, params)


def list_genres() -> list[str]:
    return [row["name"] for row in query("MATCH (c:Genre) RETURN c.name AS name ORDER BY c.name")]


def record_play(
    user_id: str, game_id: str, play_date: str, rating: float | None = None
) -> None:
    cypher = """
    MATCH (u:User {user_id: $user_id})
    MATCH (g:Game {game_id: $game_id})
    MERGE (u)-[r:PLAYED]->(g)
    SET r.play_date = date($play_date)
    """
    params = {"user_id": user_id, "game_id": game_id, "play_date": play_date}

    if rating is not None:
        cypher += "\nSET r.rating = $rating"
        params["rating"] = float(rating)

    query(cypher, params, write=True)


def graph_neighborhood(user_id: str, limit: int = 40) -> list[dict[str, Any]]:
    return query(
        """
        MATCH (u:User {user_id:$user_id})
        OPTIONAL MATCH p=(u)-[:FRIEND_OF|PLAYED|LIKES_GENRE*1..2]-(x)
        WITH u, collect(p)[0..$limit] AS paths
        UNWIND paths AS p
        UNWIND relationships(p) AS r
        WITH DISTINCT startNode(r) AS s, r, endNode(r) AS t
        RETURN elementId(s) AS source_id, labels(s)[0] AS source_label, coalesce(s.name, s.title, s.user_id, s.game_id) AS source_name,
               type(r) AS relationship, elementId(t) AS target_id, labels(t)[0] AS target_label, coalesce(t.name, t.title, t.user_id, t.game_id) AS target_name
        LIMIT $limit
        """,
        {"user_id": user_id, "limit": limit},
    )