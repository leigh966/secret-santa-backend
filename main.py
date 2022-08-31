# Going for a lightweight (no user data saved) approach instead
import sqlite3

import flask
from flask import Flask
from flask_cors import cross_origin, CORS
from secretSantaDbOperations import *

app = Flask(__name__)
cors = CORS(app)

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
    from_expr = get_inner_join_expression("players", "games_and_players", "players.player_id=games_and_players.player_id")
    all_names = select("players.player_name", from_expr, f"game_id={game_id}")
    return {"names": [all_names[i][0] for i in range(0, len(all_names))]}, 200

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