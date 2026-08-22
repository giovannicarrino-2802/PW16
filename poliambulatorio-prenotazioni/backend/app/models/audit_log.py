from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from datetime import datetime
from app.db.base import Base

class AuditLog(Base):
    __tablename__ = "audit_log"
    id = Column(Integer, primary_key=True)
    utente_id = Column(Integer, ForeignKey("utente.id"))
    azione = Column(String, nullable=False)
    entita = Column(String, nullable=False)
    entita_id = Column(Integer)
    dettagli = Column(String)
    # ora locale (cfr. docs/NOTE.md)
    ts = Column(DateTime, default=datetime.now)
