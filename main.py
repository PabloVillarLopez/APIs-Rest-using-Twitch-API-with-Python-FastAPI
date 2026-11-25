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
    mydb = mysql.connector.connect(
        host= "localhost", user= "root", password= "", database="twitch_api"
    )
    mycursor = mydb.cursor()
    mycursor.execute("SELECT * FROM twitch_users;")
    result = mycursor.fetchall()
    return result

@app.post('/users/')
async def create_user(request: Request):
    mydb = mysql.connector.connect(
        host= "localhost", user= "root", password= "", database="twitch_api"
    )
    mycursor = mydb.cursor()
    data = await request.json()
    username = data["username"]
    followed_streamers = ["followed_streamers"]
    mycursor.execute(f'INSERT INTO `twitch_users` (name, followed_streamers) VALUES ("{username}", "{followed_streamers}");')
    mydb.commit()
    return {"message": "User created succesfully"}, 201

@app.put('/users/{user_id}')
async def update_user(user_id: int, request: Request):
    mydb = mysql.connector.connect(
        host= "localhost", user= "root", password="", databaser="twitch_api"
    )
    mycursor = mydb.cursor()
    data = await request.json()
    name = data.get("name")
    followed_streamers = data.get("followed_streamers")
    update_fields = []
    if name:
        update_fields.append(f'name="{name}"')
    if followed_streamers:
        update_fields.append(f'followed_streamers="{followed_streamers}"')
    if not update_fields:
        raise HTTPException(status_code=400, detail="No fields to update")

    mycursor.execute(f'UPDATE `twitch_users` SET {", ".join(update_fields)} WHERE id={user_id};')
    mydb.commit()
    if mycursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="User not found")

    return {"message": "User modified succesfully"}

@app.delete('/users/{user_id}')
async def delete_user(user_id: int):
    mydb = mysql.connector.connect(
        host= "localhost", user= "root", password= "", database= "twitch_api"
    )
    mycursor = mydb.cursor()
    mycursor.execute(f'DELETE FROM twitch_users WHERE id={user_id};')
    mydb.commit()
    if mycursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="User not found")

    return {"message": "User deleted successfully"}