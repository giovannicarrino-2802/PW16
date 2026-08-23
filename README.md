# Piattaforma di prenotazione di visite specialistiche

Project Work PW16 - CdS Informatica per le Aziende Digitali (L-31).

Applicazione full-stack API-based per un'organizzazione del settore sanitario allo scopo di supportare il processo organizzativo per la prenotazione di visite specialistiche, la gestione di medici, prestazioni, disponibilità, associazioni medico-prestazione e utenti.

Il codice sorgente si trova nella cartella
[`poliambulatorio-prenotazioni/`](poliambulatorio-prenotazioni/); questo file
descrive brevemente il progetto nel suo insieme.

## Architettura (a livelli)

```
Front-end (HTML/CSS/JS)  ->  API REST (FastAPI)  ->  Servizi (business)
->  Repository (accesso dati)  ->  Modelli ORM  ->  Database (SQLAlchemy + SQLite)
```

Trasversale: sicurezza (JWT + RBAC), validazione (Pydantic), audit log.

Il livello **Servizi** applica le regole di business (es. una prestazione può
essere prenotata solo se associata al medico); il livello **Repository** isola
l'accesso ai dati; le **API** traducono le eccezioni di dominio in codici HTTP.

## Funzionalità principali

Ogni ruolo dispone di endpoint propri, così che l'audit log registri sempre chi
ha compiuto l'operazione e per conto di chi.

**Paziente** — sceglie il medico e vede le sole prestazioni che quel medico
eroga; seleziona lo slot su un calendario settimanale scorrevole con le
disponibilità libere e future. Può prenotare, consultare le proprie
prenotazioni e annullarle.

**Operatore di segreteria** — lavora sull'agenda completa della struttura:
prenota per conto di un paziente, annulla, completa e riprogramma. Non avendo un
profilo paziente collegato, gli endpoint di prenotazione personale non sono disponibili.

**Amministratore** — configura l'offerta clinica tramite i router riservati in
`app/api/v1/admin/`: anagrafica di medici e prestazioni, associazione tra i due,
agende e gestione utenti.

### Regole applicate lato server

Il front-end non applica vincoli: ogni regola è verificata dai servizi e
tradotta in codice HTTP da un punto unico (`main.py`).

| Regola | Violazione |
|---|---|
| La prestazione deve essere erogata dal medico scelto | `400` |
| Lo slot deve essere libero | `409` |
| `annullata` e `completata` sono stati terminali | `409` |
| La riprogrammazione avviene su uno slot dello stesso medico | `409` |
| L'operazione deve essere consentita al ruolo | `403` |

Struttura interna e flussi nei diagrammi in
[`docs/`](poliambulatorio-prenotazioni/docs/). Il seed iniziale crea 5 medici,
10 prestazioni, le relative agende e tre utenti demo, uno per ruolo.

## Struttura del repository

```
PW16/
├── README.md                        <- questo file
└── poliambulatorio-prenotazioni/    <- progetto
    ├── requirements.txt
    ├── backend/
    │   ├── app/
    │   │   ├── api/                 <- livello API (router REST, incl. admin/)
    │   │   ├── services/            <- regole di business (+ exceptions.py)
    │   │   ├── repositories/        <- accesso ai dati
    │   │   ├── models/              <- entità ORM (SQLAlchemy)
    │   │   ├── schemas/             <- DTO (Pydantic)
    │   │   ├── core/                <- configurazione e sicurezza (JWT, hashing)
    │   │   └── db/                  <- base, sessione, seed
    │   └── tests/                   <- suite pytest
    ├── frontend/                    <- interfaccia utente (booking + admin)
    └── docs/                        <- diagrammi e note di progetto
```

## Avvio del back-end

> Requisiti:
>- **Python 3.10 o superiore** (`python --version` per verificare). Su Windows,
> in fase di installazione, spuntare *Add Python to PATH*.
>- **Connessione a Internet** per il solo `pip install`; l'applicazione poi gira
>  in locale.
>- **Circa 300 MB liberi** su disco: l'ambiente virtuale con le dipendenze ne
>  occupa circa 250, il database SQLite pochi MB.
>- **Windows: policy di esecuzione.** L'attivazione del venv da PowerShell può
>  essere bloccata dalla policy predefinita. In quel caso eseguire, nella stessa
>  sessione:
>```powershell
>  Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process
>```

