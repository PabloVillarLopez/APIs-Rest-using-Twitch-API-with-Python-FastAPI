from fastapi import FastAPI, HTTPException
import mysql.connector
from pydantic import BaseModel, Field
from config.connections import DatabaseConnection

from dotenv import load_dotenv
from fastapi.responses import JSONResponse

import requests
from services.twitch_auth import TwitchTokenManager
from typing import Literal

token_manager = TwitchTokenManager()

load_dotenv()

app = FastAPI()

@app.get('/')
def root():
    return {"message": "Welcome to Pablo's twitch api"}

class UserCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    followed_streamers: str = Field(..., min_length=1, max_length=255)

class UserUpdate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    followed_streamers: str = Field(..., min_length=1, max_length=255)

class PreferenceCreate(BaseModel):
    user_id: int = Field(..., gt=0)
    streamer_name: str = Field(..., min_length=1, max_length=100)
    preference: Literal["like", "dislike"]

class PlaylistCreate(BaseModel):
    user_id: int = Field(..., gt=0)
    playlist_name: str = Field(..., min_length=1, max_length=100)
    streamers: str = Field(..., min_length=1, max_length=255)

def get_db():
    mydb = DatabaseConnection()
    db_connection = mydb.get_db_connection()
    cursor = db_connection.cursor()
    return db_connection, cursor

def close_db(conn, cursor):
    if cursor:
        cursor.close()
    if conn:
        conn.close()

def get_twitch_streamer_info(username: str):
    token = token_manager.get_token()
    response = requests.get(
        "https://api.twitch.tv/helix/users",
        params={"login": username},
        headers={
            "Client-Id": token_manager.client_id,
            "Authorization": f"Bearer {token}",
        },
        timeout=10
    )
    response.raise_for_status()
    return response.json()

def search_streamer_in_twitch(username: str):
    clean_name = username.strip().lower()
    try:
        data = get_twitch_streamer_info(clean_name)
    except requests.RequestException as err:
        raise HTTPException(status_code=502, detail=f"Twitch API error: {err}")

    users = data.get("data", [])
    if not users:
        return None
    return users[0]

@app.get('/users')
async def read_users():
    mydb_connection, mycursor = get_db()
    try:
        mycursor.execute("SELECT * FROM twitch_users;")
        result = mycursor.fetchall()
        return result
    except mysql.connector.Error as err:
        raise HTTPException(status_code=500, detail=f"Database error: {err}")
    finally:
        close_db(mydb_connection, mycursor)

@app.post('/users/')
async def create_user(user: UserCreate):
    mydb_connection, mycursor = get_db()
    try:
        username = user.name
        followed_streamers = user.followed_streamers
        sql = "INSERT INTO `twitch_users` (name, followed_streamers) VALUES (%s, %s);"
        mycursor.execute(sql, (username, followed_streamers))
        mydb_connection.commit()
        return JSONResponse(content={"message": "User created successfully"}, status_code=201)
    except mysql.connector.Error as err:
        raise HTTPException(status_code=500, detail= f'Error: {err}')
    finally:
        close_db(mydb_connection, mycursor)

@app.put('/users/{user_id}')
async def update_user(user_id: int, user: UserUpdate):
    mydb_connection, mycursor = get_db()
    try:
        name = user.name
        followed_streamers = user.followed_streamers
        update_fields = []
        params = []

        if name:
            update_fields.append("name = %s")
            params.append(name)
        if followed_streamers:
            update_fields.append("followed_streamers = %s")
            params.append(followed_streamers)
        if not update_fields:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        params.append(user_id)
        sql = f'UPDATE `twitch_users` SET {", ".join(update_fields)} WHERE id= %s;'
        mycursor.execute(sql, params)
        mydb_connection.commit()
        if mycursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="User not found")

        return JSONResponse(content={"message": "User modified successfully"}, status_code=200)
    except mysql.connector.Error as err:
        raise HTTPException(status_code=500, detail=f'Error: {err}')
    finally:
        close_db(mydb_connection, mycursor)

@app.delete('/users/{user_id}')
async def delete_user(user_id: int):
    mydb_connection, mycursor = get_db()
    try:
        sql = "DELETE FROM twitch_users WHERE id=%s;"
        mycursor.execute(sql, (user_id,))
        mydb_connection.commit()
        if mycursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="User not found")

        return JSONResponse(content={"message": "User deleted successfully"}, status_code=200)
    except mysql.connector.Error as err:
        raise HTTPException(status_code=500, detail=f'Error: {err}')
    finally:
        close_db(mydb_connection, mycursor)

@app.get("/twitch/streamers/{username}")
async def get_streamer_from_twitch(username: str):
    streamer = search_streamer_in_twitch(username)
    if not streamer:
        raise HTTPException(status_code=404, detail="Streamer not found on Twitch")
    return streamer

@app.post("/preferences", status_code=201)
async def set_streamer_preference(pref: PreferenceCreate):
    streamer = search_streamer_in_twitch(pref.streamer_name)
    if not streamer:
        raise HTTPException(status_code=404, detail="Streamer not found")

    streamer_login = streamer["login"].lower()
    mydb_connection, mycursor = get_db()
    try:
        mycursor.execute("SELECT id FROM twitch_users WHERE id=%s;", (pref.user_id,))
        if not mycursor.fetchone():
            raise HTTPException(status_code=404, detail="User not found")
        
        sql = """
            INSERT INTO streamer_preferences (user_id, streamer_name, preference)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE preference = VALUES(preference);
        """
        mycursor.execute(sql, (pref.user_id, streamer_login, pref.preference))
        mydb_connection.commit()
        return JSONResponse(
            content={
                "message": "Preference saved successfully",
                "user_id": pref.user_id,
                "streamer": streamer["display_name"],
                "preference": pref.preference
            },
            status_code=201
        )
    except mysql.connector.Error as err:
        raise HTTPException(status_code=500, detail=f"Database error: {err}")
    finally:
        close_db(mydb_connection, mycursor)

@app.post("/playlists", status_code=201)
async def create_playlist(playlist: PlaylistCreate):
    raw_streamers = [s.strip().lower() for s in playlist.streamers.split(",") if s.strip()]
    if not raw_streamers:
        raise HTTPException(status_code=400, detail="Streamers list cannot be empty")

    valid_streamers = []
    display_names = []
    for name in raw_streamers:
        streamer = search_streamer_in_twitch(name)
        if streamer:
            valid_streamers.append(streamer["login"].lower())
            display_names.append(streamer["display_name"])

    if not valid_streamers:
        raise HTTPException(status_code=404, detail="None of the provided streamers were found on Twitch")

    mydb_connection, mycursor = get_db()
    try:
        mycursor.execute("SELECT id FROM twitch_users WHERE id=%s;", (playlist.user_id,))
        if not mycursor.fetchone():
            raise HTTPException(status_code=404, detail="User not found")

        streamers_clean_str = ",".join(valid_streamers)
        sql = "INSERT INTO user_playlists (user_id, playlist_name, streamers) VALUES (%s, %s, %s);"
        mycursor.execute(sql, (playlist.user_id, playlist.playlist_name, streamers_clean_str))
        mydb_connection.commit()
        return JSONResponse(
            content={
                "message": "Playlist created successfully",
                "playlist_name": playlist.playlist_name,
                "streamers": display_names,
            },
            status_code=201
        )
    except mysql.connector.Error as err:
        raise HTTPException(status_code=500, detail=f"Database error: {err}")
    finally:
        close_db(mydb_connection, mycursor)