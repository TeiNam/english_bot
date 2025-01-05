# apis/deps.py
from typing import Generator
from utils.mysql_connector import MySQLConnector
from bots.english_bot import english_bot

def get_db() -> Generator:
    db = MySQLConnector()
    try:
        yield db
    finally:
        db.close()

def get_bot() -> english_bot:
    return english_bot