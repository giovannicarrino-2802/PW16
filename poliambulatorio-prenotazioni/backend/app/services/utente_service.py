from app.core.security import hash_password
from app.services.exceptions import (NotFoundError, ConflictError,
                                     ValidationError, ForbiddenError)


class UtenteService:
    """Regole di business per la gestione amministrativa degli utenti (RBAC).

    Quando il ruolo e' 'paziente' viene creato anche il relativo profilo
    (Paziente) con nome, cognome e codice fiscale. Ogni operazione e' tracciata
    nell'audit log."""

    def __init__(self, repo, audit):
        self.repo = repo
        self.audit = audit

    def lista(self):
        return self.repo.list()

    def lista_pazienti(self):
        return self.repo.list_pazienti()

    def dettaglio(self, utente_id):
        user = self.repo.get(utente_id)
        if user is None:
            raise NotFoundError("Utente inesistente")
        return user

    def crea(self, admin_id, dati):
        if self.repo.by_email(dati.email) is not None:
            raise ConflictError("Email gia registrata")

        if dati.ruolo == "paziente":
            if not (dati.nome and dati.cognome and dati.codice_fiscale):
                raise ValidationError(
                    "Per un utente paziente servono nome, cognome e codice fiscale")
            if self.repo.paziente_by_cf(dati.codice_fiscale) is not None:
                raise ConflictError("Codice fiscale gia presente")

        user = self.repo.crea(dati.email, hash_password(dati.password), dati.ruolo)

        if dati.ruolo == "paziente":
            self.repo.crea_paziente(user.id, dati.nome, dati.cognome,
                                    dati.codice_fiscale, dati.telefono, dati.data_nascita)

        self.audit.log(admin_id, "CREATE_UTENTE", "utente", user.id,
                       f"{user.email} ({user.ruolo})")
        return user

    def aggiorna(self, admin_id, utente_id, dati):
        user = self.dettaglio(utente_id)
        cambi = dati.model_dump(exclude_unset=True)

        nuova_email = cambi.pop("email", None)
        if nuova_email and nuova_email != user.email:
            if self.repo.by_email(nuova_email) is not None:
                raise ConflictError("Email gia registrata")
            user.email = nuova_email

        nuova_password = cambi.pop("password", None)
        if nuova_password:
            user.password_hash = hash_password(nuova_password)

        if "ruolo" in cambi and cambi["ruolo"]:
            user.ruolo = cambi["ruolo"]

        user = self.repo.aggiorna(user, {})  # commit dei campi gia impostati
        self.audit.log(admin_id, "UPDATE_UTENTE", "utente", user.id,
                       f"email={user.email}, ruolo={user.ruolo}"
                       + (", password aggiornata" if nuova_password else ""))
        return user

    def elimina(self, admin_id, utente_id):
        user = self.dettaglio(utente_id)
        if user.id == admin_id:
            raise ForbiddenError("Non puoi eliminare il tuo stesso account")
        self.repo.elimina(user)
        self.audit.log(admin_id, "DELETE_UTENTE", "utente", utente_id)
