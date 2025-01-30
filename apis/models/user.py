# apis/models/user.py
from dataclasses import dataclass
from datetime import datetime

@dataclass
class User:
    user_id: int
    username: str
    password: str
    email: str
    is_active: str  # 'Y' or 'N'
    create_at: datetime
    update_at: datetime