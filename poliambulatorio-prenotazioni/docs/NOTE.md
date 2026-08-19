# Documentazione di progetto

Questa cartella raccoglie gli artefatti di design del PW16.

## Diagrammi
- `ER.md`             -> diagramma entita-relazione (Mermaid) del modello dati
- `uml/use-case.png`  -> attori (Paziente, Operatore, Admin) e casi d'uso *(da produrre)*
- `uml/class.png`     -> modello di dominio *(da produrre)*
- `uml/sequence-prenota.png` -> flusso "Prenota visita" *(da produrre)*

## API
La documentazione OpenAPI/Swagger e' generata automaticamente da FastAPI:
avvia il back-end e apri http://localhost:8000/docs (oppure /openapi.json).

## Mappa requisito -> endpoint -> test
- RF1 registrazione/login -> `/auth/register`, `/auth/login`, `/auth/me` -> `test_login_demo`, `test_me_ritorna_ruolo`
- RF2 ricerca disponibilita -> `/medici/{id}/disponibilita`
- RF3 prestazioni per medico -> `/medici/{id}/prestazioni` -> `test_prestazioni_del_medico`
- RF4 prenotazione (validata) -> `POST /appuntamenti` -> `test_prenota_e_lista`, `test_slot_occupato_genera_conflitto`, `test_prenotazione_non_valida_bloccata`
- RF5 le mie prenotazioni / annulla -> `GET /appuntamenti`, `PATCH /appuntamenti/{id}`
- RF6 agenda operatore -> `GET /appuntamenti/tutti`, `GET /appuntamenti/admin/tutti`
- RF7 gestione medici (admin) -> `/admin/medici` -> `test_crud_medico`, `test_rbac_*`
- RF8 gestione prestazioni (admin) -> `/admin/prestazioni` -> `test_crud_prestazione`, `test_prestazione_validazione`
- RF9 gestione disponibilita (admin) -> `/admin/disponibilita` -> `test_crud_disponibilita`, `test_disponibilita_intervallo_non_valido`
- RF10 associazioni medico-prestazione -> `/admin/medici/{id}/prestazioni` -> `test_associazione_medico_prestazione`
- RF11 audit -> `AuditService` -> `test_audit_registra_operazioni_admin`
- RF12 segreteria: prenota per conto / agenda / modifica -> `/appuntamenti/operatore`, `/appuntamenti/tutti`, `PATCH /appuntamenti/tutti/{id}` -> `test_segreteria_prenota_per_paziente_e_modifica`
- RF13 gestione utenti (admin) -> `/admin/utenti` -> `test_crud_utente_operatore`, `test_crea_utente_paziente_con_profilo`, `test_utenti_rbac_e_self_delete`
- RF14 stati terminali della prenotazione -> `PATCH /appuntamenti/{id}`, `PATCH /appuntamenti/tutti/{id}` -> `test_paziente_non_annulla_due_volte`, `test_segreteria_non_annulla_due_volte`, `test_riprogramma_solo_prenotazioni_attive`, `test_riprogramma_prenotazione_completata`

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

## Ciclo di vita della prenotazione
`prenotata` e' l'unico stato attivo; `annullata` e `completata` sono **stati
terminali** e non ammettono ulteriori transizioni (annullamento ripetuto o
riprogrammazione rispondono `409`). Il vincolo esiste perche' solo una
prenotazione attiva "possiede" il proprio slot: agire su una prenotazione gia
terminata libererebbe uno slot che nel frattempo puo' appartenere a un'altra
prenotazione. Copertura: `tests/test_stati_prenotazione.py`.

## Limiti noti
Scelte consapevoli o vincoli non risolti nella soluzione, elencati per
trasparenza. Non impediscono l'uso previsto del prototipo.

- **Integrita referenziale non applicata dal database.** SQLite non verifica le
  foreign key se non viene attivato `PRAGMA foreign_keys=ON`, qui non impostato.
  L'eliminazione di un medico o di una prestazione dall'area amministrativa non
  controlla le dipendenze: restano righe orfane in `medico_prestazione`,
  `disponibilita` e `appuntamento`. Poiche' l'agenda (`list_tutti_dettaglio`)
  usa una join su medico e prestazione, le prenotazioni orfane non compaiono
  piu' nell'elenco anziche' generare un errore. Mitigazione operativa: eliminare
  medici e prestazioni solo se non hanno prenotazioni collegate.

- **Chiave di firma dei token con valore predefinito.** `SECRET_KEY` viene letta
  dalla variabile d'ambiente omonima, ma in sua assenza `core/config.py` ricade
  su un valore fisso di sviluppo (`"dev-secret-cambia-in-produzione"`). Questo
  consente di avviare la demo e la suite di test senza configurazione, ma in un
  ambiente reale la variabile va impostata: chi conoscesse il default potrebbe
  altrimenti forgiare token JWT validi per qualsiasi utente e ruolo.

- **Audit log conservato oltre la vita dell'utente.** L'eliminazione di un utente
  rimuove il profilo paziente e le sue prenotazioni, ma non i record di
  `audit_log`, che restano con un `utente_id` non piu' risolvibile. E' una scelta
  intenzionale: cancellare la tracciabilita delle azioni passate insieme
  all'utente vanificherebbe lo scopo del log. Chi consulta l'audit deve quindi
  gestire il caso di utente non piu' esistente.

## Note di implementazione
- Tutti i datetime persistiti (`inizio`, `fine`, `creato_il`, `ts`) sono naive e
  rappresentano l'**ora locale dell'ambulatorio**: un solo orologio per l'intero
  database, cosi' un record di audit e' direttamente confrontabile con l'orario
  di una prenotazione. Unica eccezione il claim `exp` del token JWT, che per
  specifica e' un timestamp UTC e non viene mai confrontato con i dati.
- Le eccezioni di dominio (`services/exceptions.py`) sono mappate a codici HTTP
  centralmente in `main.py` (`404/403/409/400`).
- Convenzione sui codici di errore: `422` segnala un payload che non supera la
  validazione dello schema Pydantic (es. `fine <= inizio` su
  `POST /admin/disponibilita`, intercettato da `DisponibilitaBase`), `400` una
  regola di dominio violata nel service (es. `ora_fine <= ora_inizio` su
  `POST /admin/disponibilita/genera`). Lo stesso errore semantico puo' quindi
  arrivare con codici diversi a seconda del livello che lo rileva per primo.
- RBAC: `require_role(...)` / `require_admin` in `app/api/deps.py`.
- La relazione molti-a-molti e' modellata da `MedicoPrestazione`; la
  prenotazione verifica sempre `AppuntamentoRepository.medico_esegue(...)`.
- Lo schema del database viene creato all'avvio da `Base.metadata.create_all()`
  e popolato dal seed (`app/db/seed.py`).
