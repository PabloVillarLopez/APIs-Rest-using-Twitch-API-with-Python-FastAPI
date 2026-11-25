import mysql.connector

class DatabaseConnection:
    def __init__(self, host: str, user: str, password: str, database: str):
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.mydb = None

    async def get_db_connection(self):
        if self.mydb is None:
            self.mydb = mysql.connector.connect(
                host= "localhost",
                user= "root",
                password = "",
                database = "twitch_api"
            )
        return self.mydb