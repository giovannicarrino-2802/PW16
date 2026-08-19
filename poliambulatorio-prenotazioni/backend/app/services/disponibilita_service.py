from datetime import datetime, timedelta, time
from app.services.exceptions import NotFoundError, ConflictError, ValidationError


class DisponibilitaService:
    """Regole di business per la gestione degli slot di disponibilita."""

    def __init__(self, repo, medico_repo, audit):
        self.repo = repo
        self.medici = medico_repo
        self.audit = audit

    def lista(self, medico_id=None):
        return self.repo.list(medico_id)

    def dettaglio(self, disponibilita_id):
        slot = self.repo.get(disponibilita_id)
        if slot is None:
            raise NotFoundError("Slot inesistente")
        return slot

    def _valida_intervallo(self, inizio, fine):
        if fine <= inizio:
            raise ValidationError("La fine deve essere successiva all'inizio")

    def crea(self, utente_id, dati):
        if self.medici.get(dati.medico_id) is None:
            raise NotFoundError("Medico inesistente")
        self._valida_intervallo(dati.inizio, dati.fine)
        if self.repo.sovrapposti(dati.medico_id, dati.inizio, dati.fine):
            raise ConflictError("Slot sovrapposto a un altro dello stesso medico")
        slot = self.repo.crea(dati.medico_id, dati.inizio, dati.fine)
        self.audit.log(utente_id, "CREATE_DISPONIBILITA", "disponibilita", slot.id,
                       f"medico={slot.medico_id} {slot.inizio}-{slot.fine}")
        return slot

    def aggiorna(self, utente_id, disponibilita_id, dati):
        slot = self.dettaglio(disponibilita_id)
        cambi = dati.model_dump(exclude_unset=True)
        medico_id = cambi.get("medico_id", slot.medico_id)
        inizio = cambi.get("inizio", slot.inizio)
        fine = cambi.get("fine", slot.fine)
        if "medico_id" in cambi and self.medici.get(medico_id) is None:
            raise NotFoundError("Medico inesistente")
        self._valida_intervallo(inizio, fine)
        if self.repo.sovrapposti(medico_id, inizio, fine, escludi_id=slot.id):
            raise ConflictError("Slot sovrapposto a un altro dello stesso medico")
        slot = self.repo.aggiorna(slot, cambi)
        self.audit.log(utente_id, "UPDATE_DISPONIBILITA", "disponibilita", slot.id, str(cambi))
        return slot

    def elimina(self, utente_id, disponibilita_id):
        slot = self.dettaglio(disponibilita_id)
        if slot.occupato:
            raise ConflictError("Impossibile eliminare uno slot gia prenotato")
        self.repo.elimina(slot)
        self.audit.log(utente_id, "DELETE_DISPONIBILITA", "disponibilita", disponibilita_id)

    def genera(self, utente_id, dati):
        """Genera in blocco slot ricorrenti evitando le sovrapposizioni con slot
        gia presenti (e all'interno del batch stesso). Ritorna (creati, saltati)."""
        if self.medici.get(dati.medico_id) is None:
            raise NotFoundError("Medico inesistente")

        h1, m1 = map(int, dati.ora_inizio.split(":"))
        h2, m2 = map(int, dati.ora_fine.split(":"))
        min_inizio, min_fine = h1 * 60 + m1, h2 * 60 + m2
        if min_fine <= min_inizio:
            raise ValidationError("L'ora di fine deve essere successiva all'ora di inizio")
        if dati.durata_min > (min_fine - min_inizio):
            raise ValidationError("La durata supera la finestra oraria indicata")

        giorni = set(dati.giorni)
        # Slot gia esistenti nel periodo, per il controllo sovrapposizioni (una sola query)
        range_dal = datetime.combine(dati.data_inizio, time(0, 0))
        range_al = datetime.combine(dati.data_fine, time(0, 0)) + timedelta(days=1)
        occupati = [(s.inizio, s.fine) for s in self.repo.nel_range(dati.medico_id, range_dal, range_al)]

        def si_sovrappone(ini, fin):
            return any(ini < of and fin > oi for (oi, of) in occupati)

        accettati, saltati = [], 0
        giorno = dati.data_inizio
        while giorno <= dati.data_fine:
            if giorno.weekday() in giorni:
                minuto = min_inizio
                while minuto + dati.durata_min <= min_fine:
                    ini = datetime(giorno.year, giorno.month, giorno.day, minuto // 60, minuto % 60)
                    fin = ini + timedelta(minutes=dati.durata_min)
                    if si_sovrappone(ini, fin):
                        saltati += 1
                    else:
                        accettati.append((dati.medico_id, ini, fin))
                        occupati.append((ini, fin))  # evita duplicati nel batch
                    minuto += dati.durata_min
            giorno += timedelta(days=1)

        creati = self.repo.crea_molti(accettati) if accettati else []
        self.audit.log(utente_id, "CREATE_DISPONIBILITA", "disponibilita", None,
                       f"batch medico={dati.medico_id}: {len(creati)} creati, {saltati} saltati")
        return creati, saltati
