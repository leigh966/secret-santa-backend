import sqlite3
import random

MAX_INT = (2**63)-1

def create_record(table_name,field_name, field_value):
    command = f'INSERT INTO {table_name} ({field_name}) VALUES ({field_value})'
    print(command)
    with sqlite3.connect("database.db") as connection:
        connection.execute(command)
        connection.commit()

def generate_unique_field(table_name, field_name):
    potential_id = -1
    with sqlite3.connect("database.db") as connection:
        while potential_id < 0 or len(connection.execute("SELECT * FROM "+table_name+" WHERE "+field_name+"='"
                                                         + str(potential_id) + "';").fetchall()) > 0:
            potential_id = random.randint(0, MAX_INT)
    return potential_id

def select(SELECT, FROM, WHERE):
    with sqlite3.connect("database.db") as connection:
        return connection.execute(f'SELECT {SELECT} FROM {FROM} WHERE {WHERE};').fetchall()

def get_inner_join_expression(table1, table2, on):
    return f"{table1} INNER JOIN {table2} ON {on}"