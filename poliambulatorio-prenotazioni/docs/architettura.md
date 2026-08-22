# Architettura logica

Organizzazione a livelli del sistema e responsabilita.

```mermaid
flowchart TB

    subgraph L1["1. Presentazione"]
        FE["<b>FRONT-END</b><br/>HTML, CSS, JavaScript<br/><i>index.html, app.js, api.js</i>"]
    end

    subgraph L2["2. API REST"]
        direction LR
        RT["<b>ROUTER FASTAPI</b> - Swagger/OpenAPI<br/><i>auth, medici, prestazioni,<br/>appuntamenti, pazienti, admin</i>"]
        DEP["<b>DIPENDENZE</b> - deps.py<br/><i>get_current_user,<br/>require_role, require_admin</i>"]
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
        DB[("<b>Database</b><br/>SQLite")]
        ORM --> DB
    end

    subgraph TRA["Funzionalita trasversali"]
        SEC["<b>SICUREZZA</b><br/>OAuth2 Bearer, JWT<br/>RBAC, hashing bcrypt"]
        VAL["<b>VALIDAZIONE DATI</b><br/>schemi Pydantic<br/>DTO separati dall'ORM"]
        AUD["<b>AUDIT LOGGING</b><br/>AuditService + AuditLog<br/>tracciamento operazioni"]
    end

    FE -->|"HTTP / REST / JSON - Bearer"| RT
    RT --> SVC
    SVC --> REP
    REP --> ORM

    DEP -.-> SEC
    RT -.-> VAL
    SVC -.-> AUD
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
