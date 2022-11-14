from dbOperations import *
import hashlib
from arrayOperations import randomise_order

def draw(game_id):
    join_expr = get_inner_join_expression("players", "games_and_players", "players.player_id=games_and_players.player_id")
    names = select("player_name", join_expr, f"game_id={game_id}")
    names = randomise_order(names)
    for index in range(0, len(names)):
        set_picked_name(game_id, names[index][0], names[(index+1)%len(names)][0])
    mark_drawn(game_id)

def is_drawn(game_id):
    drawn = select("drawn", "games", f"game_id={game_id}")[0][0]
    return drawn == 1

def mark_drawn(game_id):
    with sqlite3.connect("database.db") as connection:
        connection.execute(f"UPDATE games SET drawn = TRUE WHERE game_id={game_id};")

def should_game_start(game_id):
    passed_game = select("*", "games", f'game_id={game_id} AND draw_date > datetime("now")')
    if len(passed_game) == 0:
        return True
    return False

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


def authenticate_user(game_id,name, password):
    password_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()
    join_expr = get_inner_join_expression("players", "games_and_players", "players.player_id=games_and_players.player_id")
    and_expr = get_and_expression(f'game_id="{game_id}"', f'players.player_name="{name}"', f'players.password_hash="{password_hash}"')
    matching_players = select("DISTINCT players.player_id", join_expr, and_expr)
    return len(matching_players) > 0


def get_picked_name(game_id, name):
    join_expr = get_inner_join_expression("players", "games_and_players", "players.player_id=games_and_players.player_id")
    return select("picked_name", join_expr, f' player_name="{name}" AND game_id={game_id}')[0][0]

def game_exists(game_id):
    games_with_id = select("game_id", "games", f"game_id={game_id}")
    return len(games_with_id) > 0

def player_exists(name, game_id):
    join_expr = get_inner_join_expression("players", "games_and_players", "players.player_id=games_and_players.player_id")
    players_with_id = select("DISTINCT *", join_expr, f'game_id={game_id} AND player_name="{name}"')
    return len(players_with_id)>0

def create_player(name, password_hash, game_id, group_id):
    if(group_id != None and len(select("*", "games_and_groups", f"group_id={group_id} AND game_id={game_id}")) < 1):
        return "group_id does not correspond to any group in this game", 401
    player_id = generate_unique_field("players", "player_id")
    create_record("players", "player_id,player_name,password_hash,group_id", f'{player_id},"{name}","{password_hash}",{group_id}')
    create_record("games_and_players", "game_id,player_id", f'{game_id},{player_id}')
    return "done",201