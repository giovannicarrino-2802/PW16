from sqlalchemy.orm import Session
from app.models.medico import Medico
from app.models.prestazione import Prestazione
from app.models.medico_prestazione import MedicoPrestazione


class MedicoRepository:
    """Accesso ai dati per Medico e per le associazioni medico-prestazione."""

    def __init__(self, db: Session):
        self.db = db

    # --- CRUD medico -------------------------------------------------------
    def list(self):
        return self.db.query(Medico).order_by(Medico.cognome, Medico.nome).all()

    def get(self, medico_id):
        return self.db.query(Medico).filter(Medico.id == medico_id).first()

    def crea(self, nome, cognome, specializzazione):
        medico = Medico(nome=nome, cognome=cognome, specializzazione=specializzazione)
        self.db.add(medico)
        self.db.commit()
        self.db.refresh(medico)
        return medico

    def aggiorna(self, medico, dati: dict):
        for campo, valore in dati.items():
            setattr(medico, campo, valore)
        self.db.commit()
        self.db.refresh(medico)
        return medico

    def elimina(self, medico):
        # Rimuove le associazioni prima del medico (le disponibilita cadono
        # in cascata tramite la relationship configurata sul modello).
        (self.db.query(MedicoPrestazione)
             .filter(MedicoPrestazione.medico_id == medico.id)
             .delete())
        self.db.delete(medico)
        self.db.commit()

    # --- Associazioni medico-prestazione ----------------------------------
    def prestazioni_di(self, medico_id):
        return (self.db.query(Prestazione)
                .join(MedicoPrestazione, MedicoPrestazione.prestazione_id == Prestazione.id)
                .filter(MedicoPrestazione.medico_id == medico_id)
                .order_by(Prestazione.nome)
                .all())

    def associazione(self, medico_id, prestazione_id):
        return (self.db.query(MedicoPrestazione)
                .filter(MedicoPrestazione.medico_id == medico_id,
                        MedicoPrestazione.prestazione_id == prestazione_id)
                .first())

    def associa(self, medico_id, prestazione_id):
        assoc = MedicoPrestazione(medico_id=medico_id, prestazione_id=prestazione_id)
        self.db.add(assoc)
        self.db.commit()
        self.db.refresh(assoc)
        return assoc

    def dissocia(self, assoc):
        self.db.delete(assoc)
        self.db.commit()

    def esegue(self, medico_id, prestazione_id) -> bool:
        return self.associazione(medico_id, prestazione_id) is not None
