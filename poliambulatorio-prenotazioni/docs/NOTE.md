# Documentazione di progetto

Questa cartella raccoglie gli artefatti di design del PW16 (v2.0).

## Diagrammi
- `ER.md`             -> diagramma entita-relazione (Mermaid) del modello dati v2
- `uml/use-case.png`  -> attori (Paziente, Operatore, Admin) e casi d'uso *(da produrre)*
- `uml/class.png`     -> modello di dominio *(da produrre)*
- `uml/sequence-prenota.png` -> flusso "Prenota visita" *(da produrre)*

## API
La documentazione OpenAPI/Swagger e' generata automaticamente da FastAPI:
avvia il back-end e apri http://localhost:8000/docs (oppure /openapi.json).

## Mappa requisito -> endpoint -> test
- RF1 registrazione/login -> `/auth/register`, `/auth/login`, `/auth/me` -> `test_login_demo`, `test_me_ritorna_ruolo`
- RF2 ricerca disponibilita -> `/medici/{id}/disponibilita`
- RF3 prestazioni per medico -> `/medici/{id}/prestazioni` -> `test_prestazioni_del_medico_pubblico`
- RF4 prenotazione (validata) -> `POST /appuntamenti` -> `test_prenota_e_lista`, `test_slot_occupato_genera_conflitto`, `test_prenotazione_non_valida_bloccata`
- RF5 le mie prenotazioni / annulla -> `GET /appuntamenti`, `PATCH /appuntamenti/{id}`
- RF6 agenda operatore -> `GET /appuntamenti/admin/tutti`
- RF7 gestione medici (admin) -> `/admin/medici` -> `test_crud_medico`, `test_rbac_*`
- RF8 gestione prestazioni (admin) -> `/admin/prestazioni` -> `test_crud_prestazione`, `test_prestazione_validazione`
- RF9 gestione disponibilita (admin) -> `/admin/disponibilita` -> `test_crud_disponibilita`, `test_disponibilita_intervallo_non_valido`
- RF10 associazioni medico-prestazione -> `/admin/medici/{id}/prestazioni` -> `test_associazione_medico_prestazione`
- RF11 audit -> `AuditService` -> `test_audit_registra_operazioni_admin`
- RF12 segreteria: prenota per conto / agenda / modifica -> `/appuntamenti/operatore`, `/appuntamenti/tutti`, `PATCH /appuntamenti/tutti/{id}` -> `test_segreteria_prenota_per_paziente_e_modifica`
- RF13 gestione utenti (admin) -> `/admin/utenti` -> `test_crud_utente_operatore`, `test_crea_utente_paziente_con_profilo`, `test_utenti_rbac_e_self_delete`

## Ruoli (RBAC)
- **paziente**: prenota per se', vede/annulla le proprie prenotazioni.
- **operatore** (segreteria): prenota per conto dei pazienti, vede l'agenda di
  tutti e puo' annullare / completare / riprogrammare qualsiasi prenotazione.
- **admin**: tutto quanto sopra + gestione medici, prestazioni, associazioni,
  disponibilita e utenti.

## Azioni di audit registrate
CREATE/UPDATE/DELETE_MEDICO, CREATE/UPDATE/DELETE_PRESTAZIONE,
LINK/UNLINK_MEDICO_PRESTAZIONE, CREATE/UPDATE/DELETE_DISPONIBILITA,
CREATE/CANCEL/COMPLETE/RESCHEDULE_APPUNTAMENTO, CREATE/UPDATE/DELETE_UTENTE.

## Note di implementazione
- Le eccezioni di dominio (`services/exceptions.py`) sono mappate a codici HTTP
  centralmente in `main.py` (`404/403/409/400`).
- RBAC: `require_role(...)` / `require_admin` in `app/api/deps.py`.
- La relazione molti-a-molti e' modellata da `MedicoPrestazione`; la
  prenotazione verifica sempre `AppuntamentoRepository.medico_esegue(...)`.
