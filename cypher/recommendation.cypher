// Explainable Hybrid Game Recommendation
// Parameters: \(username,\)limit
MATCH (u:User {username: $username})
MATCH (g:Game)
WHERE NOT (u)-[:LIKES]->(g)

// 1) Social signal: เกมที่เพื่อนเล่น/ชอบ
OPTIONAL MATCH (u)-[:FRIEND_OF]-(f:User)-[:LIKES]->(g)
WITH u, g,
     count(DISTINCT f) AS friend_count,
     [x IN collect(DISTINCT f.username) WHERE x IS NOT NULL][0..3] AS friend_names

// 2) Content signal: หมวดแนวเกมตรงกับความสนใจของผู้ใช้
OPTIONAL MATCH (u)-[:INTERESTED_IN]->(gen:Genre)<-[:IN_GENRE]-(g)
WITH g, friend_count, friend_names,
     count(DISTINCT gen) AS genre_matches,
     [x IN collect(DISTINCT gen.name) WHERE x IS NOT NULL] AS matched_genres

// 3) Popularity and rating signal: ความนิยมและเรตติ้งรวมในระบบ
OPTIONAL MATCH (:User)-[r:LIKES]->(g)
WITH g, friend_count, friend_names, genre_matches, matched_genres,
     count(r) AS popularity,
     coalesce(avg(r.rating), 0.0) AS avg_rating

// 4) Hybrid heuristic score calculation
WITH g, friend_count, friend_names, genre_matches, matched_genres,
     popularity, avg_rating,
     (friend_count * 3.0) +
     (genre_matches * 2.0) +
     (popularity * 0.20) +
     (avg_rating * 0.50) AS score
WHERE friend_count > 0 OR genre_matches > 0 OR popularity > 0

OPTIONAL MATCH (d:Developer)-[:DEVELOPED]->(g)
OPTIONAL MATCH (g)-[:IN_GENRE]->(allgen:Genre)
RETURN g.game_name AS game_name,
       g.year AS year,
       g.image_url AS image_url,
       collect(DISTINCT d.name) AS developers,
       collect(DISTINCT allgen.name) AS genres,
       friend_count,
       friend_names,
       genre_matches,
       matched_genres,
       popularity,
       round(avg_rating * 100) / 100.0 AS avg_rating,
       round(score * 100) / 100.0 AS score
ORDER BY score DESC, g.game_name
LIMIT $limit;