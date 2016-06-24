import os
import sqlite3

__all__ = ['initialized']

conn = sqlite3.connect(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'soma.db'))

c = conn.cursor()


# check initialized
def initialized():
    try:
        c.execute('SELECT value FROM config WHERE name="initialized"')
        return c.fetchone()[0] == 'True'
    except Exception:
        return False


# create tables
def create_db(soma_user):
    c.executescript('''
        CREATE TABLE config(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name varchar(50),
            value varchar(255)
        );

        CREATE TABLE problem_local(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name varchar(50),
            user varchar(50),
            password varchar(255),
            user_solve varchar(50),
            show_password INTEGER
        );

        CREATE TABLE problem_remote(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name varchar(50),
            user varchar(50),
            command varchar(255),
            pid INTEGER
        );
    ''')

    c.executemany('INSERT INTO config (name, value) VALUES (?, ?)', (('initialized', 'True'), ('soma_user', soma_user)))
    conn.commit()
