# Classi coinvolte nel flusso di prenotazione

Classi coinvolte nel caso d'uso "Prenota visita", dal router al database.
Mostra come il pattern architetturale si concretizza su una singola
funzionalita; per la struttura delle tabelle si veda [`ER.md`](ER.md).

**Vista d'insieme: relazioni tra i componenti**
```mermaid
classDiagram
    direction TB

    class AppuntamentoCreate {
        <<DTO Pydantic>>
    }
    class AppuntamentoOut {
        <<DTO Pydantic>>
    }
    class RouterAppuntamenti {
        <<API>>
    }
    class AppuntamentoService {
        <<Servizio>>
    }
    class ServiceError {
        <<Eccezione>>
    }
    class NotFoundError {
        <<Eccezione>>
    }
    class ForbiddenError {
        <<Eccezione>>
    }
    class ConflictError {
        <<Eccezione>>
    }
    class ValidationError {
        <<Eccezione>>
    }
    class AuditService {
        <<Servizio>>
    }
    class AppuntamentoRepository {
        <<Repository>>
    }
    class Appuntamento {
        <<Modello ORM>>
    }
    class Disponibilita {
        <<Modello ORM>>
    }
    class MedicoPrestazione {
        <<Modello ORM>>
    }

    RouterAppuntamenti ..> AppuntamentoCreate : riceve
    RouterAppuntamenti ..> AppuntamentoOut : restituisce
    RouterAppuntamenti --> AppuntamentoService : delega

    AppuntamentoService ..> ServiceError : solleva
    AppuntamentoService --> AuditService : traccia
    AppuntamentoService --> AppuntamentoRepository : usa

    ServiceError <|-- NotFoundError
    ServiceError <|-- ForbiddenError
    ServiceError <|-- ConflictError
    ServiceError <|-- ValidationError

    AppuntamentoRepository --> Appuntamento : gestisce
    AppuntamentoRepository --> Disponibilita : gestisce
    AppuntamentoRepository ..> MedicoPrestazione : interroga
```

**Vista completa: include attributi e firme dei metodi**
```mermaid
classDiagram
    direction TB

    class RouterAppuntamenti {
        <<API>>
        +prenota(data, paziente, db) AppuntamentoOut
        +le_mie(paziente, db) List~AppuntamentoOut~
        +annulla(app_id, data, paziente, db) AppuntamentoOut
        +agenda_completa(db, utente) List~AppuntamentoDettaglioOut~
        +prenota_per_paziente(data, db, operatore) AppuntamentoOut
        +modifica_qualsiasi(app_id, data, db, operatore) AppuntamentoOut
    }

    class AppuntamentoService {
        <<Servizio>>
        -repo: AppuntamentoRepository
        -audit: AuditService
        -_valida_slot_prestazione(disponibilita_id, prestazione_id) Disponibilita
        +prenota(paziente_id, utente_id, disponibilita_id, prestazione_id)
        +prenota_per(operatore_id, paziente_id, disponibilita_id, prestazione_id)
        +le_mie(paziente_id)
        +tutti_dettaglio()
        +annulla(utente_id, paziente_id, app_id)
        +annulla_qualsiasi(utente_id, app_id)
        +completa(utente_id, app_id)
        +riprogramma(utente_id, app_id, nuovo_slot_id)
    }

    class AppuntamentoRepository {
        <<Repository>>
        -db: Session
        +slot(disponibilita_id) Disponibilita
        +slot_liberi(medico_id) List~Disponibilita~
        +prestazione(prestazione_id) Prestazione
        +paziente(paziente_id) Paziente
        +medico_esegue(medico_id, prestazione_id) bool
        +crea(paziente_id, slot, prestazione_id) Appuntamento
        +list_by_paziente(paziente_id) List~Appuntamento~
        +list_tutti_dettaglio() List~tuple~
        +annulla(app) Appuntamento
        +imposta_stato(app, stato) Appuntamento
        +riprogramma(app, nuovo_slot) Appuntamento
    }

    class AuditService {
        <<Servizio>>
        -db: Session
        +log(utente_id, azione, entita, entita_id, dettagli)
    }

    class Appuntamento {
        <<Modello ORM>>
        +int id
        +int paziente_id
        +int medico_id
        +int prestazione_id
        +int disponibilita_id
        +datetime inizio
        +datetime fine
        +str stato
        +datetime creato_il
    }

    class Disponibilita {
        <<Modello ORM>>
        +int id
        +int medico_id
        +datetime inizio
        +datetime fine
        +bool occupato
    }

    class MedicoPrestazione {
        <<Modello ORM>>
        +int id
        +int medico_id
        +int prestazione_id
    }

    class AppuntamentoCreate {
        <<DTO Pydantic>>
        +int disponibilita_id
        +int prestazione_id
    }

    class AppuntamentoOut {
        <<DTO Pydantic>>
        +int id
        +int medico_id
        +int prestazione_id
        +datetime inizio
        +datetime fine
        +str stato
    }

    class ServiceError {
        <<Eccezione>>
    }
    class NotFoundError {
        <<Eccezione>>
    }
    class ForbiddenError {
        <<Eccezione>>
    }
    class ConflictError {
        <<Eccezione>>
    }
    class ValidationError {
        <<Eccezione>>
    }

    RouterAppuntamenti ..> AppuntamentoCreate : riceve
    RouterAppuntamenti ..> AppuntamentoOut : restituisce
    RouterAppuntamenti --> AppuntamentoService : delega
    AppuntamentoService --> AppuntamentoRepository : usa
    AppuntamentoService --> AuditService : traccia
    AppuntamentoService ..> ServiceError : solleva
    AppuntamentoRepository ..> Appuntamento : gestisce
    AppuntamentoRepository ..> Disponibilita : gestisce
    AppuntamentoRepository ..> MedicoPrestazione : interroga

    ServiceError <|-- NotFoundError
    ServiceError <|-- ForbiddenError
    ServiceError <|-- ConflictError
    ServiceError <|-- ValidationError
```

## Elementi da osservare

- **Il router non conosce i modelli ORM**: riceve e restituisce DTO Pydantic
  (`AppuntamentoCreate`, `AppuntamentoOut`), mentre le entita SQLAlchemy non
  escono mai dal livello di accesso ai dati.
- **Il service non conosce SQLAlchemy**: riceve un repository nel costruttore e
  ne invoca i metodi, senza costruire query. Questo consente di sostituire il
  repository con un doppio nei test unitari.
- **Un solo punto di validazione**: `_valida_slot_prestazione` e' condiviso da
  `prenota` e `prenota_per`, cosi' le regole valgono identiche sia che prenoti
  il paziente sia che prenoti la segreteria.
- **Le eccezioni derivano da una radice comune**, il che permette a `main.py` di
  registrare la traduzione in codici HTTP una volta sola.
