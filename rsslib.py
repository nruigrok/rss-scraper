import sqlite3

def create_connection(database):
    return sqlite3.connect(database)
