from sqlalchemy.orm import Session
from app.models.prestazione import Prestazione
from app.models.medico_prestazione import MedicoPrestazione


class PrestazioneRepository:
    """Accesso ai dati per Prestazione."""

    def __init__(self, db: Session):
        self.db = db

    def list(self):
        return self.db.query(Prestazione).order_by(Prestazione.nome).all()

    def get(self, prestazione_id):
        return self.db.query(Prestazione).filter(Prestazione.id == prestazione_id).first()

    def crea(self, nome, durata_min, prezzo):
        prest = Prestazione(nome=nome, durata_min=durata_min, prezzo=prezzo)
        self.db.add(prest)
        self.db.commit()
        self.db.refresh(prest)
        return prest

    def aggiorna(self, prest, dati: dict):
        for campo, valore in dati.items():
            setattr(prest, campo, valore)
        self.db.commit()
        self.db.refresh(prest)
        return prest

    def elimina(self, prest):
        (self.db.query(MedicoPrestazione)
             .filter(MedicoPrestazione.prestazione_id == prest.id)
             .delete())
        self.db.delete(prest)
        self.db.commit()
