from typing import List
from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session
from app.api.deps import get_db, require_admin
from app.models.utente import Utente
from app.repositories.prestazione_repository import PrestazioneRepository
from app.services.prestazione_service import PrestazioneService
from app.services.audit_service import AuditService
from app.schemas.prestazione import PrestazioneOut, PrestazioneCreate, PrestazioneUpdate

router = APIRouter()


def _service(db: Session) -> PrestazioneService:
    return PrestazioneService(PrestazioneRepository(db), AuditService(db))


@router.get("", response_model=List[PrestazioneOut])
def lista(db: Session = Depends(get_db), _: Utente = Depends(require_admin)):
    return _service(db).lista()


@router.post("", response_model=PrestazioneOut, status_code=201)
def crea(data: PrestazioneCreate, db: Session = Depends(get_db),
         admin: Utente = Depends(require_admin)):
    return _service(db).crea(admin.id, data)


@router.put("/{prestazione_id}", response_model=PrestazioneOut)
def aggiorna(prestazione_id: int, data: PrestazioneUpdate, db: Session = Depends(get_db),
             admin: Utente = Depends(require_admin)):
    return _service(db).aggiorna(admin.id, prestazione_id, data)


@router.delete("/{prestazione_id}", status_code=204)
def elimina(prestazione_id: int, db: Session = Depends(get_db),
            admin: Utente = Depends(require_admin)):
    _service(db).elimina(admin.id, prestazione_id)
    return Response(status_code=204)
