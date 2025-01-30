# utils/password.py
from passlib.context import CryptContext

# bcrypt 대신 pbkdf2_sha256 알고리즘으로 변경
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def hash_password(password: str) -> str:
    """비밀번호 해싱"""
    return pwd_context.hash(password)
