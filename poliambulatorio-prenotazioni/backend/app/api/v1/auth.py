from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_user
from app.core.security import hash_password, verify_password, create_access_token
from app.models.utente import Utente
from app.models.paziente import Paziente
from app.schemas.auth import RegisterRequest, Token, UserOut

router = APIRouter()


@router.post("/register", response_model=UserOut, status_code=201)
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    if db.query(Utente).filter(Utente.email == data.email).first():
        raise HTTPException(status_code=409, detail="Email gia registrata")
    user = Utente(email=data.email, password_hash=hash_password(data.password), ruolo="paziente")
    db.add(user); db.commit(); db.refresh(user)
    db.add(Paziente(utente_id=user.id, nome=data.nome, cognome=data.cognome,
                    codice_fiscale=data.codice_fiscale, telefono=data.telefono,
                    data_nascita=data.data_nascita))
    db.commit()
    return user


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
