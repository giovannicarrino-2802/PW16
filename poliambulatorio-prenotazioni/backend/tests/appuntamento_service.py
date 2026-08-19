from app.services.exceptions import (  # noqa: F401  (ri-esportate per compatibilita)
    ConflictError,
    NotFoundError,
    ForbiddenError,
    ValidationError,
)


class AppuntamentoService:
    """Livello di business: applica le regole di prenotazione.

    Ciclo di vita di una prenotazione: `prenotata` e' l'unico stato attivo;
    `annullata` e `completata` sono stati terminali e non ammettono ulteriori
    transizioni. Solo una prenotazione attiva "possiede" il proprio slot: per
    questo le operazioni che liberano lo slot sono ammesse esclusivamente a
    partire dallo stato `prenotata`."""

    def __init__(self, repo, audit):
        self.repo = repo
        self.audit = audit

    def _valida_slot_prestazione(self, disponibilita_id, prestazione_id):
        """Controlli comuni: slot libero + prestazione esistente e associata al
        medico dello slot. Ritorna lo slot valido."""
        slot = self.repo.slot(disponibilita_id)
        if slot is None:
            raise NotFoundError("Slot inesistente")
        if slot.occupato:
            raise ConflictError("Slot non piu disponibile")
        if self.repo.prestazione(prestazione_id) is None:
            raise NotFoundError("Prestazione inesistente")
        if not self.repo.medico_esegue(slot.medico_id, prestazione_id):
            raise ValidationError(
                "La prestazione selezionata non e' associata al medico scelto")
        return slot

    def prenota(self, paziente_id, utente_id, disponibilita_id, prestazione_id):
        slot = self._valida_slot_prestazione(disponibilita_id, prestazione_id)
        app = self.repo.crea(paziente_id, slot, prestazione_id)
        self.audit.log(utente_id, "CREATE_APPUNTAMENTO", "appuntamento", app.id)
        return app

    def prenota_per(self, operatore_utente_id, paziente_id, disponibilita_id, prestazione_id):
        """Prenotazione effettuata dalla segreteria/admin per conto di un paziente."""
        if self.repo.paziente(paziente_id) is None:
            raise NotFoundError("Paziente inesistente")
        slot = self._valida_slot_prestazione(disponibilita_id, prestazione_id)
        app = self.repo.crea(paziente_id, slot, prestazione_id)
        self.audit.log(operatore_utente_id, "CREATE_APPUNTAMENTO", "appuntamento",
                       app.id, f"per paziente {paziente_id} (segreteria)")
        return app

    def le_mie(self, paziente_id):
        return self.repo.list_by_paziente(paziente_id)

    def tutti_dettaglio(self):
        """Agenda completa arricchita per segreteria/admin."""
        righe = self.repo.list_tutti_dettaglio()
        return [{
            "id": app.id,
            "paziente_id": app.paziente_id,
            "paziente_nome": f"{paz.nome} {paz.cognome}",
            "medico_id": app.medico_id,
            "medico_nome": f"{med.nome} {med.cognome}",
            "prestazione_id": app.prestazione_id,
            "prestazione_nome": prest.nome,
            "inizio": app.inizio,
            "fine": app.fine,
            "stato": app.stato,
        } for (app, paz, med, prest) in righe]

    def annulla(self, utente_id, paziente_id, app_id):
        app = self.repo.get(app_id)
        if app is None:
            raise NotFoundError("Appuntamento inesistente")
        if app.paziente_id != paziente_id:
            raise ForbiddenError("Non puoi modificare prenotazioni altrui")
        if app.stato == "completata":
            raise ConflictError("Una visita completata non e annullabile")
        if app.stato == "annullata":
            raise ConflictError("La prenotazione e gia annullata")
        app = self.repo.annulla(app)
        self.audit.log(utente_id, "CANCEL_APPUNTAMENTO", "appuntamento", app.id)
        return app

    # --- Operazioni di segreteria / admin su qualsiasi prenotazione --------
    def annulla_qualsiasi(self, utente_id, app_id):
        app = self.repo.get(app_id)
        if app is None:
            raise NotFoundError("Appuntamento inesistente")
        if app.stato == "completata":
            raise ConflictError("Una visita completata non e annullabile")
        if app.stato == "annullata":
            raise ConflictError("La prenotazione e gia annullata")
        app = self.repo.annulla(app)
        self.audit.log(utente_id, "CANCEL_APPUNTAMENTO", "appuntamento", app.id)
        return app

    def completa(self, utente_id, app_id):
        app = self.repo.get(app_id)
        if app is None:
            raise NotFoundError("Appuntamento inesistente")
        if app.stato == "annullata":
            raise ConflictError("Una visita annullata non puo' essere completata")
        app = self.repo.imposta_stato(app, "completata")
        self.audit.log(utente_id, "COMPLETE_APPUNTAMENTO", "appuntamento", app.id)
        return app

    def riprogramma(self, utente_id, app_id, nuovo_slot_id):
        app = self.repo.get(app_id)
        if app is None:
            raise NotFoundError("Appuntamento inesistente")
        if app.stato != "prenotata":
            # Uno slot e' "posseduto" solo da una prenotazione attiva: spostare
            # una prenotazione terminata liberebbe uno slot che nel frattempo
            # potrebbe appartenere a un'altra prenotazione.
            raise ConflictError("Sono riprogrammabili solo le prenotazioni attive")
        nuovo = self.repo.slot(nuovo_slot_id)
        if nuovo is None:
            raise NotFoundError("Slot inesistente")
        if nuovo.occupato and nuovo.id != app.disponibilita_id:
            raise ConflictError("Slot non piu disponibile")
        if not self.repo.medico_esegue(nuovo.medico_id, app.prestazione_id):
            raise ValidationError(
                "Il medico del nuovo slot non esegue la prestazione prenotata")
        app = self.repo.riprogramma(app, nuovo)
        self.audit.log(utente_id, "RESCHEDULE_APPUNTAMENTO", "appuntamento", app.id,
                       f"nuovo slot {nuovo_slot_id}")
        return app
