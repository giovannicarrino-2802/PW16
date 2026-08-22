from app.services.exceptions import NotFoundError, ConflictError


class MedicoService:
    """Regole di business per la gestione amministrativa dei medici e delle
    associazioni medico-prestazione. Ogni operazione di scrittura viene
    tracciata tramite il servizio di audit."""

    def __init__(self, medico_repo, prestazione_repo, audit):
        self.repo = medico_repo
        self.prestazione_repo = prestazione_repo
        self.audit = audit

    # --- CRUD medico -------------------------------------------------------
    def lista(self):
        return self.repo.list()

    def dettaglio(self, medico_id):
        medico = self.repo.get(medico_id)
        if medico is None:
            raise NotFoundError("Medico inesistente")
        return medico

    def crea(self, utente_id, dati):
        medico = self.repo.crea(dati.nome, dati.cognome, dati.specializzazione)
        self.audit.log(utente_id, "CREATE_MEDICO", "medico", medico.id,
                       f"{medico.nome} {medico.cognome} ({medico.specializzazione})")
        return medico

    def aggiorna(self, utente_id, medico_id, dati):
        medico = self.dettaglio(medico_id)
        cambi = dati.model_dump(exclude_unset=True)
        if cambi:
            medico = self.repo.aggiorna(medico, cambi)
        self.audit.log(utente_id, "UPDATE_MEDICO", "medico", medico.id, str(cambi))
        return medico

    def elimina(self, utente_id, medico_id):
        medico = self.dettaglio(medico_id)
        self.repo.elimina(medico)
        self.audit.log(utente_id, "DELETE_MEDICO", "medico", medico_id)

    # --- Associazioni medico-prestazione ----------------------------------
    def prestazioni(self, medico_id):
        self.dettaglio(medico_id)  # 404 se il medico non esiste
        return self.repo.prestazioni_di(medico_id)

    def associa(self, utente_id, medico_id, prestazione_id):
        self.dettaglio(medico_id)
        if self.prestazione_repo.get(prestazione_id) is None:
            raise NotFoundError("Prestazione inesistente")
        if self.repo.esegue(medico_id, prestazione_id):
            raise ConflictError("Associazione gia esistente")
        assoc = self.repo.associa(medico_id, prestazione_id)
        self.audit.log(utente_id, "LINK_MEDICO_PRESTAZIONE", "medico_prestazione",
                       assoc.id, f"medico={medico_id}, prestazione={prestazione_id}")
        return assoc

    def dissocia(self, utente_id, medico_id, prestazione_id):
        assoc = self.repo.associazione(medico_id, prestazione_id)
        if assoc is None:
            raise NotFoundError("Associazione inesistente")
        assoc_id = assoc.id
        self.repo.dissocia(assoc)
        self.audit.log(utente_id, "UNLINK_MEDICO_PRESTAZIONE", "medico_prestazione",
                       assoc_id, f"medico={medico_id}, prestazione={prestazione_id}")
