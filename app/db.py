import sqlite3
DB_PATH = "data/posts.db"
def get_connection():
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
conn.execute("PRAGMA journal_mode=WAL;")
return conn
def ensure_tables(conn):
conn.execute("""
CREATE TABLE IF NOT EXISTS posts (
id INTEGER PRIMARY KEY AUTOINCREMENT,
title TEXT,
text TEXT,
embedding BLOB
)
""")
conn.execute("""
CREATE TABLE IF NOT EXISTS clicks (
id INTEGER PRIMARY KEY AUTOINCREMENT,
aid TEXT,
ip TEXT,
ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")
conn.commit()
