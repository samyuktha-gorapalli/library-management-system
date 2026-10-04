import mysql.connector

DB_CONFIG = {
    "host": "127.0.0.1",
    "user": "root",
    "password": "MySQL@1234",
    "database": "librarydb",
}


def get_connection():
    """Return a new MySQL connection using the settings above."""
    return mysql.connector.connect(**DB_CONFIG)