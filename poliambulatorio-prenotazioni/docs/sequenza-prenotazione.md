# Flusso "Prenota visita" - diagramma di sequenza

Il caso d'uso principale attraverso i livelli dell'architettura.

```mermaid
sequenceDiagram
    autonumber
    actor P as Paziente
    participant FE as Front-end
    participant API as Router<br/>appuntamenti.py
    participant SVC as AppuntamentoService
    participant REPO as AppuntamentoRepository
    participant AUD as AuditService
    participant DB as Database

    Note over P,DB: Fase 1 - selezione di medico, prestazione e slot

    P->>FE: sceglie il medico
    FE->>API: GET /medici/{id}/prestazioni
    API->>REPO: prestazioni_di(medico_id)
    REPO->>DB: join medico_prestazione
    DB-->>REPO: prestazioni del medico
    REPO-->>API: elenco
    API-->>FE: 200 - solo prestazioni erogabili
    FE-->>P: popola la tendina prestazioni

    FE->>API: GET /medici/{id}/disponibilita
    API->>REPO: slot_liberi(medico_id)
    REPO->>DB: slot non occupati e futuri
    DB-->>REPO: slot liberi
    REPO-->>API: elenco
    API-->>FE: 200
    FE-->>P: calendario settimanale

    Note over P,DB: Fase 2 - conferma della prenotazione

    P->>FE: seleziona lo slot e conferma
    FE->>API: POST /appuntamenti<br/>{disponibilita_id, prestazione_id}
    API->>SVC: prenota(paziente_id, utente_id, ...)

    SVC->>REPO: slot(disponibilita_id)
    REPO-->>SVC: slot

    alt slot inesistente
        SVC-->>API: NotFoundError
        API-->>FE: 404
    else slot gia occupato
        SVC-->>API: ConflictError
        API-->>FE: 409
    else prestazione non erogata dal medico
        SVC->>REPO: medico_esegue(medico_id, prestazione_id)
        REPO-->>SVC: false
        SVC-->>API: ValidationError
        API-->>FE: 400
    else richiesta valida
        SVC->>REPO: medico_esegue(medico_id, prestazione_id)
        REPO-->>SVC: true
        SVC->>REPO: crea(paziente_id, slot, prestazione_id)
        REPO->>DB: INSERT appuntamento<br/>UPDATE slot.occupato = true
        DB-->>REPO: appuntamento
        REPO-->>SVC: appuntamento
        SVC->>AUD: log(CREATE_APPUNTAMENTO)
        AUD->>DB: INSERT audit_log
        SVC-->>API: appuntamento
        API-->>FE: 201
        FE-->>P: conferma e aggiorna gli slot
    end
```

## Note sul flusso

- Il **router non contiene regole applicative**: invoca il service e restituisce
  la risposta; le eccezioni di dominio diventano codici HTTP tramite gli
  exception handler registrati in `main.py`.
- I rami di errore sono i controlli di
  `AppuntamentoService._valida_slot_prestazione`, condivisi con la prenotazione
  della segreteria (`POST /appuntamenti/operatore`). La verifica `medico_esegue`
  interroga la tabella `medico_prestazione`: è la regola che impedisce di
  prenotare una prestazione presso un medico che non la eroga.
- `crea` inserisce l'appuntamento e occupa lo slot nella stessa transazione,
  così nessuno slot risulta prenotato senza appuntamento corrispondente.
