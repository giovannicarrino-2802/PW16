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

| Livello | Responsabilità |
|---|---|
| **Presentazione** | Interfaccia utente, conservazione del token, calendario e agenda |
| **API REST** | Instradamento, validazione del payload, autenticazione e controllo dei ruoli, traduzione delle eccezioni in codici HTTP |
| **Logica applicativa** | Regole di dominio (associazione medico-prestazione, stati della prenotazione, sovrapposizione degli slot), audit, hashing delle password |
| **Accesso ai dati** | Query e transazioni |
| **Persistenza** | Definizione delle entità e dello schema, sessione e popolamento iniziale |

## Principio guida

Il front-end non applica vincoli e il repository non verifica le operazioni, ogni regola è applicata dal livello dei servizi.

La dipendenza è **unidirezionale**: nessun livello conosce quelli soprastanti.
Le eccezioni di dominio sono l'unico canale di ritorno dal livello applicativo
verso le API, e vengono tradotte in codici HTTP da un punto unico (`main.py`),
evitando che i router replichino la stessa logica di conversione.

Fanno eccezione le letture prive di regole di dominio (elenco medici, elenco prestazioni, slot liberi, elenco pazienti), servite dal router direttamente tramite il repository, senza attraversare il livello dei servizi.