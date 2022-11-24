from dbOperations import *
import hashlib
from arrayOperations import randomise_order

def get_groupless_series(game_id):
    join_expr = get_inner_join_expression("players", "games_and_players", "players.player_id=games_and_players.player_id")
    names = select("player_name", join_expr, f"game_id={game_id}")
    names = randomise_order(names)
    return [name[0] for name in names]

def draw(game_id):
    names = []
    from_expr = get_inner_join_expression("groups", "games_and_groups",
                                          "groups.group_id=games_and_groups.group_id")
    all_groups = select("groups.group_id", from_expr, f"game_id={game_id}")
    if len(all_groups) == 0:
        names = get_groupless_series(game_id)
    else:
        names = get_group_series(game_id, all_groups)
    for index in range(0, len(names)):
        set_picked_name(game_id, names[index], names[(index+1)%len(names)])
    mark_drawn(game_id)

def get_grouped_names(game_id, all_groups):
    join_expr = get_inner_join_expression("players", "games_and_players", "players.player_id=games_and_players.player_id")
    groups = []
    total_names = 0
    for group in all_groups:
        names = select("player_name", join_expr, f"game_id={game_id} AND group_id={group[0]}")
        groups.append(randomise_order([name[0] for name in names]))
        total_names += len(names)
    return groups, total_names

def get_group_series(game_id, all_groups):
    groups, total_names = get_grouped_names(game_id, all_groups)
    bubble_sort_by_size(groups)
    output = []
    ignore_index = -1
    while(len(output) < total_names):
        print(output)
        print(groups)
        selected_index = random.randint(0, get_index_high(groups))
        print("generated index: ", selected_index)
        if selected_index == ignore_index:
            if selected_index == 0:
                selected_index += 1
            else:
                selected_index -= 1
        print("selecting: ", selected_index)
        output.append(groups[selected_index].pop(0))
        for ignore_index in range(selected_index,len(groups)-1):
            if len(groups[ignore_index]) >= len(groups[ignore_index+1]):
                break
            move_elem_right(groups, ignore_index)
    return output


def get_index_high(arr):
    highest = len(arr[0])
    for i in range(1, len(arr)):
        if len(arr[i]) < highest:
            return i-1
    return len(arr)-1

def move_elem_right(array, index):
    # swapping elements
    temp = array[index]
    array[index] = array[index + 1]
    array[index + 1] = temp

def move_into_order(array, index):
    # loop to compare array elements
    for j in range(0, len(array) - index - 1):
        # compare two adjacent elements
        if len(array[j]) < len(array[j + 1]):
            move_elem_right(array, j)

def bubble_sort_by_size(array):
    # loop to access each array element
    for i in range(len(array)):
        move_into_order(array, i)

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


def does_game_have_groups(game_id):
    return len(select("*", "games_and_groups", f"game_id={game_id}")) > 0

def get_picked_name(game_id, name):
    join_expr = get_inner_join_expression("players", "games_and_players", "players.player_id=games_and_players.player_id")
    return select("picked_name", join_expr, f' player_name="{name}" AND game_id={game_id}')[0][0]

def game_exists(game_id):
    games_with_id = select("game_id", "games", f"game_id={game_id}")
    return len(games_with_id) > 0

def player_exists(name, game_id):
    join_expr = get_inner_join_expression("players", "games_and_players", "players.player_id=games_and_players.player_id")
    players_with_id = select("DISTINCT *", join_expr, f'game_id={game_id} AND player_name=\'{name}\'')
    return len(players_with_id)>0

def create_player(name, password_hash, game_id, group_id):
    if group_id:
        if len(select("*", "games_and_groups", f"group_id={group_id} AND game_id={game_id}")) < 1:
            return "group_id does not correspond to any group in this game", 401
    else:
        group_id = "NULL"
    player_id = generate_unique_field("players", "player_id")
    create_record("players", "player_id,player_name,password_hash,group_id", f'{player_id},"{name}","{password_hash}",{group_id}')
    create_record("games_and_players", "game_id,player_id", f'{game_id},{player_id}')
    return "done",201

def get_players(game_id):
    from_expr = get_inner_join_expression("players", "games_and_players", "players.player_id=games_and_players.player_id")
    fields = "players.player_name"
    game_has_groups = does_game_have_groups(game_id)
    if game_has_groups:
        fields += ", groups.group_name"
        from_expr+=" INNER JOIN groups ON players.group_id=groups.group_id"
    all_players = select(fields, from_expr, f"game_id={game_id}")
    output = {"players" : []}
    for name in all_players:
        new_player = {"name":name[0]}
        if game_has_groups:
            new_player["group"] = name[1]
        output["players"].append(new_player)

    return output