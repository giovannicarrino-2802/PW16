from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_user
from app.core.security import verify_password, create_access_token
from app.models.utente import Utente
from app.schemas.auth import Token, UserOut

router = APIRouter()


@router.post("/login", response_model=Token)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(Utente).filter(Utente.email == form.username).first()
    if not user or not verify_password(form.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Email o password errate")
    return Token(access_token=create_access_token(user.id, user.ruolo))


@router.get("/me", response_model=UserOut)
def me(user: Utente = Depends(get_current_user)):
    """Ritorna l'utente autenticato: usato dal front-end per conoscere il
    ruolo e mostrare o nascondere l'area amministrativa."""
    return user
