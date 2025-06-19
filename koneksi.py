import psycopg2
import psycopg2.extras
from flask import current_app, g
from urllib.parse import urlparse

def get_db():
    if 'db' not in g:
        db_url = 'postgresql://postgres:dsAAmeSHsZknzaJhzmjdKMRPRcSdCOsg@tramway.proxy.rlwy.net:44692/railway'
        if db_url:
            result = urlparse(db_url)

            g.db = psycopg2.connect(
                dbname=result.path[1:],
                user=result.username,
                password=result.password,
                host=result.hostname,
                port=result.port
            )
    return g.db

def close_db(e=None):
    db = g.pop('db', None)

    if db is not None:
        db.close()
