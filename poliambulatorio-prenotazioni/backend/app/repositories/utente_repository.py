from sqlalchemy.orm import Session
from app.models.utente import Utente
from app.models.paziente import Paziente
from app.models.appuntamento import Appuntamento
from app.models.disponibilita import Disponibilita


class UtenteRepository:
    """Accesso ai dati per Utente e per il profilo Paziente collegato."""

    def __init__(self, db: Session):
        self.db = db

    # --- Utente ------------------------------------------------------------
    def list(self):
        return self.db.query(Utente).order_by(Utente.email).all()

    def get(self, utente_id):
        return self.db.query(Utente).filter(Utente.id == utente_id).first()

    def by_email(self, email):
        return self.db.query(Utente).filter(Utente.email == email).first()

    def crea(self, email, password_hash, ruolo):
        user = Utente(email=email, password_hash=password_hash, ruolo=ruolo)
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def aggiorna(self, user, dati: dict):
        for campo, valore in dati.items():
            setattr(user, campo, valore)
        self.db.commit()
        self.db.refresh(user)
        return user

    def elimina(self, user):
        """Elimina l'utente e, se presente, il profilo paziente con le sue
        prenotazioni (liberando i relativi slot)."""
        paz = self.paziente_by_utente(user.id)
        if paz is not None:
            apps = (self.db.query(Appuntamento)
                    .filter(Appuntamento.paziente_id == paz.id).all())
            for a in apps:
                slot = (self.db.query(Disponibilita)
                        .filter(Disponibilita.id == a.disponibilita_id).first())
                if slot is not None:
                    slot.occupato = False
                self.db.delete(a)
            self.db.delete(paz)
        self.db.delete(user)
        self.db.commit()

    # --- Paziente ----------------------------------------------------------
    def paziente_by_utente(self, utente_id):
        return self.db.query(Paziente).filter(Paziente.utente_id == utente_id).first()

    def paziente_by_cf(self, codice_fiscale):
        return self.db.query(Paziente).filter(Paziente.codice_fiscale == codice_fiscale).first()

    def crea_paziente(self, utente_id, nome, cognome, codice_fiscale, telefono=None,
                      data_nascita=None):
        paz = Paziente(utente_id=utente_id, nome=nome, cognome=cognome,
                       codice_fiscale=codice_fiscale, telefono=telefono,
                       data_nascita=data_nascita)
        self.db.add(paz)
        self.db.commit()
        self.db.refresh(paz)
        return paz

    def list_pazienti(self):
        return self.db.query(Paziente).order_by(Paziente.cognome, Paziente.nome).all()
