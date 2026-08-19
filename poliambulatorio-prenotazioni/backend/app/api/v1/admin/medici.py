from typing import List
from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session
from app.api.deps import get_db, require_admin
from app.models.utente import Utente
from app.repositories.medico_repository import MedicoRepository
from app.repositories.prestazione_repository import PrestazioneRepository
from app.services.medico_service import MedicoService
from app.services.audit_service import AuditService
from app.schemas.medico import MedicoOut, MedicoCreate, MedicoUpdate
from app.schemas.prestazione import PrestazioneOut
from app.schemas.medico_prestazione import AssociazioneCreate, MedicoPrestazioneOut

router = APIRouter()


def _service(db: Session) -> MedicoService:
    return MedicoService(MedicoRepository(db), PrestazioneRepository(db), AuditService(db))


# --- CRUD medici -----------------------------------------------------------
@router.get("", response_model=List[MedicoOut])
def lista(db: Session = Depends(get_db), _: Utente = Depends(require_admin)):
    return _service(db).lista()


@router.post("", response_model=MedicoOut, status_code=201)
def crea(data: MedicoCreate, db: Session = Depends(get_db),
         admin: Utente = Depends(require_admin)):
    return _service(db).crea(admin.id, data)


@router.put("/{medico_id}", response_model=MedicoOut)
def aggiorna(medico_id: int, data: MedicoUpdate, db: Session = Depends(get_db),
             admin: Utente = Depends(require_admin)):
    return _service(db).aggiorna(admin.id, medico_id, data)


@router.delete("/{medico_id}", status_code=204)
def elimina(medico_id: int, db: Session = Depends(get_db),
            admin: Utente = Depends(require_admin)):
    _service(db).elimina(admin.id, medico_id)
    return Response(status_code=204)


# --- Associazioni medico-prestazione --------------------------------------
@router.get("/{medico_id}/prestazioni", response_model=List[PrestazioneOut])
def prestazioni(medico_id: int, db: Session = Depends(get_db),
                _: Utente = Depends(require_admin)):
    return _service(db).prestazioni(medico_id)


@router.post("/{medico_id}/prestazioni", response_model=MedicoPrestazioneOut, status_code=201)
def associa(medico_id: int, data: AssociazioneCreate, db: Session = Depends(get_db),
            admin: Utente = Depends(require_admin)):
    return _service(db).associa(admin.id, medico_id, data.prestazione_id)


@router.delete("/{medico_id}/prestazioni/{prestazione_id}", status_code=204)
def dissocia(medico_id: int, prestazione_id: int, db: Session = Depends(get_db),
             admin: Utente = Depends(require_admin)):
    _service(db).dissocia(admin.id, medico_id, prestazione_id)
    return Response(status_code=204)
