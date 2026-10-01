from __future__ import annotations

from pathlib import Path
from typing import Any
import streamlit as st
from neo4j import GraphDatabase, RoutingControl

# ชี้ตำแหน่งโฟลเดอร์ cypher/
CYPHER_DIR = Path(__file__).resolve().parent / "cypher"


def load_cypher(filename: str) -> str:
    """อ่านคำสั่ง Cypher จากไฟล์ในโฟลเดอร์ cypher/"""
    file_path = CYPHER_DIR / filename
    return file_path.read_text(encoding="utf-8")


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


def query(cypher: str, parameters: dict[str, Any] | None = None, *, write: bool = False) -> list[dict[str, Any]]:
    _, _, _, database = _config()
    records, _, _ = get_driver().execute_query(
        cypher,
        parameters_=parameters or {},
        database_=database,
        routing_=RoutingControl.WRITE if write else RoutingControl.READ,
    )
    return [record.data() for record in records]


def ping() -> bool:
    rows = query("RETURN 1 AS ok")
    return bool(rows and rows[0]["ok"] == 1)


def create_schema() -> None:
    """อ่าน schema.cypher แล้วรันคำสั่ง Constraint แต่ละบรรทัด"""
    cypher_text = load_cypher("schema.cypher")
    statements = [stmt.strip() for stmt in cypher_text.split(";") if stmt.strip()]
    for stmt in statements:
        query(stmt, write=True)


