# Architettura logica

Organizzazione a livelli del sistema e responsabilita.

```mermaid
flowchart TB

    subgraph L1["1. Presentazione"]
        FE["<b>FRONT-END</b><br/><i>index.html, app.js, api.js</i><br/>---<br/>- Login e sessione utente<br/>- Scelta medico e prestazione<br/>- Consultazione slot disponibili<br/>- Gestione prenotazioni utente"]
    end

    subgraph L2["2. API REST"]
        direction LR
        RT["<b>ROUTER FASTAPI</b><br/><i>Swagger / OpenAPI</i><br/>---<br/>- /auth<br/>- /medici<br/>- /prestazioni<br/>- /appuntamenti<br/>- /pazienti<br/>- /admin"]
        DEP["<b>DIPENDENZE</b><br/><i>deps.py</i><br/>---<br/>- get_current_user<br/>- require_role<br/>- require_admin"]
        RT --> DEP
    end

    subgraph L3["3. Logica applicativa"]
        direction LR
        SVC["<b>SERVIZI</b><br/><i>Appuntamento, Medico, Prestazione,<br/>Disponibilita, Utente, Audit</i><br/>---<br/>- Regole di business<br/>- Verifica slot e sovrapposizioni<br/>- Controllo proprieta risorsa<br/>- Transizioni di stato"]
        EXC["<b>ECCEZIONI DI DOMINIO</b><br/><i>NotFound, Forbidden,<br/>Conflict, Validation</i><br/>---<br/>mappate dagli handler a<br/>404 / 403 / 409 / 400"]
        SVC --> EXC
    end

    subgraph L4["4. Accesso ai dati"]
        REP["<b>REPOSITORY</b><br/><i>Appuntamento, Medico, Prestazione,<br/>Disponibilita, Utente</i><br/>---<br/>- Query e persistenza<br/>- Ricerca slot liberi<br/>- CRUD appuntamenti"]
    end

    subgraph L5["5. Persistenza"]
        direction LR
        ORM["<b>MODELLI ORM SQLALCHEMY</b><br/>---<br/>Utente, Paziente, Medico,<br/>Prestazione, MedicoPrestazione,<br/>Disponibilita, Appuntamento, AuditLog"]
        DB[("<b>Database</b><br/>SQLite")]
        ORM --> DB
    end

    subgraph TRA["Funzionalita trasversali"]
        SEC["<b>SICUREZZA</b><br/><i>autenticazione e autorizzazione</i><br/>---<br/>- OAuth2 Bearer Token<br/>- JWT<br/>- RBAC per ruolo<br/>- Hashing password bcrypt"]
        VAL["<b>VALIDAZIONE DATI</b><br/><i>schemi Pydantic</i><br/>---<br/>- Validazione payload<br/>- Response model<br/>- Separazione DTO / ORM<br/>- Campi obbligatori e tipi"]
        AUD["<b>AUDIT LOGGING</b><br/><i>AuditService + AuditLog</i><br/>---<br/>- Prenotazioni e annullamenti<br/>- Operazioni amministrative<br/>- Tracciamento su database"]
    end

    FE -->|"HTTP / REST / JSON<br/>Authorization: Bearer"| RT
    RT -->|"regole di business"| SVC
    SVC -->|"accesso ai dati"| REP
    REP -->|"persistenza"| ORM

    DEP -.->|"token / ruoli"| SEC
    RT -.->|"request / response"| VAL
    SVC -.->|"logging eventi"| AUD

    classDef pres fill:#E7F0FD,stroke:#1E6FD9,stroke-width:1.5px,color:#111
    classDef api fill:#E3F5F6,stroke:#0E7C86,stroke-width:1.5px,color:#111
    classDef logic fill:#E6F4EC,stroke:#2E7D5B,stroke-width:1.5px,color:#111
    classDef data fill:#FCEEDF,stroke:#C2681A,stroke-width:1.5px,color:#111
    classDef pers fill:#ECEFF1,stroke:#2C3E50,stroke-width:1.5px,color:#111
    classDef sec fill:#F0EAFB,stroke:#6A3DBF,stroke-width:1.5px,color:#111
    classDef val fill:#FCE7EF,stroke:#C2185B,stroke-width:1.5px,color:#111
    classDef aud fill:#E6F4EC,stroke:#2E7D5B,stroke-width:1.5px,color:#111

    class FE pres
    class RT,DEP api
    class SVC,EXC logic
    class REP data
    class ORM,DB pers
    class SEC sec
    class VAL val
    class AUD aud

    linkStyle 3 stroke:#1E6FD9,stroke-width:2px
    linkStyle 4 stroke:#0E7C86,stroke-width:2px
    linkStyle 5 stroke:#2E7D5B,stroke-width:2px
    linkStyle 6 stroke:#C2681A,stroke-width:2px
    linkStyle 7 stroke:#6A3DBF
    linkStyle 8 stroke:#C2185B
    linkStyle 9 stroke:#2E7D5B

    style L1 fill:#FFFFFF,stroke:#9E9E9E
    style L2 fill:#FFFFFF,stroke:#9E9E9E
    style L3 fill:#FFFFFF,stroke:#9E9E9E
    style L4 fill:#FFFFFF,stroke:#9E9E9E
    style L5 fill:#FFFFFF,stroke:#9E9E9E
    style TRA fill:#FAFAFA,stroke:#616161,stroke-dasharray: 4 3
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
