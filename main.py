# Going for a lightweight (no user data saved) approach instead
import sqlite3

import flask
from flask import Flask
import random
import hashlib
from flask_cors import cross_origin, CORS

app = Flask(__name__)
cors = CORS(app)
MAX_INT = (2**63)-1

def generate_unique_field(table_name, field_name):
    potential_id = -1
    with sqlite3.connect("database.db") as connection:
        while potential_id < 0 or len(connection.execute("SELECT * FROM "+table_name+" WHERE "+field_name+"='"
                                                         + str(potential_id) + "';").fetchall()) > 0:
            potential_id = random.randint(0, MAX_INT)
    return potential_id

def create_record(table_name,field_name, field_value):
    command = f'INSERT INTO {table_name} ({field_name}) VALUES ({field_value})'
    print(command)
    with sqlite3.connect("database.db") as connection:
        connection.execute(command)


def authenticate_user(game_id,name, password):
    password_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()
    command = f'SELECT DISTINCT players.player_id ' \
              f'FROM games_and_players ' \
              f'INNER JOIN players ' \
              f'ON players.player_id=games_and_players.player_id ' \
              f'WHERE game_id="{game_id}" ' \
              f'AND players.player_name="{name}" ' \
              f'AND players.password_hash="{password_hash}";'
    with sqlite3.connect("database.db") as connection:
        all_results = connection.execute(command).fetchall()
        return len(connection.execute(command).fetchall()) > 0

@app.route('/players/<game_id>', methods=["POST"])
@cross_origin()
def get_all_players(game_id):
    json_data = flask.request.json
    name=json_data["name"]
    password=json_data["password"]
    if not authenticate_user(game_id, name, password):
        return "Name and/or password incorrect", 401
    command = f"SELECT players.player_name " \
              f"FROM players " \
              f"INNER JOIN games_and_players " \
              f"ON players.player_id=games_and_players.player_id " \
              f'WHERE game_id={game_id};'
    with sqlite3.connect("database.db") as connection:
        allNames = connection.execute(command).fetchall()
        return {"names": [allNames[i][0] for i in range(0, len(allNames))]}, 200

@app.route('/register/<game_id>', methods=["POST"])
@cross_origin()
def register_player(game_id):
    if not game_exists(game_id):
        return f"No game with id {game_id}", 404
    json_data = flask.request.json
    name=json_data["name"]
    if name == "":
        return "No name given", 400
    print(name)
    if player_exists(name, game_id):
        return "That username is already taken!", 409
    password=json_data["password"]
    if password == "":
        return "No password given", 400
    print(password)
    password_hash = hashlib.sha256(password.encode('utf-8'))
    return create_player(name, password_hash.hexdigest(), game_id)


def game_exists(game_id):
    command = f"SELECT game_id FROM games WHERE game_id={game_id}"
    with sqlite3.connect("database.db") as connection:
        return len(connection.execute(command).fetchall())>0

def player_exists(name, game_id):
    command = f"SELECT DISTINCT *" \
              f"FROM players,games_and_players " \
              f'WHERE game_id={game_id} AND player_name="{name}";'
    with sqlite3.connect("database.db") as connection:
        return len(connection.execute(command).fetchall())>0

def create_player(name, password_hash, game_id):
    player_id = generate_unique_field("players", "player_id")
    create_record("players", "player_id,player_name,password_hash", f'{player_id},"{name}","{password_hash}"')
    create_record("games_and_players", "game_id,player_id", f'{game_id},{player_id}')
    return "done",201

@app.route('/create-session/self-register', methods=["POST"])
@cross_origin()
def create_session():
    json_data = flask.request.json
    draw_date = json_data["draw"]
    game_id = generate_unique_field("games", "game_id")
    create_record("games","game_id,draw_date",f'{game_id},"{draw_date}"')
    return str(game_id), 201

@app.route('/game/<game_id>/draw_date')
@cross_origin()
def get_draw_date(game_id):
    command = f'SELECT draw_date FROM games WHERE game_id="{game_id}"'
    with sqlite3.connect("database.db") as connection:
        return connection.execute(command).fetchall()[0][0]


@app.route('/session/<session_id>-<user_id>')
@cross_origin()
def session(session_id, user_id):
    with sqlite3.connect("database.db") as connection:
        names_results = connection.execute("SELECT name FROM games WHERE game_id='"+str(session_id)+"';").fetchall()
        names = []
        for names_result in names_results:
            names.append(names_result[0])
        if len(names) > 0:
            return '{"names": '+str(names)+"}", 200
        else:
            return "No Game Found", 400





import init_db

app.run(port=8000)