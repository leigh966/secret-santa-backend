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
def get_picked(game_id):
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


@app.route('/groups/<game_id>')
@cross_origin()
def get_all_groups(game_id):
    from_expr = get_inner_join_expression("groups", "games_and_groups",
                                          "groups.group_id=games_and_groups.group_id")
    all_groups = select("groups.group_id,groups.group_name", from_expr, f"game_id={game_id}")
    json_output = []
    for group in all_groups:
        new_json = {"id": str(group[0]), "name": group[1]}  # fixing rounding error by converting to string
        json_output.append(new_json)
    return {"groups":json_output}, 200



@app.route('/players/<game_id>', methods=["POST"])
@cross_origin()
def get_all_players(game_id):
    json_data = flask.request.json
    name=json_data["name"]
    password=json_data["password"]
    if not authenticate_user(game_id, name, password):
        return "Name and/or password incorrect", 401
    return get_players(game_id), 200

def validate_registration(name, password, game_id):
    if is_drawn(game_id):
        return "The results have already been drawn!", 401
    if name == "":
        return "No name given", 400
    if player_exists(name, game_id):
        return "That username is already taken!", 409
    if password == "":
        return "No password given", 400
    return "", 200

@app.route('/register/<game_id>', methods=["POST"])
@cross_origin()
def register_player(game_id):
    if not game_exists(game_id):
        return f"No game with id {game_id}", 404
    json_data = flask.request.json
    name=json_data["name"]
    password=json_data["password"]
    group_id = json_data["group_id"]
    validation_report = validate_registration(name, password, game_id)
    if validation_report[1] != 200:  # stop and return the report if an error has occurred
        return validation_report

    password_hash = hashlib.sha256(password.encode('utf-8'))
    return create_player(name, password_hash.hexdigest(), game_id, group_id)


@app.route('/create-session/self-register', methods=["POST"])
@cross_origin()
def create_session():
    json_data = flask.request.json
    print(json_data)
    draw_date = json_data["draw"]
    groups = json_data["groups"]
    print(groups)
    game_id = generate_unique_field("games", "game_id")
    for group in groups:
        group_id = generate_unique_field("groups", "group_id")
        create_record("groups", "group_id,group_name", f'{group_id},"{group}"')
        create_record("games_and_groups", "game_id, group_id", f'{game_id}, {group_id}')
    create_record("games","game_id,draw_date",f'{game_id},"{draw_date}"')
    return str(game_id), 201

@app.route('/game/<game_id>/draw_date')
@cross_origin()
def get_draw_date(game_id):
    return select("draw_date", "games", f"game_id={game_id}")[0][0]


import init_db

app.run(port=8000)