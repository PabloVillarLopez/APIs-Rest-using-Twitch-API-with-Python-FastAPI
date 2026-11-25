import mysql.connector
from dotenv import load_dotenv
import os

load_dotenv()

class DatabaseConnection:
    def __init__(
            self, 
            host: str | None = None,
            user: str | None = None,
            password: str | None = None, 
            database: str | None = None):
        self.host = host or os.getenv("DB_HOST", "localhost")
        self.user = user or os.getenv("DB_USER", "root")
        self.password = password or os.getenv("DB_PASSWORD")
        self.database = database or os.getenv("DB_NAME", "twitch_api")

    def get_db_connection(self):
        if not self.password:
            raise ValueError("DB_PASSWORD is missing on environment variables")
        
        return mysql.connector.connect(
            host= self.host,
            user= self.user,
            password = self.password,
            database = self.database
        )