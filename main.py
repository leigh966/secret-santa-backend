# Going for a lightweight (no user data saved) approach instead
import sqlite3

import flask
from flask import Flask
import random
import hashlib
from flask_cors import cross_origin, CORS

from dbOperations import *

app = Flask(__name__)
cors = CORS(app)





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


# DEBUG - ensure to remove in production
@app.route('/start/<game_id>', methods=["POST"])
@cross_origin()
def start_game(game_id):
    LONG_AGO = "01-01-1980 00:00:00"
    command = "UPDATE games " \
              f'SET draw_date = "{LONG_AGO}" ' \
              f'WHERE game_id = "{game_id}";'
    print(command)

    with sqlite3.connect("database.db") as connection:
        connection.execute(command)
        connection.commit()
        return "", 201

def should_game_start(game_id):
    passed_game = select("*", "games", f'game_id={game_id} AND draw_date > datetime("now")')
    if len(passed_game) == 0:
        return True
    return False


def get_picked_name(game_id, name):
    command = 'SELECT picked_name ' \
              'FROM players ' \
              'INNER JOIN games_and_players ' \
              'ON players.player_id=games_and_players.player_id ' \
              f'WHERE player_name="{name}" ' \
              f'AND game_id={game_id};'
    print(command)
    with sqlite3.connect("database.db") as connection:
        picked_names=connection.execute(command).fetchall()
        return picked_names[0][0]

def set_picked_name(game_id, name, picked_name):
    command = 'UPDATE players ' \
              f"SET picked_name = '{picked_name}' " \
              f'WHERE player_id ' \
              f'IN  (SELECT player_id FROM games_and_players WHERE game_id={game_id}) ' \
              f'AND player_name = "{name}";'
    print(command)
    with sqlite3.connect("database.db") as connection:
        connection.execute(command)
        connection.commit()

def mark_drawn(game_id):
    with sqlite3.connect("database.db") as connection:
        connection.execute(f"UPDATE games SET drawn = TRUE WHERE game_id={game_id};")

def randomise_order(arr):
    output=[]
    while len(arr) > 0:
        index = random.randrange(0,len(arr))
        elem = arr.pop(index)
        output.append(elem)
    return output

def draw(game_id):
    command = 'SELECT player_name ' \
              'FROM players ' \
              'INNER JOIN games_and_players ' \
              'ON players.player_id=games_and_players.player_id ' \
              f'WHERE game_id={game_id};'
    names = ()
    print(command)
    with sqlite3.connect("database.db") as connection:
        names=randomise_order(connection.execute(command).fetchall())
        print("names: ", names)
    for index in range(0, len(names)):
        set_picked_name(game_id, names[index][0], names[(index+1)%len(names)][0])

def is_drawn(game_id):
    drawn = select("drawn", "games", f"game_id={game_id}")[0][0]
    return drawn == 1

@app.route('/picked/<game_id>', methods=["POST"])
@cross_origin()
def get_name(game_id):
    json_data = flask.request.json
    name=json_data["name"]
    password=json_data["password"]
    if not authenticate_user(game_id, name, password):
        return "Name and/or password incorrect", 401
    if not should_game_start(game_id):
        return "Not ready to draw", 401
    picked_name = get_picked_name(game_id,name)
    status = 200
    if picked_name == None:
        if is_drawn(game_id):
            return "A name should have been drawn but hasn't. Sorry, we don't know what went wrong", 500
        draw(game_id)
        picked_name = get_picked_name(game_id, name)
        status = 201
    print(picked_name)
    return picked_name, status



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
    if player_exists(name, game_id):
        return "That username is already taken!", 409
    password=json_data["password"]
    if password == "":
        return "No password given", 400
    password_hash = hashlib.sha256(password.encode('utf-8'))
    return create_player(name, password_hash.hexdigest(), game_id)


def game_exists(game_id):
    games_with_id = select("game_id", "games", f"game_id={game_id}")
    return len(games_with_id) > 0

def player_exists(name, game_id):
    command = f"SELECT DISTINCT *" \
              f"FROM players " \
              f"INNER JOIN games_and_players " \
              f"ON players.player_id=games_and_players.player_id " \
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
    return select("draw_date", "games", f"game_id={game_id}")[0][0]


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