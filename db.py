import os
import sqlite3

conn = sqlite3.connect(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'soma.db'))

c = conn.cursor()


# check initialized
def get_config(name):
    try:
        c.execute('SELECT value FROM config WHERE name=?', (name,))
        return c.fetchone()[0]
    except Exception:
        return None


def local_list():
    c.execute('SELECT name, source, user, password, show_password FROM problem_local ORDER BY name')
    return c.fetchall()


def remote_list():
    c.execute('SELECT name, source, port, pid FROM problem_remote ORDER BY name')
    return c.fetchall()


def empty_port(port):
    c.execute('SELECT id FROM problem_remote WHERE port = ?', (port,))
    return len(c.fetchall()) == 0


def get_remote_problem(prob_name):
    c.execute('SELECT user, entry, port, pid FROM problem_remote WHERE name = ?', (prob_name,))
    probs = c.fetchall()
    if len(probs) == 0:
        return None
    return probs[0]


# create tables
def create_db(soma_user, soma_path):
    c.executescript('''
        CREATE TABLE config(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name varchar(50),
            value varchar(255)
        );

        CREATE TABLE problem_local(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source varchar(100),
            name varchar(50),
            user varchar(50),
            password varchar(255),
            show_password INTEGER,
            user_solve varchar(50)
        );

        CREATE TABLE problem_remote(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source varchar(100),
            name varchar(50),
            user varchar(50),
            entry varchar(255),
            port INTEGER,
            pid INTEGER
        );
    ''')

    c.executemany('INSERT INTO config (name, value) VALUES (?, ?)', (
        ('initialized', 'True'),
        ('soma_user', soma_user),
        ('soma_path', soma_path))
    )
    conn.commit()


# create local problem
def add_local(source, name, user, password, show_password, user_pwn):
    c.execute(
        'INSERT INTO problem_local (source, name, user, password, show_password, user_solve) VALUES (?, ?, ?, ?, ?, ?)',
        (source, name, user, password, show_password, user_pwn)
    )
    conn.commit()


# create remote problem
def add_remote(source, name, user, entry, port, pid):
    c.execute(
        'INSERT INTO problem_remote (source, name, user, entry, port, pid) VALUES (?, ?, ?, ?, ?, ?)',
        (source, name, user, entry, port, pid)
    )
    conn.commit()


def modify_remote(name, port, pid):
    c.execute('UPDATE problem_remote SET port = ?, pid = ? WHERE name = ?', (port, pid, name))
    conn.commit()
