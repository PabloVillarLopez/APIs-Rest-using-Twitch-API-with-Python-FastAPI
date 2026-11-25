from fastapi import Request, FastAPI, HTTPException
import mysql.connector
from pydantic import BaseModel, Field
from config.connections import DatabaseConnection
import os

from dotenv import load_dotenv
from fastapi.responses import JSONResponse

load_dotenv()

app = FastAPI()

@app.get('/')
def root():
    return {"message": "Welcome to Pablo's twitch api"}

class UserCreate(BaseModel):
    name: str
    followed_streamers: str

class UserUpdate(BaseModel):
    name: str
    followed_streamers: str

def get_db():
    return DatabaseConnection()

@app.get('/users')
async def read_users():
    mydb = get_db()
    mydb_connection = await mydb.get_db_connection()
    mycursor = mydb_connection.cursor()
    try:
        mycursor.execute("SELECT * FROM twitch_users;")
        result = mycursor.fetchall()
        return result
    finally:
        mycursor.close()
        mydb_connection.close()

@app.post('/users/')
async def create_user(user: UserCreate):
    mydb = get_db()
    mydb_connection = mydb.get_db_connection()
    mycursor = mydb_connection.cursor()
    #data = await request.json()
    try:
        username = user.name
        followed_streamers = user.followed_streamers
        sql = f'INSERT INTO `twitch_users` (name, followed_streamers) VALUES ("{username}", "{followed_streamers}");'
        mycursor.execute(sql)
        mydb_connection.commit()
        return JSONResponse(content={"message": "User created successfully"}, status_code=201)
    finally:
        mycursor.close()
        mydb_connection.close()

@app.put('/users/{user_id}')
async def update_user(user_id: int, user: UserUpdate):
    mydb = get_db()
    mydb_connection = mydb.get_db_connection()
    mycursor = mydb_connection.cursor()
    try:
        #data = await request.json()
        #name = data.get("name")
        #followed_streamers = data.get("followed_streamers")
        name = user.name
        followed_streamers = user.followed_streamers
        update_fields = []
        if name:
            update_fields.append(f'name="{name}"')
        if followed_streamers:
            update_fields.append(f'followed_streamers="{followed_streamers}"')
        if not update_fields:
            raise HTTPException(status_code=400, detail="No fields to update")
        sql = f'UPDATE `twitch_users` SET {", ".join(update_fields)} WHERE id={user_id};'
        mycursor.execute(sql)
        mydb_connection.commit()
        if mycursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="User not found")

        return JSONResponse(content={"message": "User modified successfully"}, status_code=200)
    finally:
        mycursor.close()
        mydb_connection.close()

@app.delete('/users/{user_id}')
async def delete_user(user_id: int):
    mydb = get_db()
    mydb_connection = mydb.get_db_connection()
    mycursor = mydb_connection.cursor()
    try:
        sql = f'DELETE FROM twitch_users WHERE id={user_id};'
        mycursor.execute(sql)
        mydb_connection.commit()
        if mycursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="User not found")

        return JSONResponse(content={"message": "User deleted successfully"}, status_code=200)
    finally:
        mycursor.close()
        mydb_connection.close()