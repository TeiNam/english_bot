# apis/deps.py
from typing import Generator

from bots.english_bot import english_bot
from utils.mysql_connector import MySQLConnector


def get_db() -> Generator:
    db = MySQLConnector()
    try:
        yield db
    finally:
        db.close()


def get_bot() -> english_bot:
    return english_bot
