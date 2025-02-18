# test/create_hash_password.py
from utils.password import hash_password


def create_test_hash():
    """테스트용 해시 패스워드 생성"""
    passwords = [
        "admin"
    ]

    print("\n=== 패스워드 해시 결과 ===")
    for pwd in passwords:
        hashed = hash_password(pwd)
        print(f"\n원본 패스워드: {pwd}")
        print(f"해시된 패스워드: {hashed}")
        print("=" * 50)


if __name__ == "__main__":
    create_test_hash()