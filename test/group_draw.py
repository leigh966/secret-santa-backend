import requests
import time
import sys

requests_session = requests.session()
requests_session.headers.update({'Content-Type': 'application/json', 'Accept':'application/json'})
requests_session.headers.update({'charset':'utf-8'})

game_id = ""
HOST = "http://localhost:8000/"
headers = {
      "Accept": "application/json",
  "Content-Type": "application/json"
}
group_ids = []

def create_game():
    global game_id
    data = {
        "draw": "2022-02-19 11:00:00",
        "groups": ["a", "b", "c"]
    }
    game_id = requests_session.post(HOST+"create-session/self-register", json=data).text
    print("game_id = ", game_id)

def get_groups():
    global group_ids
    group_ids.clear()
    r = requests.get(HOST+"groups/"+game_id)
    my_json = r.json()["groups"]
    for group in my_json:
        group_ids.append(group["id"])

names = [["1", "2", "3", "4"], ["11", "12", "13", "14"], ["21", "22", "23", "24"]]
def register_all():
    global names
    for i in range(0, len(names)):
        group_id = group_ids[i]
        for name in names[i]:
            register(name, group_id)

def register(name, group_id):
    global game_id
    data = {
        "name" : name,
        "password" : "pass",
        "group_id" : group_id
    }
    requests_session.post(HOST+"register/"+game_id, json=data, headers=headers)

def get_picked(name):
    global game_id
    data = {
        "name": name,
        "password": "pass",
    }
    return requests_session.post(HOST+"picked/"+game_id, json=data).text


no_runs = 1
if len(sys.argv) > 1:
    no_runs = int(sys.argv[1])
for i in range(0, no_runs):
    seen = []
    create_game()
    get_groups()
    register_all()

    get_picked("1")
    time.sleep(5)
    for group in names:
        for name in group:
            picked = get_picked(name)
            assert(seen.count(picked)==0) # not already picked
            assert(group.count(picked)==0) # not in this group
            print(name+" -> "+picked)


