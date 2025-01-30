# apis/models/auth_service.py
from typing import Optional
from utils.mysql_connector import MySQLConnector
from passlib.context import CryptContext
from .user import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    def __init__(self):
        self.db = MySQLConnector()

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)

    def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """사용자 인증

        Args:
            email: 이메일
            password: 비밀번호

        Returns:
            Optional[User]: 인증된 사용자 정보 또는 None
        """
        # 사용자 조회
        results = self.db.select(
            table="user",
            where={"email": email, "is_active": "Y"}
        )

        if not results:
            return None

        user_data = results[0]
        if not self.verify_password(password, user_data['password']):
            return None

        return User(
            user_id=user_data['user_id'],
            username=user_data['username'],
            password=user_data['password'],
            email=user_data['email'],
            is_active=user_data['is_active'],
            create_at=user_data['create_at'],
            update_at=user_data['update_at']
        )