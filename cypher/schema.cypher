CREATE CONSTRAINT user_username_unique IF NOT EXISTS
FOR (u:User) REQUIRE u.username IS UNIQUE;

CREATE CONSTRAINT game_name_unique IF NOT EXISTS
FOR (g:Game) REQUIRE g.game_name IS UNIQUE;

CREATE CONSTRAINT developer_id_unique IF NOT EXISTS
FOR (d:Developer) REQUIRE d.developer_id IS UNIQUE;

CREATE CONSTRAINT genre_name_unique IF NOT EXISTS
FOR (gen:Genre) REQUIRE gen.name IS UNIQUE;