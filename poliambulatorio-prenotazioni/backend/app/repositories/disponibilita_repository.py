from sqlalchemy.orm import Session
from app.models.disponibilita import Disponibilita


class DisponibilitaRepository:
    """Accesso ai dati per gli slot di Disponibilita."""

    def __init__(self, db: Session):
        self.db = db

    def list(self, medico_id=None):
        query = self.db.query(Disponibilita)
        if medico_id is not None:
            query = query.filter(Disponibilita.medico_id == medico_id)
        return query.order_by(Disponibilita.inizio).all()

    def get(self, disponibilita_id):
        return (self.db.query(Disponibilita)
                .filter(Disponibilita.id == disponibilita_id)
                .first())

    def crea(self, medico_id, inizio, fine):
        slot = Disponibilita(medico_id=medico_id, inizio=inizio, fine=fine, occupato=False)
        self.db.add(slot)
        self.db.commit()
        self.db.refresh(slot)
        return slot

    def aggiorna(self, slot, dati: dict):
        for campo, valore in dati.items():
            setattr(slot, campo, valore)
        self.db.commit()
        self.db.refresh(slot)
        return slot

    def elimina(self, slot):
        self.db.delete(slot)
        self.db.commit()

    def crea_molti(self, intervalli):
        """Inserisce piu' slot in un'unica transazione.

        `intervalli` e' una lista di tuple (medico_id, inizio, fine)."""
        objs = [Disponibilita(medico_id=m, inizio=i, fine=f, occupato=False)
                for (m, i, f) in intervalli]
        self.db.add_all(objs)
        self.db.commit()
        for o in objs:
            self.db.refresh(o)
        return objs

    def nel_range(self, medico_id, dal, al):
        """Slot del medico che intersecano l'intervallo [dal, al)."""
        return (self.db.query(Disponibilita)
                .filter(Disponibilita.medico_id == medico_id,
                        Disponibilita.inizio < al,
                        Disponibilita.fine > dal)
                .all())

    def sovrapposti(self, medico_id, inizio, fine, escludi_id=None):
        """Ritorna gli slot dello stesso medico che si sovrappongono all'intervallo."""
        query = (self.db.query(Disponibilita)
                 .filter(Disponibilita.medico_id == medico_id,
                         Disponibilita.inizio < fine,
                         Disponibilita.fine > inizio))
        if escludi_id is not None:
            query = query.filter(Disponibilita.id != escludi_id)
        return query.all()
