from app.services.exceptions import NotFoundError


class PrestazioneService:
    """Regole di business per la gestione amministrativa delle prestazioni."""

    def __init__(self, repo, audit):
        self.repo = repo
        self.audit = audit

    def lista(self):
        return self.repo.list()

    def dettaglio(self, prestazione_id):
        prest = self.repo.get(prestazione_id)
        if prest is None:
            raise NotFoundError("Prestazione inesistente")
        return prest

    def crea(self, utente_id, dati):
        prest = self.repo.crea(dati.nome, dati.durata_min, dati.prezzo)
        self.audit.log(utente_id, "CREATE_PRESTAZIONE", "prestazione", prest.id,
                       f"{prest.nome} ({prest.durata_min} min, {prest.prezzo} EUR)")
        return prest

    def aggiorna(self, utente_id, prestazione_id, dati):
        prest = self.dettaglio(prestazione_id)
        cambi = dati.model_dump(exclude_unset=True)
        if cambi:
            prest = self.repo.aggiorna(prest, cambi)
        self.audit.log(utente_id, "UPDATE_PRESTAZIONE", "prestazione", prest.id, str(cambi))
        return prest

    def elimina(self, utente_id, prestazione_id):
        prest = self.dettaglio(prestazione_id)
        self.repo.elimina(prest)
        self.audit.log(utente_id, "DELETE_PRESTAZIONE", "prestazione", prestazione_id)
