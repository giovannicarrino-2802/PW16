from typing import List, Optional
from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session
from app.api.deps import get_db, require_admin
from app.models.utente import Utente
from app.repositories.disponibilita_repository import DisponibilitaRepository
from app.repositories.medico_repository import MedicoRepository
from app.services.disponibilita_service import DisponibilitaService
from app.services.audit_service import AuditService
from app.schemas.disponibilita import (DisponibilitaOut, DisponibilitaCreate,
                                        DisponibilitaUpdate, DisponibilitaBatchCreate,
                                        DisponibilitaBatchResult)

router = APIRouter()


def _service(db: Session) -> DisponibilitaService:
    return DisponibilitaService(DisponibilitaRepository(db), MedicoRepository(db), AuditService(db))


@router.get("", response_model=List[DisponibilitaOut])
def lista(medico_id: Optional[int] = None, db: Session = Depends(get_db),
          _: Utente = Depends(require_admin)):
    return _service(db).lista(medico_id)


@router.post("", response_model=DisponibilitaOut, status_code=201)
def crea(data: DisponibilitaCreate, db: Session = Depends(get_db),
         admin: Utente = Depends(require_admin)):
    return _service(db).crea(admin.id, data)


@router.post("/genera", response_model=DisponibilitaBatchResult, status_code=201)
def genera(data: DisponibilitaBatchCreate, db: Session = Depends(get_db),
           admin: Utente = Depends(require_admin)):
    creati, saltati = _service(db).genera(admin.id, data)
    return {"creati": creati, "creati_count": len(creati), "saltati": saltati}


@router.put("/{disponibilita_id}", response_model=DisponibilitaOut)
def aggiorna(disponibilita_id: int, data: DisponibilitaUpdate, db: Session = Depends(get_db),
             admin: Utente = Depends(require_admin)):
    return _service(db).aggiorna(admin.id, disponibilita_id, data)


@router.delete("/{disponibilita_id}", status_code=204)
def elimina(disponibilita_id: int, db: Session = Depends(get_db),
            admin: Utente = Depends(require_admin)):
    _service(db).elimina(admin.id, disponibilita_id)
    return Response(status_code=204)
