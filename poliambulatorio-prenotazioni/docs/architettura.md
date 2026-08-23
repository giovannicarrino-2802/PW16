# Architettura logica

Organizzazione a livelli del sistema e responsabilità.

```mermaid
flowchart TB

    subgraph L1["1. Presentazione"]
        FE["<b>FRONT-END</b><br/>HTML, CSS, JavaScript<br/><i>index.html, app.js, api.js</i>"]
    end

    subgraph L2["2. API REST"]
        direction LR
        RT["<b>ROUTER FASTAPI</b> - Swagger/OpenAPI<br/><i>auth, medici, prestazioni, appuntamenti,<br/>pazienti, admin/* (medici, prestazioni,<br/>disponibilita, utenti)</i>"]
        DEP["<b>DIPENDENZE</b> - deps.py<br/><i>get_current_user, get_current_paziente,<br/>require_role, require_admin</i>"]
        RT --> DEP
    end

    subgraph L3["3. Logica applicativa"]
        direction LR
        SVC["<b>SERVIZI</b> - regole di business<br/><i>Appuntamento, Medico, Prestazione,<br/>Disponibilita, Utente, Audit</i>"]
        EXC["<b>ECCEZIONI DI DOMINIO</b><br/><i>NotFound, Forbidden, Conflict, Validation</i><br/>mappate a 404 / 403 / 409 / 400"]
        SVC --> EXC
    end

    subgraph L4["4. Accesso ai dati"]
        REP["<b>REPOSITORY</b> - query e persistenza<br/><i>Appuntamento, Medico, Prestazione,<br/>Disponibilita, Utente</i>"]
    end

    subgraph L5["5. Persistenza"]
        direction LR
        ORM["<b>MODELLI ORM SQLALCHEMY</b><br/><i>Utente, Paziente, Medico, Prestazione,<br/>MedicoPrestazione, Disponibilita,<br/>Appuntamento, AuditLog</i>"]
        SES["<b>SESSIONE E SCHEMA</b> - db/<br/><i>base dichiarativa, sessione, seed</i>"]
        DB[("<b>Database</b><br/>SQLite")]
        ORM --> DB
        SES --> DB
    end

    subgraph TRA["Funzionalità trasversali"]
        SEC["<b>SICUREZZA</b><br/>OAuth2 Bearer, JWT<br/>RBAC, hashing bcrypt"]
        VAL["<b>VALIDAZIONE DATI</b><br/>schemi Pydantic - DTO separati dall'ORM<br/>payload malformato: 422"]
        AUD["<b>AUDIT LOGGING</b><br/>AuditService + AuditLog<br/>tracciamento operazioni"]
    end

    FE -->|"HTTP / REST / JSON - Bearer"| RT
    RT --> SVC
    SVC --> REP
    REP --> ORM
    RT -.->|"letture senza regole di dominio"| REP

    DEP -.-> SEC
    SVC -.-> SEC
    RT -.-> VAL
    SVC -.-> AUD
```

## Responsabilità dei livelli

| Livello | Responsabilità | Cosa non fa |
|---|---|---|
| **Presentazione** | Interfaccia utente, conservazione del token, resa di calendario e agenda | Nessuna regola di business: ogni vincolo è verificato lato server |
| **API REST** | Instradamento, validazione del payload (`422` se malformato), autenticazione e controllo dei ruoli, traduzione delle eccezioni in codici HTTP | Non contiene regole applicative |
| **Logica applicativa** | Regole di dominio (associazione medico-prestazione, stati della prenotazione, sovrapposizione degli slot), audit, hashing delle password | Non conosce HTTP né costruisce query |
| **Accesso ai dati** | Query e transazioni, isolamento di SQLAlchemy dal resto | Non decide se un'operazione sia lecita |
| **Persistenza** | Definizione delle entità e dello schema, sessione e popolamento iniziale | Nessuna regola applicativa: le entità non contengono logica |

## Principio guida

La dipendenza è **unidirezionale**: nessun livello conosce quelli soprastanti.
Le eccezioni di dominio sono l'unico canale di ritorno dal livello applicativo
verso le API, e vengono tradotte in codici HTTP da un punto unico (`main.py`),
evitando che i router replichino la stessa logica di conversione.

Una sola deroga, deliberata: le **letture prive di regole di dominio**
(elenco medici, elenco prestazioni, slot liberi, elenco pazienti) sono servite
dal router direttamente tramite il repository, senza attraversare il livello
dei servizi. Introdurre un servizio che si limiti a inoltrare la chiamata
aggiungerebbe un livello senza contenuto; tutte le operazioni di scrittura e
tutte quelle soggette a regole passano invece dai servizi.

## Vedi anche

- [`sequenza-prenotazione.md`](sequenza-prenotazione.md) — il flusso di
  prenotazione attraverso i livelli qui descritti.
- [`classi-prenotazione.md`](classi-prenotazione.md) — le classi che
  concretizzano lo schema su una singola funzionalità.