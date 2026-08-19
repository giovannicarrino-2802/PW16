from sqlalchemy import Column, Integer, String, Float
from sqlalchemy.orm import relationship
from app.db.base import Base


class Prestazione(Base):
    __tablename__ = "prestazione"
    id = Column(Integer, primary_key=True)
    nome = Column(String, nullable=False)
    durata_min = Column(Integer, nullable=False)
    prezzo = Column(Float, nullable=False)

    # Relazione molti-a-molti con Medico tramite medico_prestazione
    medici = relationship(
        "Medico",
        secondary="medico_prestazione",
        back_populates="prestazioni",
    )
