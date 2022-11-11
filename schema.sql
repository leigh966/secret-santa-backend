DROP TABLE IF EXISTS games;
DROP TABLE IF EXISTS players;
DROP TABLE IF EXISTS games_and_players;
DROP TABLE IF EXISTS groups;

CREATE TABLE groups (
    group_id INTEGER PRIMARY KEY,
    group_name VARCHAR(20) NOT NULL
);

CREATE TABLE games (
    game_id INTEGER PRIMARY KEY,
    draw_date DATE,
    drawn INTEGER DEFAULT FALSE
);

CREATE TABLE players (
    player_id INTEGER PRIMARY KEY,
    password_hash VARCHAR(100) NOT NULL,
    player_name VARCHAR(20) NOT NULL,
    picked_name VARCHAR(20) DEFAULT NULL,
    group_id INTEGER,
    FOREIGN KEY(group_id) REFERENCES groups(group_id)
);

CREATE TABLE games_and_players (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id INTEGER NOT NULL,
    player_id INTEGER NOT NULL,
    FOREIGN KEY(game_id) REFERENCES games(game_id),
    FOREIGN KEY(player_id) REFERENCES players(player_id)
);