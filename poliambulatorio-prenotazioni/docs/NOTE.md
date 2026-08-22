# Documentazione di progetto

La cartella [`docs/`](.) raccoglie gli artefatti di design del PW16.

## Diagrammi

| File | Contenuto |
|---|---|
| [`casi-uso.md`](casi-uso.md) | Attori (Paziente, Operatore, Admin) e casi d'uso |
| [`architettura.md`](architettura.md) | Architettura a livelli e responsabilità |
| [`ER.md`](ER.md) | Modello dati: entità, relazioni e vincoli |
| [`classi-prenotazione.md`](classi-prenotazione.md) | Classi coinvolte nel flusso di prenotazione |
| [`sequenza-prenotazione.md`](sequenza-prenotazione.md) | Flusso completo della prenotazione |
| [`stati-prenotazione.md`](stati-prenotazione.md) | Ciclo di vita di un appuntamento |

La documentazione OpenAPI/Swagger è generata automaticamente da FastAPI ed è
disponibile su http://localhost:8000/docs a back-end avviato.

## Mappa requisito - endpoint - test

| ID | Requisito | Endpoint | Test |
|---|---|---|---|
| RF1 | Autenticazione | `/auth/login`, `/auth/me` | `test_login_demo`, `test_me_ritorna_ruolo` |
| RF2 | Ricerca disponibilità | `/medici/{id}/disponibilita` | `test_prenota_e_lista` (indiretta) |
| RF3 | Prestazioni per medico | `/medici/{id}/prestazioni` | `test_prestazioni_del_medico` |
| RF4 | Prenotazione validata | `POST /appuntamenti` | `test_prenota_e_lista`, `test_slot_occupato_genera_conflitto`, `test_prenotazione_non_valida_bloccata` |
| RF5 | Le mie prenotazioni / annullamento | `GET /appuntamenti`, `PATCH /appuntamenti/{id}` | `test_prenota_e_lista`, `test_paziente_non_annulla_due_volte` |
| RF5b | Titolarita della prenotazione | `PATCH /appuntamenti/{id}` | `test_paziente_non_annulla_prenotazione_altrui` |
| RF6 | Agenda operatore | `GET /appuntamenti/tutti` | `test_agenda_richiede_staff` |
| RF7 | Gestione medici | `/admin/medici` | `test_crud_medico`, `test_rbac_*` |
| RF8 | Gestione prestazioni | `/admin/prestazioni` | `test_crud_prestazione`, `test_prestazione_validazione` |
| RF9 | Gestione disponibilità | `/admin/disponibilita` | `test_crud_disponibilita`, `test_disponibilita_intervallo_non_valido` |
| RF10 | Associazioni medico-prestazione | `/admin/medici/{id}/prestazioni` | `test_associazione_medico_prestazione` |
| RF11 | Audit | `AuditService` | `test_audit_registra_operazioni_admin` |
| RF12 | Segreteria: prenota per conto, agenda, modifica | `/appuntamenti/operatore`, `/appuntamenti/tutti`, `PATCH /appuntamenti/tutti/{id}` | `test_segreteria_prenota_per_paziente_e_modifica` |
| RF13 | Gestione utenti | `/admin/utenti` | `test_crud_utente_operatore`, `test_crea_utente_paziente_con_profilo`, `test_utenti_rbac_e_self_delete` |
| RF14 | Stati terminali | `PATCH /appuntamenti/{id}`, `PATCH /appuntamenti/tutti/{id}` | `test_paziente_non_annulla_due_volte`, `test_segreteria_non_annulla_due_volte`, `test_riprogramma_solo_prenotazioni_attive`, `test_riprogramma_prenotazione_completata`, `test_riprogramma_solo_stesso_medico`, `test_riprogramma_su_slot_occupato` |
| RF15 | Integrità degli slot | `DELETE /admin/disponibilita/{id}` | `test_elimina_slot_prenotato_bloccata` |

## Controllo degli accessi

- **paziente**: prenota per sé, consulta e annulla le proprie prenotazioni.
- **operatore** (segreteria): prenota per conto dei pazienti, consulta l'agenda
  di tutti e può annullare / completare / riprogrammare qualsiasi prenotazione.
