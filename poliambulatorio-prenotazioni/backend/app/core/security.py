from datetime import datetime, timedelta
import bcrypt
from jose import jwt
from app.core.config import settings

# Hashing password con bcrypt "puro" (senza passlib): evita l'incompatibilita
# tra passlib 1.7 e bcrypt >= 4.1. bcrypt accetta al massimo 72 byte, quindi la
# password viene troncata in modo sicuro.

def _to72(password):
    if isinstance(password, str):
        password = password.encode("utf-8")
    return password[:72]

def hash_password(password):
    return bcrypt.hashpw(_to72(password), bcrypt.gensalt()).decode("utf-8")

def verify_password(plain, hashed):
    if isinstance(hashed, str):
        hashed = hashed.encode("utf-8")
    try:
        return bcrypt.checkpw(_to72(plain), hashed)
    except ValueError:
        return False

def create_access_token(subject, ruolo):
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": str(subject), "ruolo": ruolo, "exp": expire}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
