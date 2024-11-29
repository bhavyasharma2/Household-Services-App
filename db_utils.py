import sqlite3
from flask import g

DATABASE = 'household_services.db'

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE) 
        g.db.row_factory = sqlite3.Row 
        
    return g.db

def execute_query(query, params=()):
    db = get_db()
    cursor = db.cursor()
    cursor.execute(query, params)
    db.commit()
    return cursor

def fetch_all(query, params=()):
    db = get_db()
    cursor = db.cursor()
    cursor.execute(query, params)
    return cursor.fetchall()

def fetch_one(query, params=()):
    db = get_db()
    cursor = db.cursor()
    cursor.execute(query, params)
    return cursor.fetchone()

