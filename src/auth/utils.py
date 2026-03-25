import bcrypt
import base64
import jwt
from src.config import settings


def get_password_hash(password) -> str:
    bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hash = bcrypt.hashpw(bytes, salt)
    return base64.b64encode(hash).decode("utf-8")

def verify_password(plain_password, hashed_password) -> bool:
    hashed_bytes = base64.b64decode(hashed_password.encode("utf-8"))
    bytes = plain_password.encode('utf-8')
    result = bcrypt.checkpw(bytes, hashed_bytes)
    return result

def encode_jwt(
    payload: dict, 
    private_key: str = settings.auth_jwt.private_key_path.read_text(), 
    algorithm=settings.auth_jwt.algorithm
) -> str:
    encoded = jwt.encode(payload, private_key, algorithm)
    return encoded

def decode_jwt(
    token: str | bytes, 
    public_key: str = settings.auth_jwt.public_key_path.read_text(), 
    algorithm=settings.auth_jwt.algorithm
) -> str:
    decoded = jwt.decode(token, public_key, algorithms=[algorithm])
    return decoded
