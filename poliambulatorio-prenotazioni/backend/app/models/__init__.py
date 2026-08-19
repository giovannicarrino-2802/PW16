"""Registrazione dei modelli ORM nel metadata di SQLAlchemy.

Importare questo package (o i singoli moduli) garantisce che tutte le
tabelle siano note a `Base.metadata` prima della configurazione dei mapper
e della `create_all`.
"""
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
