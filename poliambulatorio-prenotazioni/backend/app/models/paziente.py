from sqlalchemy import Column, Integer, String, Date, ForeignKey
from app.db.base import Base

class Paziente(Base):
    __tablename__ = "paziente"
    id = Column(Integer, primary_key=True)
    utente_id = Column(Integer, ForeignKey("utente.id"), unique=True, nullable=False)
    nome = Column(String, nullable=False)
    cognome = Column(String, nullable=False)
    codice_fiscale = Column(String, unique=True, nullable=False)
    telefono = Column(String)
    data_nascita = Column(Date)
