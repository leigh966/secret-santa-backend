# Going for a lightweight (no user data saved) approach instead
import flask
from flask import Flask
from flask_cors import cross_origin, CORS
from secretSantaDbOperations import *
from db import db
from db_config import *
from Models.Game import Game
import uuid
from datetime import datetime


app = Flask(__name__)
cors = CORS(app)
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ["DATABASE_URL"]
db.init_app(app)

# DEBUG - ensure to remove in production
@app.route('/start/<game_id>', methods=["POST"])
@cross_origin()
def start_game(game_id):
    LONG_AGO = "01-01-1980 00:00:00"
    command = "UPDATE games " \
              f'SET draw_date = \'{LONG_AGO}\' ' \
              f'WHERE game_id = \'{game_id}\';'
    execute(command)
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
    all_groups = db.session.query(Group).filter(Group.game_id==game_id).all()
    json_output = []
    for group in all_groups:
        new_json = {"id": str(group.group_id), "name": group.group_name}  # fixing rounding error by converting to string
        json_output.append(new_json)
    return {"groups":json_output}, 200



@app.route('/players/<game_id>', methods=["POST"])
@cross_origin()
def get_all_players(game_id):
    json_data = flask.request.json
    name=json_data["name"]
    password=json_data["password"]
    if not authenticate_user(game_id, name, password, db.session):
        return "Name and/or password incorrect", 401
    return get_players(game_id, db.session), 200

def validate_registration(name, password, game_id, db):
    if is_drawn(game_id, db):
        return "The results have already been drawn!", 401
    if name == "":
        return "No name given", 400
    if player_exists(name, game_id, db.session):
        return "That username is already taken!", 409
    if password == "": # should probably make some password rules? nothing crazy just sanity stuff
        return "No password given", 400
    return "", 200

@app.route('/register/<game_id>', methods=["POST"])
@cross_origin()
def register_player(game_id):
    db.get_or_404(Game, game_id, description="Game does not exist")
    json_data = flask.request.json
    name=json_data["name"]
    password=json_data["password"]
    group_id = json_data["group_id"]
    validation_report = validate_registration(name, password, game_id, db)
    if validation_report[1] != 200:  # stop and return the report if an error has occurred
        return validation_report

    password_hash = hashlib.sha256(password.encode('utf-8'))
    return create_player(name, password_hash.hexdigest(), game_id, group_id, db.session)


@app.route('/create-session/self-register', methods=["POST"])
@cross_origin()
def create_session():
    json_data = flask.request.json
    print(json_data)
    groups = json_data["groups"]
    print(groups)
    game = Game()
    game_id = str(uuid.uuid4())
    game.game_id = game_id
    game.draw_date = datetime.strptime(json_data["draw"], '%Y-%m-%d %H:%M:%S')
    db.session.add(game)
    for group in groups:
        create_group(group, game_id, db.session)
    db.session.commit()
    return str(game_id), 201

@app.route('/game/<game_id>/draw_date')
@cross_origin()
def get_draw_date(game_id):
    game = db.get_or_404(Game,game_id)
    return str(game.draw_date)


with app.app_context():
    db.create_all()