def seed_demo_data() -> None:
    create_schema()

    users = [
        {"username": "Alice", "role": "Hardcore Gamer", "level": 45},
        {"username": "Bob", "role": "FPS Enthusiast", "level": 32},
        {"username": "Charlie", "role": "Gacha & RPG Fan", "level": 50},
        {"username": "David", "role": "Survival Specialist", "level": 28},
        {"username": "Emma", "role": "Co-op & Sandbox Lover", "level": 19},
        {"username": "Frank", "role": "Competitive Gamer", "level": 38},
    ]

    games = [
        {"game_name": "Elden Ring", "year": 2022, "image_url": "https://images.unsplash.com/photo-1542751371-adc38448a05e?w=600&auto=format&fit=crop&q=80"},
        {"game_name": "Cyberpunk 2077", "year": 2020, "image_url": "https://images.unsplash.com/photo-1550745165-9bc0b252726f?w=600&auto=format&fit=crop&q=80"},
        {"game_name": "Minecraft", "year": 2011, "image_url": "https://images.unsplash.com/photo-1627856013091-fed6e4e30025?w=600&auto=format&fit=crop&q=80"},
        {"game_name": "Valorant", "year": 2020, "image_url": "https://images.unsplash.com/photo-1511512578047-dfb367046420?w=600&auto=format&fit=crop&q=80"},
        {"game_name": "Genshin Impact", "year": 2020, "image_url": "https://images.unsplash.com/photo-1579373903781-fd5c0c30c4cd?w=600&auto=format&fit=crop&q=80"},
        {"game_name": "Honkai: Star Rail", "year": 2023, "image_url": "https://images.unsplash.com/photo-1538481199705-c710c4e965fc?w=600&auto=format&fit=crop&q=80"},
        {"game_name": "The Witcher 3", "year": 2015, "image_url": "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?w=600&auto=format&fit=crop&q=80"},
        {"game_name": "GTA V", "year": 2013, "image_url": "https://images.unsplash.com/photo-1509198397868-475647b2a1e5?w=600&auto=format&fit=crop&q=80"},
        {"game_name": "Apex Legends", "year": 2019, "image_url": "https://images.unsplash.com/photo-1563089145-599997674d42?w=600&auto=format&fit=crop&q=80"},
        {"game_name": "Project Zomboid", "year": 2013, "image_url": "https://images.unsplash.com/photo-1508739773434-c26b3d09e071?w=600&auto=format&fit=crop&q=80"},
    ]

    developers = [
        {"developer_id": "D01", "name": "FromSoftware"},
        {"developer_id": "D02", "name": "CD Projekt Red"},
        {"developer_id": "D03", "name": "Mojang Studios"},
        {"developer_id": "D04", "name": "Riot Games"},
        {"developer_id": "D05", "name": "HoYoverse"},
    ]

    genres = ["Action RPG", "Open World", "Survival", "FPS", "Sandbox", "Turn-Based RPG"]

    query("UNWIND $rows AS r MERGE (u:User {username: r.username}) SET u.role = r.role, u.level = r.level", {"rows": users}, write=True)
    query("UNWIND $rows AS r MERGE (g:Game {game_name: r.game_name}) SET g.year = r.year, g.image_url = r.image_url", {"rows": games}, write=True)
    query("UNWIND $rows AS r MERGE (d:Developer {developer_id: r.developer_id}) SET d.name = r.name", {"rows": developers}, write=True)
    query("UNWIND $rows AS name MERGE (:Genre {name: name})", {"rows": genres}, write=True)

    friendships = [
        ["Alice", "Bob"], ["Alice", "Charlie"], ["Alice", "David"],
        ["Bob", "Charlie"], ["Bob", "Emma"], ["Charlie", "David"], ["Charlie", "Emma"],
    ]
    query(
        """
        UNWIND $rows AS row
        MATCH (a:User {username: row[0]}), (b:User {username: row[1]})
        MERGE (a)-[:FRIEND_OF]->(b)
        """,
        {"rows": friendships},
        write=True,
    )

    likes = [
        {"u": "Alice", "g": "Elden Ring", "rating": 5.0, "hours": 120},
        {"u": "Alice", "g": "The Witcher 3", "rating": 4.5, "hours": 95},
        {"u": "Alice", "g": "Cyberpunk 2077", "rating": 4.0, "hours": 80},
        {"u": "Bob", "g": "Valorant", "rating": 4.5, "hours": 300},
        {"u": "Bob", "g": "Apex Legends", "rating": 4.0, "hours": 150},
        {"u": "Bob", "g": "GTA V", "rating": 4.0, "hours": 110},
        {"u": "Charlie", "g": "Genshin Impact", "rating": 5.0, "hours": 400},
        {"u": "Charlie", "g": "Honkai: Star Rail", "rating": 5.0, "hours": 210},
        {"u": "Charlie", "g": "Minecraft", "rating": 4.0, "hours": 180},
        {"u": "David", "g": "Elden Ring", "rating": 5.0, "hours": 140},
        {"u": "David", "g": "Project Zomboid", "rating": 4.5, "hours": 90},
        {"u": "Emma", "g": "Minecraft", "rating": 5.0, "hours": 260},
        {"u": "Emma", "g": "Project Zomboid", "rating": 4.0, "hours": 75},
        {"u": "Emma", "g": "Genshin Impact", "rating": 4.0, "hours": 60},
    ]
    query(
        """
        UNWIND $rows AS row
        MATCH (u:User {username: row.u}), (g:Game {game_name: row.g})
        MERGE (u)-[r:LIKES]->(g)
        SET r.rating = row.rating, r.hours_played = row.hours
        """,
        {"rows": likes},
        write=True,
    )

    interests = [
        ["Alice", "Action RPG"], ["Alice", "Open World"],
        ["Bob", "FPS"], ["Bob", "Open World"],
        ["Charlie", "Turn-Based RPG"], ["Charlie", "Open World"],
        ["David", "Survival"], ["David", "Action RPG"],
        ["Emma", "Sandbox"], ["Emma", "Survival"],
    ]
    query(
        """
        UNWIND $rows AS row
        MATCH (u:User {username: row[0]}), (gen:Genre {name: row[1]})
        MERGE (u)-[:INTERESTED_IN]->(gen)
        """,
        {"rows": interests},
        write=True,
    )

    game_genres = [
        ["Elden Ring", "Action RPG"], ["Elden Ring", "Open World"],
        ["Cyberpunk 2077", "Action RPG"], ["Cyberpunk 2077", "Open World"],
        ["Minecraft", "Sandbox"], ["Minecraft", "Survival"],
        ["Valorant", "FPS"], ["Apex Legends", "FPS"],
        ["Genshin Impact", "Action RPG"], ["Genshin Impact", "Open World"],
        ["Honkai: Star Rail", "Turn-Based RPG"],
        ["The Witcher 3", "Action RPG"], ["The Witcher 3", "Open World"],
        ["GTA V", "Open World"], ["Project Zomboid", "Survival"],
    ]
    query(
        """
        UNWIND $rows AS row
        MATCH (g:Game {game_name: row[0]}), (gen:Genre {name: row[1]})
        MERGE (g)-[:IN_GENRE]->(gen)
        """,
        {"rows": game_genres},
        write=True,
    )

    dev_games = [
        ["D01", "Elden Ring"], ["D02", "Cyberpunk 2077"], ["D02", "The Witcher 3"],
        ["D03", "Minecraft"], ["D04", "Valorant"],
        ["D05", "Genshin Impact"], ["D05", "Honkai: Star Rail"],
    ]
    query(
        """
        UNWIND $rows AS row
        MATCH (d:Developer {developer_id: row[0]}), (g:Game {game_name: row[1]})
        MERGE (d)-[:DEVELOPED]->(g)
        """,
        {"rows": dev_games},
        write=True,
    )


