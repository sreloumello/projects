# app/database.py — database connection and dependency injection

import psycopg2
import psycopg2.extras
from app.config import get_settings


def get_connection():
    s = get_settings()
    return psycopg2.connect(
        host=s.DB_HOST,
        port=s.DB_PORT,
        dbname=s.DB_NAME,
        user=s.DB_USER,
        password=s.db_password,
        cursor_factory=psycopg2.extras.RealDictCursor,
        connect_timeout=5,
    )


def get_db():
    """fastapi dependency — yields a connection and closes it after the request"""
    conn = get_connection()
    try:
        yield conn
    finally:
        conn.close()
