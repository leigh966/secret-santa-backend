import hashlib
from arrayOperations import randomise_order
from Models.Group import Group
import uuid
from Models.Game import Game
from Models.Player import Player
from sqlalchemy import and_
from datetime import datetime
import random

def create_group(name, game_id, session):
    grp = Group()
    grp.group_id = str(uuid.uuid4())
    grp.group_name = name
    grp.game_id = game_id
    session.add(grp)

def get_groupless_series(game_id,session):
    players = session.query(Player).filter(Player.game_id==game_id).all()
    players = randomise_order(players)
    return [player.player_name for player in players]

def draw(game_id, session):
    names = []
    all_groups = session.query(Group).filter(Group.game_id==game_id).all()
    if len(all_groups) == 0:
        names = get_groupless_series(game_id, session)
    else:
        names = get_group_series(game_id,all_groups, session)
    for index in range(0, len(names)):
        chosen_name = names[(index+1)%len(names)]
        print("chosen name: ",chosen_name)
        set_picked_name(game_id, names[index], chosen_name, session)
    mark_drawn(game_id, session)

def get_grouped_names(game_id, all_groups, session):
    player_query = session.query(Player.player_name).filter(Player.game_id==game_id)
    groups = []
    total_names = 0
    for group in all_groups:
        names = player_query.filter(Player.group_id==group.group_id).all()
        groups.append([name_tuple[0] for name_tuple in names])
        total_names += len(names)
    print("grouped names:",groups)
    return groups, total_names

def get_group_series(game_id,all_groups, session):
    groups, total_names = get_grouped_names(game_id,all_groups, session)
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

def is_drawn(game_id, db):
    game = db.get_or_404(Game, game_id)
    return game.drawn

def mark_drawn(game_id, session):
    game = session.query(Game).filter(Game.game_id==game_id).first()
    game.drawn = True
    session.commit()

def should_game_start(game_id, db):
    game = db.get_or_404(Game, game_id, description="Game not found")
    return game.draw_date < datetime.now()

def set_picked_name(game_id, name, picked_name, session):
    player = session.query(Player).filter(and_(Player.game_id==game_id,Player.player_name==name)).first()
    player.picked_name = picked_name
    print("updating player",player.player_name,"to have picked_name",picked_name)
    session.commit()



def authenticate_user(game_id,name, password,session):
    password_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()
    matching_players = session.query(Player).filter(and_(Player.game_id==game_id,Player.player_name==name,Player.password_hash==password_hash))
    return matching_players.count() > 0


def does_game_have_groups(game_id):
    return len(select("*", "games_and_groups", f"game_id={game_id}")) > 0

def get_picked_name(game_id, name,session):
    player = session.query(Player).filter(and_(Player.player_name==name,Player.game_id==game_id)).first()
    return player.picked_name

def game_exists(game_id):
    games_with_id = select("game_id", "games", f"game_id={game_id}")
    return len(games_with_id) > 0

def player_exists(name, game_id, session):
   return session.query(Player).filter(and_(Player.game_id==game_id,Player.player_name==name)).count()>0

def create_player(name, password_hash, game_id, group_id, session):
    if group_id:
        num_matching_groups = session.query(Group).filter(and_(Group.group_id==group_id,Group.game_id==game_id)).count()
        if num_matching_groups < 1:
            return "group_id does not correspond to any group in this game", 401
    new_player = Player()
    new_player.player_id = str(uuid.uuid4())
    new_player.password_hash=password_hash
    new_player.player_name=name
    new_player.game_id=game_id
    new_player.group_id=group_id
    session.add(new_player)
    session.commit()
    return "done",201

def get_players(game_id, session):
    players = session.query(Player).filter(Player.game_id==game_id)
    
    output = []
    for player in players:
        group = session.query(Group).get(player.group_id)
        group_name = None
        if group:
            group_name = group.group_name
        output.append({"name":player.player_name, "group":group_name})


    return output