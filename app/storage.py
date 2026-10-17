"""SQLite persistence: editable configuration plus immutable generation snapshots."""
import json
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path

DEFAULT_DB = Path(__file__).resolve().parent.parent / 'data' / 'unisched.db'

@contextmanager
def connect():
    path = Path(os.environ.get('UNISCHED_DB', str(DEFAULT_DB)))
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path, timeout=30)
    connection.row_factory = sqlite3.Row
    connection.execute('PRAGMA journal_mode=WAL')
    try:
        with connection:
            yield connection
    finally:
        connection.close()

def initialize():
    with connect() as db:
        db.executescript('''
        CREATE TABLE IF NOT EXISTS configuration (
            id INTEGER PRIMARY KEY CHECK(id=1), body TEXT NOT NULL,
            revision INTEGER NOT NULL DEFAULT 1,
            updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
        );
        CREATE TABLE IF NOT EXISTS generations (
            id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
            config_revision INTEGER NOT NULL, config TEXT NOT NULL,
            result TEXT NOT NULL
        );
        ''')

def get_config():
    from .domain import Configuration
    with connect() as db:
        row = db.execute('SELECT * FROM configuration WHERE id=1').fetchone()
    if not row:
        return {'revision': 0, 'configuration': Configuration().model_dump()}
    # Add schema defaults in memory; never rewrite a user's old configuration on read.
    return {'revision': row['revision'], 'configuration': Configuration(**json.loads(row['body'])).model_dump()}

class RevisionConflict(Exception):
    pass

def save_config(config, expected_revision):
    with connect() as db:
        db.execute('BEGIN IMMEDIATE')
        row = db.execute('SELECT revision FROM configuration WHERE id=1').fetchone()
        current = row['revision'] if row else 0
        if current != expected_revision:
            raise RevisionConflict('Academic data changed in another window. Reload before saving.')
        db.execute('''INSERT INTO configuration(id,body,revision) VALUES(1,?,?)
            ON CONFLICT(id) DO UPDATE SET body=excluded.body, revision=excluded.revision,
            updated_at=strftime('%Y-%m-%dT%H:%M:%fZ','now')''', (json.dumps(config), current+1))
    return current+1

def save_generation(name, revision, config, result):
    with connect() as db:
        cursor = db.execute('INSERT INTO generations(name,config_revision,config,result) VALUES(?,?,?,?)',
                            (name, revision, json.dumps(config), json.dumps(result)))
        return cursor.lastrowid

def get_generation(identifier):
    from .domain import Configuration, COLLEGE
    with connect() as db:
        row = db.execute('SELECT * FROM generations WHERE id=?', (identifier,)).fetchone()
    if not row:
        return None
    config = Configuration(**json.loads(row['config']))
    return {**dict(row), 'config': config.model_dump(), 'result': json.loads(row['result']),
            'meta': {'college':COLLEGE, **config.settings.meta()}}

def generations():
    with connect() as db:
        rows = db.execute('''SELECT id,name,created_at,config_revision,
            json_extract(result,'$.status') AS status,
            json_extract(result,'$.summary.teaching_hours') AS teaching_hours
            FROM generations ORDER BY id DESC LIMIT 100''').fetchall()
    return [dict(row) for row in rows]
