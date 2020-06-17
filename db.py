import os
import apsw
from flask import current_app

DATABASE = os.environ["DATABASE"]


db = apsw.Connection(
    DATABASE,
)
cur = db.cursor()

def create_table():
    with current_app.open_resource('schema.sql') as f:
        db.executescript(f.read().decode('utf8'))

def insert_location(userid, longitude, latitude):
    cur.execute("INSERT INTO post (userid, latitude, longitude) VALUES (?, ?, ?)", (userid, latitude, longitude))

def fetch_location(userid):
    location = db.execute("SELECT latitude, longitude FROM post WHERE username=?", (userid)).fetchone()
    return location

def insert_freeword(userid, freeword):
    cur.execute("INSERT INTO post (userid, freeword) VALUES (?, ?), (userid, freeword)")

def fetch_freeword(userid):
    word = db.execute("SELECT freeword FROM post WHERE username=?", (userid)).fetchone()
    return word

def fetch_userid(username):
    username = db.execute("SELECT id FROM user WHERE username=?", (username)).fetchone()

def insert_username(username):
    db.execute("INSERT INTO user (username) VALUES (?)", (username))

if __name__ == '__main__':
    create_table()
    