import mysql.connector
import os

def get_db_connection():
    connection = mysql.connector.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        user=os.getenv('DB_USER', 'root'),
        password=os.getenv('DB_PASSWORD', 'adminpass'),
        database=os.getenv('DB_NAME', 'major_map_db')
    )
    return connection