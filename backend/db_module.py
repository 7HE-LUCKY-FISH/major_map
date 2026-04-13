import mysql.connector
from mysql.connector import Error
import os
import sys
import time
import dotenv

dotenv.load_dotenv()


def get_db_connection():
    """Connect to the application database (major_map_db by default)."""
    try:
        connection = mysql.connector.connect(
            host=os.getenv("DB_HOST", "localhost"),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD", "adminpass"),
            database=os.getenv("DB_NAME", "major_map_db"),
            port=int(os.getenv("DB_PORT", 3306)), 
            auth_plugin="mysql_native_password"
        )
        return connection
    except Error as e:
        print(f"Error connecting to database: {e}")
        return None


def get_server_connection():
    """Connect to MySQL server without selecting a database.

    Used by DDL scripts that need to create the database itself.
    """
    try:
        connection = mysql.connector.connect(
            host=os.getenv("DB_HOST", "localhost"),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD", "adminpass"),
            auth_plugin="mysql_native_password",
        )
        return connection
    except Error as e:
        print(f"Error connecting to database server: {e}")
        return None


def get_db_connection_with_retry(max_attempts=10, sleep_seconds=5):
    """Retry get_db_connection() up to max_attempts times.

    Designed for Docker Compose startup where the DB may not be ready yet.
    Calls sys.exit(1) if all attempts fail.
    """
    for _ in range(max_attempts):
        connection = get_db_connection()
        if connection is not None:
            return connection
        print("Waiting for database connection...")
        time.sleep(sleep_seconds)
    print("Could not connect to the database.")
    sys.exit(1)


def get_server_connection_with_retry(max_attempts=10, sleep_seconds=5):
    """Retry get_server_connection() up to max_attempts times.

    Designed for Docker Compose startup where the DB server may not be ready yet.
    Calls sys.exit(1) if all attempts fail.
    """
    for _ in range(max_attempts):
        connection = get_server_connection()
        if connection is not None:
            return connection
        print("Waiting for database connection...")
        time.sleep(sleep_seconds)
    print("Could not connect to the database server.")
    sys.exit(1)

