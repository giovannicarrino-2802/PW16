from typing import List
from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session
from app.api.deps import get_db, require_admin
from app.models.utente import Utente
from app.repositories.utente_repository import UtenteRepository
from app.services.utente_service import UtenteService
from app.services.audit_service import AuditService
from app.schemas.utente import UtenteCreate, UtenteUpdate, UtenteAdminOut

router = APIRouter()


def _service(db: Session) -> UtenteService:
    return UtenteService(UtenteRepository(db), AuditService(db))


@router.get("", response_model=List[UtenteAdminOut])
def lista(db: Session = Depends(get_db), _: Utente = Depends(require_admin)):
    return _service(db).lista()


@router.post("", response_model=UtenteAdminOut, status_code=201)
def crea(data: UtenteCreate, db: Session = Depends(get_db),
         admin: Utente = Depends(require_admin)):
    return _service(db).crea(admin.id, data)


@router.put("/{utente_id}", response_model=UtenteAdminOut)
def aggiorna(utente_id: int, data: UtenteUpdate, db: Session = Depends(get_db),
             admin: Utente = Depends(require_admin)):
    return _service(db).aggiorna(admin.id, utente_id, data)


@router.delete("/{utente_id}", status_code=204)
def elimina(utente_id: int, db: Session = Depends(get_db),
            admin: Utente = Depends(require_admin)):
    _service(db).elimina(admin.id, utente_id)
    return Response(status_code=204)
