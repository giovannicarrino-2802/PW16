from sqlalchemy import Column, Integer, ForeignKey, UniqueConstraint
from app.db.base import Base


class MedicoPrestazione(Base):
    """Associazione molti-a-molti Medico-Prestazione; la coppia e' unica."""
    __tablename__ = "medico_prestazione"

    id = Column(Integer, primary_key=True)
    medico_id = Column(Integer, ForeignKey("medico.id"), nullable=False, index=True)
    prestazione_id = Column(Integer, ForeignKey("prestazione.id"), nullable=False, index=True)

    __table_args__ = (
        UniqueConstraint("medico_id", "prestazione_id", name="uq_medico_prestazione"),
    )
