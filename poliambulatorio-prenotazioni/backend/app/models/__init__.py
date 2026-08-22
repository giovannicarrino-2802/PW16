"""Registra tutti i modelli ORM in `Base.metadata` prima di `create_all`."""
from app.models.utente import Utente
from app.models.paziente import Paziente
from app.models.medico import Medico
from app.models.prestazione import Prestazione
from app.models.medico_prestazione import MedicoPrestazione
from app.models.disponibilita import Disponibilita
from app.models.appuntamento import Appuntamento
from app.models.audit_log import AuditLog

__all__ = [
    "Utente",
    "Paziente",
    "Medico",
    "Prestazione",
    "MedicoPrestazione",
    "Disponibilita",
    "Appuntamento",
    "AuditLog",
]
