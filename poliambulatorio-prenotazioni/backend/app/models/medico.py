from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.db.base import Base


class Medico(Base):
    __tablename__ = "medico"
    id = Column(Integer, primary_key=True)
    nome = Column(String, nullable=False)
    cognome = Column(String, nullable=False)
    specializzazione = Column(String, nullable=False)

    # Relazione molti-a-molti con Prestazione tramite medico_prestazione
    prestazioni = relationship(
        "Prestazione",
        secondary="medico_prestazione",
        back_populates="medici",
    )
    # Slot di disponibilita del medico (cancellati con il medico)
    disponibilita = relationship(
        "Disponibilita",
        back_populates="medico",
        cascade="all, delete-orphan",
    )
