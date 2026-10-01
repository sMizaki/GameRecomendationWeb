from __future__ import annotations
from typing import Any
import streamlit as st
from neo4j import GraphDatabase, RoutingControl

def _config() -> tuple[str, str, str, str]:
    cfg = st.secrets["neo4j"]
    return (cfg["uri"], cfg["username"], cfg["password"], cfg.get("database", "b9b3be4a"))

@st.cache_resource(show_spinner=False)
def get_driver():
    uri, username, password, _ = _config()
    driver = GraphDatabase.driver(uri, auth=(username, password))
    driver.verify_connectivity()
    return driver

def query(cypher: str, parameters: dict[str, Any] | None = None, *, write: bool = False) -> list[dict[str, Any]]:
    _, _, _, database = _config()
    records, _, _ = get_driver().execute_query(
        cypher, parameters_=parameters or {}, database_=database,
        routing_=RoutingControl.WRITE if write else RoutingControl.READ,
    )
    return [record.data() for record in records]

def ping() -> bool:
    rows = query("RETURN 1 AS ok")
    return bool(rows and rows[0]["ok"] == 1)

def create_schema() -> None:
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

    users = [
        {"user_id": "U001", "name": "Anan", "platform": "PC", "year": 2026},
        {"user_id": "U002", "name": "Mali", "platform": "PlayStation", "year": 2026},
        {"user_id": "U003", "name": "Krit", "platform": "PC", "year": 2025},
        {"user_id": "U004", "name": "Nida", "platform": "Nintendo Switch", "year": 2026},
    ]
    # ใส่ลิงก์ภาพประกอบเกมจำลอง (อาจารย์จะเห็นภาพเกมตอนพรีเซนต์)
    games = [
        {"game_id": "G101", "title": "Stardew Valley", "year": 2016, "image_url": "https://images.igdb.com/igdb/image/upload/t_cover_big/xrpmydnu9rpxvxfjkiu7.jpg"},
        {"game_id": "G102", "title": "Elden Ring", "year": 2022, "image_url": "https://images.igdb.com/igdb/image/upload/t_cover_big/co4jni.jpg"},
        {"game_id": "G103", "title": "Hollow Knight", "year": 2017, "image_url": "https://images.igdb.com/igdb/image/upload/t_cover_big/co8b3e.jpg"},
        {"game_id": "G104", "title": "Overwatch 2", "year": 2022, "image_url": "https://images.igdb.com/igdb/image/upload/t_cover_big/co2k1d.jpg"},
    ]
    developers = [
        {"dev_id": "D01", "name": "ConcernedApe"},
        {"dev_id": "D02", "name": "FromSoftware"},
        {"dev_id": "D03", "name": "Team Cherry"},
        {"dev_id": "D04", "name": "Blizzard"},
    ]
    genres = ["RPG", "Farming Sim", "Action", "Metroidvania", "FPS"]

    query("UNWIND $rows AS row MERGE (u:User {user_id: row.user_id}) SET u.name = row.name, u.platform = row.platform", {"rows": users}, write=True)
    query("UNWIND $rows AS row MERGE (g:Game {game_id: row.game_id}) SET g.title = row.title, g.year = row.year, g.image_url = row.image_url", {"rows": games}, write=True)
    query("UNWIND $rows AS row MERGE (d:Developer {developer_id: row.dev_id}) SET d.name = row.name", {"rows": developers}, write=True)
    query("UNWIND $rows AS name MERGE (:Genre {name:name})", {"rows": genres}, write=True)

    query("UNWIND $rows AS r MATCH (a:User {user_id: r[0]}), (b:User {user_id: r[1]}) MERGE (a)-[:FRIEND_OF]->(b)", {"rows": [["U001", "U002"], ["U001", "U003"], ["U003", "U004"]]}, write=True)
    
    plays = [
        {"u": "U001", "g": "G101", "date": "2026-08-01", "rating": 5.0},
        {"u": "U001", "g": "G103", "date": "2026-08-14", "rating": 4.5},
        {"u": "U002", "g": "G101", "date": "2026-08-05", "rating": 5.0},
        {"u": "U003", "g": "G102", "date": "2026-08-07", "rating": 5.0},
    ]
    query("UNWIND $rows AS row MATCH (u:User {user_id: row.u}), (g:Game {game_id: row.g}) MERGE (u)-[r:PLAYED]->(g) SET r.play_date = date(row.date), r.rating = row.rating", {"rows": plays}, write=True)
    
    query("UNWIND $rows AS r MATCH (u:User {user_id: r[0]}), (c:Genre {name: r[1]}) MERGE (u)-[:LIKES_GENRE]->(c)", {"rows": [["U001", "RPG"], ["U001", "Farming Sim"], ["U002", "Farming Sim"], ["U003", "Action"]]}, write=True)
    query("UNWIND $rows AS r MATCH (g:Game {game_id: r[0]}), (c:Genre {name: r[1]}) MERGE (g)-[:IN_GENRE]->(c)", {"rows": [["G101", "RPG"], ["G101", "Farming Sim"], ["G102", "RPG"], ["G102", "Action"], ["G103", "Metroidvania"], ["G104", "FPS"]]}, write=True)
    query("UNWIND $rows AS r MATCH (d:Developer {developer_id: r[0]}), (g:Game {game_id: r[1]}) MERGE (d)-[:DEVELOPED]->(g)", {"rows": [["D01", "G101"], ["D02", "G102"], ["D03", "G103"], ["D04", "G104"]]}, write=True)

