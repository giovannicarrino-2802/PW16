# Architettura logica

Organizzazione a livelli del sistema e responsabilita di ciascuno.
Versione navigabile su GitHub del diagramma `Architettura_logica.drawio`.

```mermaid
flowchart TB
    %% Asse portante dell'architettura
    FE -->|"HTTP - JSON<br/>Authorization: Bearer"| RT
    RT --> SVC
    SVC --> REP
    REP --> ORM

    subgraph L1["1. Presentazione"]
        FE["Front-end<br/>HTML - CSS - JavaScript<br/><i>index.html, app.js, api.js</i>"]
    end

    subgraph L2["2. API REST"]
        direction LR
        RT["Router FastAPI<br/><i>auth, medici, prestazioni,<br/>appuntamenti, pazienti, admin/</i>"]
        DEP["Dipendenze<br/><i>deps.py: get_current_user,<br/>require_role, require_admin</i>"]
        
        RT --> DEP
    end

    subgraph L3["3. Logica applicativa"]
        direction LR
        SVC["Servizi<br/><i>AppuntamentoService, MedicoService,<br/>PrestazioneService, DisponibilitaService,<br/>UtenteService, AuditService</i>"]
        EXC["Eccezioni di dominio<br/><i>NotFound, Forbidden,<br/>Conflict, Validation</i>"]
        
        SVC --> EXC
    end

    subgraph L4["4. Accesso ai dati"]
        REP["Repository<br/><i>AppuntamentoRepository, MedicoRepository,<br/>PrestazioneRepository, DisponibilitaRepository,<br/>UtenteRepository</i>"]
    end

    subgraph L5["5. Persistenza"]
        direction LR
        ORM["Modelli ORM SQLAlchemy<br/><i>Utente, Paziente, Medico, Prestazione,<br/>MedicoPrestazione, Disponibilita,<br/>Appuntamento, AuditLog</i>"]
        DB[("Database<br/>SQLite")]
        
        ORM --> DB
    end

    subgraph TRA["Funzionalità trasversali"]
        direction TB
        SEC["Sicurezza<br/>OAuth2 Bearer - JWT<br/>RBAC - hashing bcrypt"]
        VAL["Validazione<br/>schemi Pydantic<br/>DTO separati dall'ORM"]
        AUD["Audit logging<br/>tracciamento delle<br/>operazioni rilevanti"]
    end

    %% Collegamento di ritorno delle eccezioni (più lungo per non spezzare il layout)
    EXC -.->|"mappate a<br/>404/403/409/400"| RT

    %% Collegamenti dalle funzionalità trasversali (Cross-cutting)
    SEC -.-> DEP
    VAL -.-> RT
    AUD -.-> SVC
```

```mermaid
flowchart TB
    subgraph L1["Presentazione"]
        FE["Front-end<br/>HTML - CSS - JavaScript<br/><i>index.html, app.js, api.js</i>"]
    end

    subgraph L2["API REST"]
        RT["Router FastAPI<br/><i>auth, medici, prestazioni,<br/>appuntamenti, pazienti, admin/</i>"]
        DEP["Dipendenze<br/><i>deps.py: get_current_user,<br/>require_role, require_admin</i>"]
    end

    subgraph L3["Logica applicativa"]
        SVC["Servizi<br/><i>AppuntamentoService, MedicoService,<br/>PrestazioneService, DisponibilitaService,<br/>UtenteService, AuditService</i>"]
        EXC["Eccezioni di dominio<br/><i>NotFound, Forbidden,<br/>Conflict, Validation</i>"]
    end

    subgraph L4["Accesso ai dati"]
        REP["Repository<br/><i>AppuntamentoRepository, MedicoRepository,<br/>PrestazioneRepository, DisponibilitaRepository,<br/>UtenteRepository</i>"]
    end

    subgraph L5["Persistenza"]
        ORM["Modelli ORM SQLAlchemy<br/><i>Utente, Paziente, Medico, Prestazione,<br/>MedicoPrestazione, Disponibilita,<br/>Appuntamento, AuditLog</i>"]
        DB[("Database<br/>SQLite")]
    end

    subgraph TRA["Funzionalita trasversali"]
        SEC["Sicurezza<br/>OAuth2 Bearer - JWT<br/>RBAC - hashing bcrypt"]
        VAL["Validazione<br/>schemi Pydantic<br/>DTO separati dall'ORM"]
        AUD["Audit logging<br/>tracciamento delle<br/>operazioni rilevanti"]
    end

    FE -->|"HTTP - JSON<br/>Authorization: Bearer"| RT
    RT --> DEP
    RT --> SVC
    SVC --> EXC
    EXC -.->|"mappate a<br/>404/403/409/400"| RT
    SVC --> REP
    REP --> ORM
    ORM --> DB

    SEC -.-> DEP
    VAL -.-> RT
    AUD -.-> SVC
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
