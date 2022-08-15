# Going for a lightweight (no user data saved) approach instead
import sqlite3

import flask
from flask import Flask
import random
import hashlib
from flask_cors import cross_origin, CORS

app = Flask(__name__)
cors = CORS(app)


def generate_unique_field(table_name, field_name):
    NUM_AVAILABLE_IDS = 1000000
    potential_id = -1
    with sqlite3.connect("database.db") as connection:
        while potential_id < 0 or len(connection.execute("SELECT * FROM "+table_name+" WHERE "+field_name+"='"
                                                         + str(potential_id) + "';").fetchall()) > 0:
            potential_id = random.randint(0, NUM_AVAILABLE_IDS)
    return potential_id

def create_record(table_name,field_name, field_value):
    command = f'INSERT INTO {table_name} ({field_name}) VALUES ({field_value})'
    print(command)
    with sqlite3.connect("database.db") as connection:
        connection.execute(command)



def create_player(name, password_hash, game_id):
    player_id = generate_unique_field("players", "player_id")
    create_record("games", "player_id,player_name,password_hash", f'{player_id},{name},{password_hash}')
    create_record("games-players", "game_id,player_id", f'{game_id},{player_id}')

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
    command = f"SELECT draw_date FROM games WHERE game_id={game_id}"
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