def get_users() -> list[dict[str, Any]]:
    return query("MATCH (u:User) RETURN u.user_id AS user_id, u.name AS name ORDER BY u.user_id")

def get_dashboard_metrics() -> dict[str, int]:
    rows = query("MATCH (u:User) WITH count(u) AS users MATCH (g:Game) WITH users, count(g) AS games MATCH ()-[r:PLAYED]->() WITH users, games, count(r) AS plays MATCH ()-[f:FRIEND_OF]->() RETURN users, games, plays, count(f) AS friendships")
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
    if not rows: return None
    rows[0]["played"] = [x for x in rows[0]["played"] if x.get("game_id")]
    return rows[0]

def recommend_games(user_id: str, limit: int = 8) -> list[dict[str, Any]]:
    # โหลดโค้ด Cypher จากไฟล์ recommendation.cypher มาทำงาน
    with open("cypher/recommendation.cypher", "r", encoding="utf-8") as f:
        cypher_query = f.read()
    return query(cypher_query, {"user_id": user_id, "limit": limit})

def search_games(keyword: str = "", genre: str | None = None) -> list[dict[str, Any]]:
    return query(
        """
        MATCH (g:Game)
        OPTIONAL MATCH (d:Developer)-[:DEVELOPED]->(g)
        OPTIONAL MATCH (g)-[:IN_GENRE]->(c:Genre)
        WITH g, collect(DISTINCT d.name) AS developers, collect(DISTINCT c.name) AS genres
        WHERE (\(keyword = '' OR toLower(g.title) CONTAINS toLower(\)keyword))
          AND (\(genre = '' OR\)genre IN genres)
        RETURN g.game_id AS game_id, g.title AS title, g.year AS year, g.image_url AS image_url, developers, genres
        ORDER BY g.title
        """,
        {"keyword": keyword.strip(), "genre": genre or ""},
    )

def list_genres() -> list[str]:
    return [row["name"] for row in query("MATCH (c:Genre) RETURN c.name AS name ORDER BY c.name")]

def record_play(user_id: str, game_id: str, play_date: str, rating: float | None = None) -> None:
    query(
        """
        MATCH (u:User {user_id:\(user_id}), (g:Game {game_id:\)game_id})
        MERGE (u)-[r:PLAYED]->(g)
        SET r.play_date = date($play_date)
        FOREACH (_ IN CASE WHEN \(rating IS NULL THEN [] ELSE [1] END | SET r.rating =\)rating)
        """,
        {"user_id": user_id, "game_id": game_id, "play_date": play_date, "rating": rating},
        write=True,
    )

def graph_neighborhood(user_id: str, limit: int = 40) -> list[dict[str, Any]]:
    return query(
        """
        MATCH (u:User {user_id:$user_id})
        OPTIONAL MATCH p=(u)-[:FRIEND_OF|PLAYED|LIKES_GENRE*1..2]-(x)
        WITH u, collect(p)[0..$limit] AS paths UNWIND paths AS p UNWIND relationships(p) AS r
        WITH DISTINCT startNode(r) AS s, r, endNode(r) AS t
        RETURN elementId(s) AS source_id, labels(s)[0] AS source_label, coalesce(s.name, s.title, s.user_id, s.game_id) AS source_name,
               type(r) AS relationship, elementId(t) AS target_id, labels(t)[0] AS target_label, coalesce(t.name, t.title, t.user_id, t.game_id) AS target_name
        LIMIT $limit
        """,
        {"user_id": user_id, "limit": limit},
    )