from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from app.core.config import settings
from app.db.session import SessionLocal
from app.models.utente import Utente
from app.models.paziente import Paziente

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> Utente:
    cred_exc = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Credenziali non valide",
                            headers={"WWW-Authenticate": "Bearer"})
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise cred_exc
        user_id = int(user_id)
    except (JWTError, ValueError):
        raise cred_exc
    # Il ruolo si rilegge dal DB e non dal claim del token: una revoca ha
    # effetto immediato anziche' alla scadenza.
    user = db.query(Utente).first()
    if user is None:
        raise cred_exc
    return user


def require_role(*ruoli):
    def checker(user: Utente = Depends(get_current_user)) -> Utente:
        if user.ruolo not in ruoli:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permessi insufficienti")
        return user
    return checker


require_admin = require_role("admin")


def get_current_paziente(user: Utente = Depends(get_current_user),
                         db: Session = Depends(get_db)) -> Paziente:
    paziente = db.query(Paziente).filter(Paziente.utente_id == user.id).first()
    if paziente is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Profilo paziente non trovato")
    return paziente
