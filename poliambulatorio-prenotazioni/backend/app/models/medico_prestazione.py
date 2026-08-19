from sqlalchemy import Column, Integer, ForeignKey, UniqueConstraint
from app.db.base import Base


class MedicoPrestazione(Base):
    """Tabella di associazione molti-a-molti tra Medico e Prestazione.

    Un medico puo' eseguire piu' prestazioni e una prestazione puo' essere
    eseguita da piu' medici. La coppia (medico_id, prestazione_id) e' unica.
    """
    __tablename__ = "medico_prestazione"

    id = Column(Integer, primary_key=True)
    medico_id = Column(Integer, ForeignKey("medico.id"), nullable=False, index=True)
    prestazione_id = Column(Integer, ForeignKey("prestazione.id"), nullable=False, index=True)

    __table_args__ = (
        UniqueConstraint("medico_id", "prestazione_id", name="uq_medico_prestazione"),
    )
