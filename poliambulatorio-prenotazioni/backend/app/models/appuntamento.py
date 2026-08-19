from sqlalchemy import Column, Integer, DateTime, String, ForeignKey
from datetime import datetime
from app.db.base import Base

class Appuntamento(Base):
    __tablename__ = "appuntamento"
    id = Column(Integer, primary_key=True)
    paziente_id = Column(Integer, ForeignKey("paziente.id"), nullable=False)
    medico_id = Column(Integer, ForeignKey("medico.id"), nullable=False)
    prestazione_id = Column(Integer, ForeignKey("prestazione.id"), nullable=False)
    disponibilita_id = Column(Integer, ForeignKey("disponibilita.id"), nullable=False)
    inizio = Column(DateTime, nullable=False)
    fine = Column(DateTime, nullable=False)
    stato = Column(String, nullable=False, default="prenotata")
    # Ora locale dell'ambulatorio, come tutti i datetime persistiti.
    creato_il = Column(DateTime, default=datetime.now)
