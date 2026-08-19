from app.models.audit_log import AuditLog

class AuditService:
    def __init__(self, db):
        self.db = db

    def log(self, utente_id, azione, entita, entita_id=None, dettagli=None):
        rec = AuditLog(utente_id=utente_id, azione=azione, entita=entita,
                       entita_id=entita_id, dettagli=dettagli)
        self.db.add(rec)
        self.db.commit()
