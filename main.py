from fastapi import Request, FastAPI, HTTPException
import mysql.connector
from pydantic import BaseModel, Field

app = FastAPI()

@app.get('/')
def root():
    return {"message": "Welcome to Pablo's twitch api"}