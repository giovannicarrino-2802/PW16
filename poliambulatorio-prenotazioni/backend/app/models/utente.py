from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from app.db.base import Base

class Utente(Base):
    __tablename__ = "utente"
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    ruolo = Column(String, nullable=False, default="paziente")
    # Ora locale dell'ambulatorio, come tutti i datetime persistiti.
    creato_il = Column(DateTime, default=datetime.now)