### Windows (PowerShell)

Assicurarsi che Python sia installato nel sistema.

```powershell
cd poliambulatorio-prenotazioni\backend
python -m venv .venv
.venv\Scripts\activate
pip install -r ..\requirements.txt
# ignorare eventuali messaggi di aggiornamento
uvicorn app.main:app --reload
```

### macOS / Linux

```bash
cd poliambulatorio-prenotazioni/backend
python -m venv .venv
source .venv/bin/activate
pip install -r ../requirements.txt
uvicorn app.main:app --reload
```

- Swagger UI (documentazione API):  http://localhost:8000/docs
- Al primo avvio il database SQLite viene creato e popolato con i dati di esempio.

### Credenziali demo
- Paziente:  mario.rossi@example.com  /  Password123!
- Operatore: segreteria@example.com   /  Segreteria123!
- Admin:   admin@example.com        /  Admin123!

## Front-end
Aprire `poliambulatorio-prenotazioni/frontend/index.html` nel browser (con il
back-end avviato).

- **Prenota una visita**: scegliere il medico -> la tendina delle prestazioni si
  popola con le sole prestazioni erogate da quel medico -> selezionare uno slot
  sul calendario settimanale (scorrere le settimane con le frecce) -> conferma prenotazione.
- **Le mie prenotazioni**: elenco e annullamento.
- **Amministrazione** (solo `admin`): CRUD Medici, CRUD Prestazioni, gestione
  Associazioni medico-prestazione, Gestione Utenti (crea/modifica/elimina
  utenti con ruolo e password; creando un utente *paziente* si registra anche il
  profilo con nome/cognome/codice fiscale), e Disponibilità con flusso a 3 passi:
  (1) Seleziona il medico, (2) genera slot ricorrenti indicando periodo, giorni della
  settimana, fascia oraria e durata, (3) rivedi gli slot su un calendario
  settimanale.
- **Agenda** (segreteria `operatore` e `admin`): vista di **tutte** le
  prenotazioni con nome paziente/medico/prestazione, filtro per stato e azioni
  Riprogramma / Completa / Annulla su qualsiasi appuntamento. La
  riprogrammazione propone gli altri slot liberi dello stesso medico.
- **Prenota per conto** (segreteria `operatore` e `admin`): nella scheda *Prenota*, la segreteria seleziona il paziente in cima e poi prenota normalmente scegliendo medico, prestazione e slot.

> Nota sui ruoli: prenotare per sé stessi e "Le mie prenotazioni" sono per gli
> account **paziente** (es. `mario.rossi@example.com`); la **segreteria**
> (`operatore`) prenota *per conto* dei pazienti e gestisce l'agenda di tutti.
> L'endpoint `/appuntamenti` (prenotazione personale) risponde `403` a un account
> non paziente.

## API principali

### Pubbliche / paziente / operatore
| Metodo | Endpoint | Ruolo | Descrizione |
|--------|----------|-------|-------------|
| POST | `/api/v1/auth/login` | pubblico | Login (JWT) |
| GET  | `/api/v1/auth/me` | autenticato | Utente corrente (ruolo) |
| GET  | `/api/v1/medici` | autenticato | Elenco medici |
| GET  | `/api/v1/medici/{id}/prestazioni` | autenticato | Prestazioni del medico |
| GET  | `/api/v1/medici/{id}/disponibilita` | autenticato | Slot liberi |
| GET  | `/api/v1/prestazioni` | autenticato | Catalogo prestazioni |
| POST | `/api/v1/appuntamenti` | paziente | Prenota (valida medico-prestazione) |
| GET  | `/api/v1/appuntamenti` | paziente | Le mie prenotazioni |
| PATCH| `/api/v1/appuntamenti/{id}` | paziente | Annulla |
| GET  | `/api/v1/appuntamenti/tutti` | operatore/admin | Agenda completa (paziente/medico/prestazione) |
| POST | `/api/v1/appuntamenti/operatore` | operatore/admin | Prenota per conto di un paziente |
| PATCH| `/api/v1/appuntamenti/tutti/{id}` | operatore/admin | Modifica (annulla / completa / riprogramma) |
| GET  | `/api/v1/pazienti` | operatore/admin | Elenco pazienti (per prenotare per conto) |

