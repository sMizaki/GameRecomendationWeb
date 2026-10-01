MATCH (u:User {user_id:$user_id})
MATCH (g:Game)
WHERE NOT (u)-[:PLAYED]->(g)

// 1) Social signal: เพื่อนเล่นเกมอะไรบ้าง
OPTIONAL MATCH (u)-[:FRIEND_OF]-(f:User)-[:PLAYED]->(g)
WITH u, g,
     count(DISTINCT f) AS friend_count,
     [x IN collect(DISTINCT f.name) WHERE x IS NOT NULL][0..3] AS friend_names

// 2) Content signal: หมวดหมู่เกม (Genre) ที่ตรงกับความสนใจ
OPTIONAL MATCH (u)-[:LIKES_GENRE]->(c:Genre)<-[:IN_GENRE]-(g)
WITH g, friend_count, friend_names,
     count(DISTINCT c) AS interest_matches,
     [x IN collect(DISTINCT c.name) WHERE x IS NOT NULL] AS matched_genres

// 3) Popularity and rating signal: ความนิยมและคะแนน
OPTIONAL MATCH (:User)-[pr:PLAYED]->(g)
WITH g, friend_count, friend_names, interest_matches, matched_genres,
     count(pr) AS popularity,
     coalesce(avg(pr.rating), 0.0) AS avg_rating

// 4) คำนวณคะแนนรวม
WITH g, friend_count, friend_names, interest_matches, matched_genres,
     popularity, avg_rating,
     (friend_count * 3.0) + (interest_matches * 2.0) + (popularity * 0.20) + (avg_rating * 0.50) AS score
WHERE friend_count > 0 OR interest_matches > 0 OR popularity > 0

OPTIONAL MATCH (d:Developer)-[:DEVELOPED]->(g)
OPTIONAL MATCH (g)-[:IN_GENRE]->(allc:Genre)
RETURN g.game_id AS game_id,
       g.title AS title,
       g.image_url AS image_url,
       collect(DISTINCT d.name) AS developers,
       collect(DISTINCT allc.name) AS genres,
       friend_count, friend_names, interest_matches, matched_genres,
       popularity, round(avg_rating * 100) / 100.0 AS avg_rating,
       round(score * 100) / 100.0 AS score
ORDER BY score DESC, g.title
LIMIT $limit;