- **admin**: tutto quanto sopra più la configurazione del poliambulatorio
  (medici, prestazioni, associazioni, disponibilità, utenti).

Le dipendenze `require_role(...)` e `require_admin` sono definite in
`app/api/deps.py`.

### Matrice dei permessi

Legenda: **X** consentito - **-** negato (`403`) - **n/a** non applicabile al ruolo.

| Endpoint | Metodo | paziente | operatore | admin | Dipendenza |
|---|---|:--:|:--:|:--:|---|
| `/auth/login` | POST | X | X | X | nessuna (pubblico) |
| `/auth/me` | GET | X | X | X | `get_current_user` |
| `/medici` | GET | X | X | X | `get_current_user` |
| `/medici/{id}/prestazioni` | GET | X | X | X | `get_current_user` |
| `/medici/{id}/disponibilita` | GET | X | X | X | `get_current_user` |
| `/prestazioni` | GET | X | X | X | `get_current_user` |
| `/appuntamenti` | POST | X | n/a | n/a | `get_current_paziente` |
| `/appuntamenti` | GET | X | n/a | n/a | `get_current_paziente` |
| `/appuntamenti/{id}` | PATCH | X | n/a | n/a | `get_current_paziente` |
| `/appuntamenti/tutti` | GET | - | X | X | `require_role("operatore","admin")` |
| `/appuntamenti/operatore` | POST | - | X | X | `require_role("operatore","admin")` |
| `/appuntamenti/tutti/{id}` | PATCH | - | X | X | `require_role("operatore","admin")` |
| `/pazienti` | GET | - | X | X | `require_role("operatore","admin")` |
| `/admin/medici` | GET POST PUT DELETE | - | - | X | `require_admin` |
| `/admin/medici/{id}/prestazioni` | GET POST DELETE | - | - | X | `require_admin` |
| `/admin/prestazioni` | GET POST PUT DELETE | - | - | X | `require_admin` |
| `/admin/disponibilita` | GET POST PUT DELETE | - | - | X | `require_admin` |
| `/admin/disponibilita/genera` | POST | - | - | X | `require_admin` |
| `/admin/utenti` | GET POST PUT DELETE | - | - | X | `require_admin` |

Gli endpoint marcati **n/a** richiedono un profilo paziente collegato
all'utente: un account di segreteria non ne ha uno e riceve `403` da
`get_current_paziente`. Senza token qualsiasi endpoint protetto risponde `401`.
L'admin non può eliminare il proprio account (`403`), per non lasciare il
sistema privo di amministratori.

### Azioni di audit registrate

| Entità | Azioni |
|---|---|
| Medici | `CREATE_MEDICO`, `UPDATE_MEDICO`, `DELETE_MEDICO` |
| Prestazioni | `CREATE_PRESTAZIONE`, `UPDATE_PRESTAZIONE`, `DELETE_PRESTAZIONE` |
| Associazioni | `LINK_MEDICO_PRESTAZIONE`, `UNLINK_MEDICO_PRESTAZIONE` |
| Disponibilità | `CREATE_DISPONIBILITA`, `UPDATE_DISPONIBILITA`, `DELETE_DISPONIBILITA` |
| Appuntamenti | `CREATE_APPUNTAMENTO`, `CANCEL_APPUNTAMENTO`, `COMPLETE_APPUNTAMENTO`, `RESCHEDULE_APPUNTAMENTO` |
| Utenti | `CREATE_UTENTE`, `UPDATE_UTENTE`, `DELETE_UTENTE` |

## Ciclo di vita della prenotazione

`prenotata` è l'unico stato attivo; `annullata` e `completata` sono **stati
terminali** e non ammettono ulteriori transizioni (annullamento ripetuto o
riprogrammazione rispondono `409`). Il vincolo esiste perchè solo una
prenotazione attiva "possiede" il proprio slot: agire su una prenotazione già
terminata libererebbe uno slot che nel frattempo può appartenere a un'altra
prenotazione.

