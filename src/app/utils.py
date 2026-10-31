from pwdlib import PasswordHash


password_hash = PasswordHash.recommended()
def get_password_hash(password: str) -> str:
    """Хэширует пароль и возвращает строку для сохранения в БД."""
    return password_hash.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Проверяет, соответствует ли введённый пароль сохранённому хэшу."""
    return password_hash.verify(plain_password, hashed_password)