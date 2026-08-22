# Architettura logica

Organizzazione a livelli del sistema e responsabilita.

```mermaid
flowchart TB

    subgraph L1["1. Presentazione"]
        FE["<b>Front-end</b><br/>HTML / CSS / JavaScript<br/><i>index.html, app.js, api.js</i>"]
    end

    subgraph L2["2. API REST"]
        direction LR
        RT["<b>Router FastAPI</b><br/><i>auth, medici, prestazioni,<br/>appuntamenti, pazienti, admin</i>"]
        DEP["<b>Dipendenze (deps.py)</b><br/><i>get_current_user,<br/>require_role, require_admin</i>"]
        RT --> DEP
    end

    subgraph L3["3. Logica applicativa"]
        direction LR
        SVC["<b>Servizi</b><br/><i>Appuntamento, Medico, Prestazione,<br/>Disponibilita, Utente, Audit</i>"]
        EXC["<b>Eccezioni di dominio</b><br/><i>NotFound, Forbidden,<br/>Conflict, Validation</i><br/>mappate a 404 / 403 / 409 / 400"]
        SVC --> EXC
    end

    subgraph L4["4. Accesso ai dati"]
        REP["<b>Repository</b><br/><i>Appuntamento, Medico, Prestazione,<br/>Disponibilita, Utente</i>"]
    end

    subgraph L5["5. Persistenza"]
        direction LR
        ORM["<b>Modelli ORM SQLAlchemy</b><br/><i>Utente, Paziente, Medico, Prestazione,<br/>MedicoPrestazione, Disponibilita,<br/>Appuntamento, AuditLog</i>"]
        DB[("Database<br/>SQLite")]
        ORM --> DB
    end

    subgraph TRA["Funzionalita trasversali"]
        SEC["<b>Sicurezza</b><br/>OAuth2 Bearer / JWT<br/>RBAC / hashing bcrypt"]
        VAL["<b>Validazione</b><br/>schemi Pydantic<br/>DTO separati dall'ORM"]
        AUD["<b>Audit logging</b><br/>tracciamento delle<br/>operazioni rilevanti"]
    end

    FE -->|"HTTP / JSON<br/>Authorization: Bearer"| RT
    RT --> SVC
    SVC --> REP
    REP --> ORM

    DEP -.-> SEC
    RT -.-> VAL
    SVC -.-> AUD

    classDef comp fill:#E8EAFB,stroke:#4A4FA8,stroke-width:1px,color:#111
    classDef store fill:#E7F4EC,stroke:#3B7F58,stroke-width:1px,color:#111
    class FE,RT,DEP,SVC,EXC,REP,ORM,SEC,VAL,AUD comp
    class DB store

    style L1 fill:#FCFAEC,stroke:#BFB77F
    style L2 fill:#FCFAEC,stroke:#BFB77F
    style L3 fill:#FCFAEC,stroke:#BFB77F
    style L4 fill:#FCFAEC,stroke:#BFB77F
    style L5 fill:#FCFAEC,stroke:#BFB77F
    style TRA fill:#F5F5F5,stroke:#9E9E9E,stroke-dasharray: 4 3
```

## Responsabilita dei livelli

| Livello | Responsabilita | Cosa non fa |
|---|---|---|
| **Presentazione** | Interfaccia utente, conservazione del token, resa di calendario e agenda | Nessuna regola di business: ogni vincolo e' verificato lato server |
| **API REST** | Instradamento, validazione del payload, autenticazione e controllo dei ruoli, traduzione delle eccezioni in codici HTTP | Non contiene regole applicative |
| **Logica applicativa** | Regole di dominio (associazione medico-prestazione, stati della prenotazione, sovrapposizione degli slot), audit | Non conosce HTTP ne' costruisce query |
| **Accesso ai dati** | Query e transazioni, isolamento di SQLAlchemy dal resto | Non decide se un'operazione sia lecita |
| **Persistenza** | Definizione delle entita e dello schema | - |

## Principio guida

La dipendenza e' **unidirezionale**: ogni livello conosce solo quello
immediatamente sottostante. Le eccezioni di dominio sono l'unico canale di
ritorno dal livello applicativo verso le API, e vengono tradotte in codici HTTP
da un punto unico (`main.py`), evitando che i router replichino la stessa
logica di conversione.
