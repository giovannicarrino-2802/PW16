from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_paziente, require_role
from app.models.utente import Utente
from app.repositories.appuntamento_repository import AppuntamentoRepository
from app.services.appuntamento_service import (AppuntamentoService, ConflictError,
                                               NotFoundError, ForbiddenError,
                                               ValidationError)
from app.services.audit_service import AuditService
from app.schemas.appuntamento import (AppuntamentoCreate, AppuntamentoOut,
                                      AppuntamentoUpdate, AppuntamentoPerPaziente,
                                      AppuntamentoAdminUpdate, AppuntamentoDettaglioOut)
from app.models.appuntamento import Appuntamento

router = APIRouter()


def _service(db: Session) -> AppuntamentoService:
    return AppuntamentoService(AppuntamentoRepository(db), AuditService(db))


# --- Paziente --------------------------------------------------------------
@router.post("", response_model=AppuntamentoOut, status_code=201)
def prenota(data: AppuntamentoCreate, paziente=Depends(get_current_paziente), db: Session = Depends(get_db)):
    try:
        return _service(db).prenota(paziente.id, paziente.utente_id, data.disponibilita_id, data.prestazione_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.get("", response_model=List[AppuntamentoOut])
def le_mie(paziente=Depends(get_current_paziente), db: Session = Depends(get_db)):
    return _service(db).le_mie(paziente.id)


@router.patch("/{app_id}", response_model=AppuntamentoOut)
def annulla(app_id: int, data: AppuntamentoUpdate, paziente=Depends(get_current_paziente),
            db: Session = Depends(get_db)):
    if data.stato != "annullata":
        raise HTTPException(status_code=422, detail="Da questo endpoint e ammesso solo stato 'annullata'")
    try:
        return _service(db).annulla(paziente.utente_id, paziente.id, app_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ForbiddenError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))


# --- Segreteria (operatore) / admin ---------------------------------------
@router.get("/tutti", response_model=List[AppuntamentoDettaglioOut])
def agenda_completa(db: Session = Depends(get_db),
                    _: Utente = Depends(require_role("operatore", "admin"))):
    """Agenda di tutte le prenotazioni, con nome paziente/medico/prestazione."""
    return _service(db).tutti_dettaglio()


@router.post("/operatore", response_model=AppuntamentoOut, status_code=201)
def prenota_per_paziente(data: AppuntamentoPerPaziente, db: Session = Depends(get_db),
                         operatore: Utente = Depends(require_role("operatore", "admin"))):
    """La segreteria prenota per conto di un paziente."""
    return _service(db).prenota_per(operatore.id, data.paziente_id,
                                    data.disponibilita_id, data.prestazione_id)


@router.patch("/tutti/{app_id}", response_model=AppuntamentoOut)
def modifica_qualsiasi(app_id: int, data: AppuntamentoAdminUpdate, db: Session = Depends(get_db),
                       operatore: Utente = Depends(require_role("operatore", "admin"))):
    """Segreteria/admin: riprogramma (disponibilita_id) oppure cambia stato
    (annullata/completata) di una qualsiasi prenotazione."""
    svc = _service(db)
    if data.disponibilita_id is not None:
        return svc.riprogramma(operatore.id, app_id, data.disponibilita_id)
    if data.stato == "annullata":
        return svc.annulla_qualsiasi(operatore.id, app_id)
    if data.stato == "completata":
        return svc.completa(operatore.id, app_id)
    raise HTTPException(status_code=422,
                        detail="Indicare 'disponibilita_id' (riprogramma) oppure "
                               "stato 'annullata'/'completata'")


# Alias storico mantenuto per compatibilita
@router.get("/admin/tutti", response_model=List[AppuntamentoOut])
def agenda_completa_legacy(db: Session = Depends(get_db),
                           _: Utente = Depends(require_role("operatore", "admin"))):
    return db.query(Appuntamento).order_by(Appuntamento.inizio).all()
