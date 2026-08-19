from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_user
from app.models.prestazione import Prestazione
from app.schemas.prestazione import PrestazioneOut

router = APIRouter()

@router.get("", response_model=List[PrestazioneOut])
def lista_prestazioni(db: Session = Depends(get_db), _=Depends(get_current_user)):
    return db.query(Prestazione).all()