La riprogrammazione sposta inoltre solo l'orario: il nuovo slot deve
appartenere allo stesso medico (altrimenti `409`), perchè cambiare medico
equivarrebbe a una prenotazione diversa da quella scelta dal paziente e va
gestita annullando e riprenotando. Copertura:
`tests/test_stati_prenotazione.py`.

## Gestione degli errori

Le eccezioni di dominio (`services/exceptions.py`) sono mappate a codici HTTP
centralmente in `main.py`: `404` / `403` / `409` / `400`.

A queste si affianca il `422` prodotto da FastAPI quando il payload non supera
la validazione dello schema Pydantic (es. `fine <= inizio` su
`POST /admin/disponibilita`, intercettato da `DisponibilitaBase`), mentre il
`400` segnala una regola di dominio violata nel service (es.
`ora_fine <= ora_inizio` su `POST /admin/disponibilita/genera`). Lo stesso
errore semantico può quindi arrivare con codici diversi a seconda del livello
che lo rileva per primo.

## Suite di test

I test condividono un unico database di sessione: `conftest.py` cancella e
ricrea `test_poliambulatorio.db` una sola volta all'avvio della suite, poi il
seed lo ripopola. Non c'è isolamento fra file: ogni prenotazione consuma uno
slot, che i test successivi non trovano più fra quelli liberi. I test che
hanno bisogno di risorse specifiche (medico, prestazione, slot) se le creano
quindi tramite gli endpoint amministrativi anzichè attingere dal seed.

Vanno eseguiti con `pytest` sull'intera cartella: lanciare un singolo file
parte da uno stato diverso, e l'esecuzione in parallelo non è supportata.

## Note di implementazione

- Il database conserva tutti i datetime (`inizio`, `fine`, `creato_il`, `ts`)
  in forma naive, riferiti all'ora locale dell'ambulatorio: un solo orologio per
  l'intero database, così un record di audit è direttamente confrontabile con
  l'orario di una prenotazione. Unica eccezione il claim `exp` del token JWT,
  che per specifica è un timestamp UTC e non viene mai confrontato con i dati.
- La relazione molti-a-molti è modellata da `MedicoPrestazione`; la
  prenotazione verifica sempre `AppuntamentoRepository.medico_esegue(...)`.
- Lo schema del database viene creato all'avvio da `Base.metadata.create_all()`
  e popolato dal seed (`app/db/seed.py`).

## Limiti noti

Scelte consapevoli o vincoli non risolti nella soluzione. Non impediscono l'uso
previsto del prototipo.

- **Integrità referenziale non applicata dal database.** SQLite non verifica le
  foreign key se non viene attivato `PRAGMA foreign_keys=ON`, qui non impostato.
  L'eliminazione di un medico o di una prestazione dall'area amministrativa non
  controlla le dipendenze: restano righe orfane in `medico_prestazione`,
  `disponibilità` e `appuntamento`. Poiché l'agenda (`list_tutti_dettaglio`)
  usa una join su medico e prestazione, le prenotazioni orfane non compaiono
  più nell'elenco anzichè generare un errore. Mitigazione operativa: eliminare
  medici e prestazioni solo se non hanno prenotazioni collegate.

- **Chiave di firma dei token con valore predefinito.** `SECRET_KEY` viene letta
  dalla variabile d'ambiente omonima, ma in sua assenza `core/config.py` ricade
  su un valore fisso di sviluppo (`"dev-secret-cambia-in-produzione"`). Questo
  consente di avviare la demo e la suite di test senza configurazione, ma in un
  ambiente reale la variabile va impostata: chi conoscesse il default potrebbe
  altrimenti forgiare token JWT validi per qualsiasi utente e ruolo.

- **Audit log conservato oltre la vita dell'utente.** L'eliminazione di un utente
  rimuove il profilo paziente e le sue prenotazioni, ma non i record di
  `audit_log`, che restano con un `utente_id` non più risolvibile. È una scelta
  intenzionale: cancellare la tracciabilità delle azioni passate insieme
  all'utente vanificherebbe lo scopo del log.