def get_users() -> list[dict[str, Any]]:
    return query("MATCH (u:User) RETURN u.username AS username, u.role AS role, u.level AS level ORDER BY u.username")


def get_dashboard_metrics() -> dict[str, int]:
    rows = query(
        """
        MATCH (u:User) WITH count(u) AS users
        MATCH (g:Game) WITH users, count(g) AS games
        MATCH ()-[r:LIKES]->() WITH users, games, count(r) AS likes
        MATCH ()-[f:FRIEND_OF]->()
        RETURN users, games, likes, count(f) AS friendships
        """
    )
    return rows[0] if rows else {"users": 0, "games": 0, "likes": 0, "friendships": 0}


def get_profile(username: str) -> dict[str, Any] | None:
    rows = query(
        """
        MATCH (u:User {username: $username})
        OPTIONAL MATCH (u)-[:INTERESTED_IN]->(gen:Genre)
        OPTIONAL MATCH (u)-[r:LIKES]->(g:Game)
        RETURN u.username AS username, u.role AS role, u.level AS level,
               collect(DISTINCT gen.name) AS interests,
               collect(DISTINCT {game_name: g.game_name, rating: r.rating, hours: r.hours_played}) AS liked_games
        """,
        {"username": username},
    )
    if not rows:
        return None
    row = rows[0]
    row["liked_games"] = [x for x in row["liked_games"] if x.get("game_name")]
    return row


def recommend_games(username: str, limit: int = 6) -> list[dict[str, Any]]:
    """โหลดและรันคำสั่งจาก recommendation.cypher"""
    cypher_text = load_cypher("recommendation.cypher")
    return query(
        cypher_text,
        {"username": username, "limit": int(limit)},
    )


def search_games(keyword: str = "", genre: str | None = None) -> list[dict[str, Any]]:
    return query(
        """
        MATCH (g:Game)
        OPTIONAL MATCH (d:Developer)-[:DEVELOPED]->(g)
        OPTIONAL MATCH (g)-[:IN_GENRE]->(gen:Genre)
        WITH g, collect(DISTINCT d.name) AS developers, collect(DISTINCT gen.name) AS genres
        WHERE (\(keyword = '' OR toLower(g.game_name) CONTAINS toLower(\)keyword))
          AND (\(genre = '' OR\)genre IN genres)
        RETURN g.game_name AS game_name, g.year AS year, g.image_url AS image_url,
               developers, genres
        ORDER BY g.game_name
        """,
        {"keyword": keyword.strip(), "genre": genre or ""},
    )


def list_genres() -> list[str]:
    return [row["name"] for row in query("MATCH (g:Genre) RETURN g.name AS name ORDER BY g.name")]


def record_like(username: str, game_name: str, rating: float, hours: int) -> None:
    query(
        """
        MATCH (u:User {username: \(username}), (g:Game {game_name:\)game_name})
        MERGE (u)-[r:LIKES]->(g)
        SET r.rating = \(rating, r.hours_played =\)hours
        """,
        {"username": username, "game_name": game_name, "rating": rating, "hours": hours},
        write=True,
    )


def graph_neighborhood(username: str, limit: int = 40) -> list[dict[str, Any]]:
    return query(
        """
        MATCH (u:User {username: $username})
        OPTIONAL MATCH p=(u)-[:FRIEND_OF|LIKES|INTERESTED_IN*1..2]-(x)
        WITH u, collect(p)[0..$limit] AS paths
        UNWIND paths AS p
        UNWIND relationships(p) AS r
        WITH DISTINCT startNode(r) AS s, r, endNode(r) AS t
        RETURN elementId(s) AS source_id, labels(s)[0] AS source_label,
               coalesce(s.username, s.game_name, s.name) AS source_name,
               type(r) AS relationship,
               elementId(t) AS target_id, labels(t)[0] AS target_label,
               coalesce(t.username, t.game_name, t.name) AS target_name
        LIMIT $limit
        """,
        {"username": username, "limit": int(limit)},
    )