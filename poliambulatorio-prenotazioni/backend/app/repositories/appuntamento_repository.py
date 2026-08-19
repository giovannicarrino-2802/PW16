from datetime import datetime
from sqlalchemy.orm import Session
from app.models.disponibilita import Disponibilita
from app.models.appuntamento import Appuntamento
from app.models.prestazione import Prestazione
from app.models.medico import Medico
from app.models.paziente import Paziente
from app.models.medico_prestazione import MedicoPrestazione


class AppuntamentoRepository:
    def __init__(self, db: Session):
        self.db = db

    def slot(self, disponibilita_id):
        return self.db.query(Disponibilita).filter(Disponibilita.id == disponibilita_id).first()

    def slot_liberi(self, medico_id):
        # Gli orari degli slot sono datetime "naive" espressi nell'ora locale
        # dell'ambulatorio (sia quelli del seed sia quelli generati dall'area
        # amministrativa): il confronto usa quindi datetime.now() e non utcnow().
        now = datetime.now()
        return (self.db.query(Disponibilita)
                .filter(Disponibilita.medico_id == medico_id,
                        Disponibilita.occupato.is_(False),
                        Disponibilita.inizio >= now)
                .order_by(Disponibilita.inizio).all())

    def prestazione(self, prestazione_id):
        return self.db.query(Prestazione).filter(Prestazione.id == prestazione_id).first()

    def paziente(self, paziente_id):
        return self.db.query(Paziente).filter(Paziente.id == paziente_id).first()

    def medico_esegue(self, medico_id, prestazione_id) -> bool:
        """True se la prestazione e' associata al medico (medico_prestazione)."""
        return (self.db.query(MedicoPrestazione)
                .filter(MedicoPrestazione.medico_id == medico_id,
                        MedicoPrestazione.prestazione_id == prestazione_id)
                .first()) is not None

    def crea(self, paziente_id, slot, prestazione_id):
        app = Appuntamento(paziente_id=paziente_id, medico_id=slot.medico_id,
                           prestazione_id=prestazione_id, disponibilita_id=slot.id,
                           inizio=slot.inizio, fine=slot.fine, stato="prenotata")
        slot.occupato = True
        self.db.add(app)
        self.db.commit()
        self.db.refresh(app)
        return app

    def list_by_paziente(self, paziente_id):
        return (self.db.query(Appuntamento)
                .filter(Appuntamento.paziente_id == paziente_id)
                .order_by(Appuntamento.inizio).all())

    def get(self, app_id):
        return self.db.query(Appuntamento).filter(Appuntamento.id == app_id).first()

    def annulla(self, app):
        app.stato = "annullata"
        slot = self.slot(app.disponibilita_id)
        if slot:
            slot.occupato = False
        self.db.commit()
        self.db.refresh(app)
        return app

    def imposta_stato(self, app, stato):
        app.stato = stato
        self.db.commit()
        self.db.refresh(app)
        return app

    def list_tutti_dettaglio(self):
        """Tutte le prenotazioni con i dati di paziente, medico e prestazione
        (una sola query con join). Ordine: piu' recenti prima."""
        return (self.db.query(Appuntamento, Paziente, Medico, Prestazione)
                .join(Paziente, Paziente.id == Appuntamento.paziente_id)
                .join(Medico, Medico.id == Appuntamento.medico_id)
                .join(Prestazione, Prestazione.id == Appuntamento.prestazione_id)
                .order_by(Appuntamento.inizio.desc())
                .all())

    def riprogramma(self, app, nuovo_slot):
        """Sposta la prenotazione su un nuovo slot: libera il vecchio, occupa il
        nuovo e aggiorna medico/orari."""
        vecchio = self.slot(app.disponibilita_id)
        if vecchio and vecchio.id != nuovo_slot.id:
            vecchio.occupato = False
        nuovo_slot.occupato = True
        app.medico_id = nuovo_slot.medico_id
        app.disponibilita_id = nuovo_slot.id
        app.inizio = nuovo_slot.inizio
        app.fine = nuovo_slot.fine
        app.stato = "prenotata"
        self.db.commit()
        self.db.refresh(app)
        return app