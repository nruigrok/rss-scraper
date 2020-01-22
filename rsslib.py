import sqlite3

DATABASE = "rss.db"
def create_connection():
    return sqlite3.connect(DATABASE)
