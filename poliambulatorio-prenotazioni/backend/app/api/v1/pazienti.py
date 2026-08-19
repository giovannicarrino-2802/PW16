from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api.deps import get_db, require_role
from app.models.utente import Utente
from app.repositories.utente_repository import UtenteRepository
from app.schemas.paziente import PazienteOut

router = APIRouter()


@router.get("", response_model=List[PazienteOut])
def lista_pazienti(db: Session = Depends(get_db),
                   _: Utente = Depends(require_role("operatore", "admin"))):
    """Elenco pazienti: usato dalla segreteria per prenotare per conto altrui."""
    return UtenteRepository(db).list_pazienti()
