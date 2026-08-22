from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_paziente, require_role
from app.models.utente import Utente
from app.repositories.appuntamento_repository import AppuntamentoRepository
from app.services.appuntamento_service import AppuntamentoService
from app.services.audit_service import AuditService
from app.schemas.appuntamento import (AppuntamentoCreate, AppuntamentoOut,
                                      AppuntamentoUpdate, AppuntamentoPerPaziente,
                                      AppuntamentoAdminUpdate, AppuntamentoDettaglioOut)
from app.models.appuntamento import Appuntamento

router = APIRouter()

# Le eccezioni di dominio sollevate dai servizi (NotFound/Forbidden/Conflict/
# Validation) sono tradotte in risposte HTTP dagli exception handler registrati
# in `main.py`: i router non le intercettano.


def _service(db: Session) -> AppuntamentoService:
    return AppuntamentoService(AppuntamentoRepository(db), AuditService(db))


# --- Paziente --------------------------------------------------------------
@router.post("", response_model=AppuntamentoOut, status_code=201)
def prenota(data: AppuntamentoCreate, paziente=Depends(get_current_paziente),
            db: Session = Depends(get_db)):
    return _service(db).prenota(paziente.id, paziente.utente_id,
                                data.disponibilita_id, data.prestazione_id)


@router.get("", response_model=List[AppuntamentoOut])
def le_mie(paziente=Depends(get_current_paziente), db: Session = Depends(get_db)):
    return _service(db).le_mie(paziente.id)


@router.patch("/{app_id}", response_model=AppuntamentoOut)
def annulla(app_id: int, data: AppuntamentoUpdate, paziente=Depends(get_current_paziente),
            db: Session = Depends(get_db)):
    if data.stato != "annullata":
        raise HTTPException(status_code=422,
                            detail="Da questo endpoint e ammesso solo stato 'annullata'")
    return _service(db).annulla(paziente.utente_id, paziente.id, app_id)


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