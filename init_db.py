from dbOperations import getConnection
from db_config import DATABASE_NAME, INIT_SCHEMA_FILENAME

connection = getConnection()
cursor = connection.cursor()
cursor.exec

with open(INIT_SCHEMA_FILENAME) as f:
    cursor.execute(f.read())


connection.commit()
cursor.close()
connection.close()