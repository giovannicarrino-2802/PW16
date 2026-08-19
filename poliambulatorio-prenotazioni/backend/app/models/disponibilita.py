from sqlalchemy import Column, Integer, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base


class Disponibilita(Base):
    __tablename__ = "disponibilita"
    id = Column(Integer, primary_key=True)
    medico_id = Column(Integer, ForeignKey("medico.id"), nullable=False, index=True)
    inizio = Column(DateTime, nullable=False)
    fine = Column(DateTime, nullable=False)
    occupato = Column(Boolean, nullable=False, default=False)

    medico = relationship("Medico", back_populates="disponibilita")
