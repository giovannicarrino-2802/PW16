from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_user
from app.models.medico import Medico
from app.repositories.appuntamento_repository import AppuntamentoRepository
from app.repositories.medico_repository import MedicoRepository
from app.schemas.medico import MedicoOut, SlotOut
from app.schemas.prestazione import PrestazioneRef

router = APIRouter()


@router.get("", response_model=List[MedicoOut])
def lista_medici(db: Session = Depends(get_db), _=Depends(get_current_user)):
    return db.query(Medico).all()


@router.get("/{medico_id}/disponibilita", response_model=List[SlotOut])
def disponibilita(medico_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    return AppuntamentoRepository(db).slot_liberi(medico_id)


@router.get("/{medico_id}/prestazioni", response_model=List[PrestazioneRef])
def prestazioni_del_medico(medico_id: int, db: Session = Depends(get_db),
                           _=Depends(get_current_user)):
    """Prestazioni erogabili dal medico selezionato (richiede autenticazione).

    Usato dal front-end per popolare la tendina delle prestazioni in base al
    medico scelto (relazione medico-prestazione)."""
    repo = MedicoRepository(db)
    if repo.get(medico_id) is None:
        raise HTTPException(status_code=404, detail="Medico inesistente")
    return repo.prestazioni_di(medico_id)
