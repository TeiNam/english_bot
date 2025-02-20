# apis/models/user.py
from typing import Optional

from pydantic import BaseModel


class User(BaseModel):
    user_id: int
    email: str
    username: str
    is_admin: bool = False


class TokenData(BaseModel):
    email: Optional[str] = None
    user_id: Optional[int] = None
