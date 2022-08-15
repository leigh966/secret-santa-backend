DROP TABLE IF EXISTS games;
DROP TABLE IF EXISTS players;
DROP TABLE IF EXISTS games_and_players;

CREATE TABLE games (
    game_id INTEGER PRIMARY KEY,
    draw_date DATE
);

CREATE TABLE players (
    player_id INTEGER PRIMARY KEY,
    player_name VARCHAR(20)
);

CREATE TABLE games_and_players (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id INTEGER,
    player_id INTEGER,
    FOREIGN KEY(game_id) REFERENCES games(game_id),
    FOREIGN KEY(player_id) REFERENCES players(player_id)
);