### Amministrative
| Metodo | Endpoint | Descrizione |
|--------|----------|-------------|
| GET/POST | `/api/v1/admin/medici` | Elenco / creazione medico |
| PUT/DELETE | `/api/v1/admin/medici/{id}` | Modifica / eliminazione |
| GET | `/api/v1/admin/medici/{id}/prestazioni` | Prestazioni associate |
| POST | `/api/v1/admin/medici/{id}/prestazioni` | Associa una prestazione |
| DELETE | `/api/v1/admin/medici/{id}/prestazioni/{prestazione_id}` | Rimuovi associazione |
| GET/POST | `/api/v1/admin/prestazioni` | Elenco / creazione prestazione |
| PUT/DELETE | `/api/v1/admin/prestazioni/{id}` | Modifica / eliminazione |
| GET/POST | `/api/v1/admin/disponibilita` | Elenco / creazione slot singolo |
| POST | `/api/v1/admin/disponibilita/genera` | Generazione ricorrente di slot (periodo + giorni + orari + durata) |
| PUT/DELETE | `/api/v1/admin/disponibilita/{id}` | Modifica / eliminazione |
| GET/POST | `/api/v1/admin/utenti` | Gestione utenti: elenco / creazione (email, password, ruolo) |
| PUT/DELETE | `/api/v1/admin/utenti/{id}` | Modifica (incl. password) / eliminazione |

Tutte le operazioni di scrittura amministrative e di segreteria sono tracciate
nell'`AuditLog`. L'elenco completo delle azioni registrate è in
[`docs/NOTE.md`](poliambulatorio-prenotazioni/docs/NOTE.md).

## Test

```
cd poliambulatorio-prenotazioni/backend
pytest
```

I test (cartella `backend/tests/`) usano un database SQLite dedicato
(`conftest.py`) e coprono: CRUD medici/prestazioni/disponibilità, associazioni
medico-prestazione, blocco delle prenotazioni non valide, autorizzazioni RBAC,
titolarità delle prenotazioni, stati terminali e vincoli sugli slot, gestione
utenti e audit log. Vanno eseguiti sull'intera cartella.

## Documentazione di progetto

La cartella [`docs/`](poliambulatorio-prenotazioni/docs/) raccoglie la
documentazione tecnica e i diagrammi in formato Mermaid, che GitHub renderizza
direttamente.

| Documento | Contenuto |
|---|---|
| [`NOTE.md`](poliambulatorio-prenotazioni/docs/NOTE.md) | Punto di ingresso: mappa requisiti-endpoint-test, matrice dei permessi, ciclo di vita della prenotazione, limiti noti |
| [`casi-uso.md`](poliambulatorio-prenotazioni/docs/casi-uso.md) | Attori e casi d'uso |
| [`architettura.md`](poliambulatorio-prenotazioni/docs/architettura.md) | Architettura a livelli e responsabilità |
| [`ER.md`](poliambulatorio-prenotazioni/docs/ER.md) | Modello dati: entità, relazioni e vincoli |
| [`classi-prenotazione.md`](poliambulatorio-prenotazioni/docs/classi-prenotazione.md) | Classi coinvolte nel flusso di prenotazione, dal router al database |
| [`sequenza-prenotazione.md`](poliambulatorio-prenotazioni/docs/sequenza-prenotazione.md) | Flusso completo della prenotazione |
| [`stati-prenotazione.md`](poliambulatorio-prenotazioni/docs/stati-prenotazione.md) | Ciclo di vita di un appuntamento |