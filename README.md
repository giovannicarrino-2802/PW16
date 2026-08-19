# Poliambulatorio - Sistema gestionale prenotazioni

Applicazione full-stack API-based per la gestione di un poliambulatorio:
prenotazione di visite specialistiche **e** area amministrativa completa per la
gestione di medici, prestazioni, disponibilita e associazioni medico-prestazione.

Project Work PW16 - CdS Informatica per le Aziende Digitali (L-31).

## Architettura (a livelli)

```
Front-end (HTML/CSS/JS)  ->  API REST (FastAPI)  ->  Servizi (business)
->  Repository (accesso dati)  ->  Modelli ORM  ->  Database (SQLAlchemy + SQLite)
```

Trasversale: sicurezza (JWT + RBAC), validazione (Pydantic), audit log.

Il livello **Servizi** applica le regole di business (es. una prestazione puo'
essere prenotata solo se associata al medico); il livello **Repository** isola
l'accesso ai dati; le **API** traducono le eccezioni di dominio in codici HTTP.

## Architettura e funzionalita principali

1. **Entita `MedicoPrestazione`**: tabella di associazione molti-a-molti
   tra `Medico` e `Prestazione` (`id`, `medico_id`, `prestazione_id`, con vincolo
   di unicita). Relazioni ORM `Medico.prestazioni` / `Prestazione.medici` e
   `Medico.disponibilita`.
2. **Repository**: `MedicoRepository`, `PrestazioneRepository`,
   `DisponibilitaRepository`, oltre a quello degli appuntamenti, esteso con
   `prestazione()` e `medico_esegue()`.
3. **Servizi**: `MedicoService`, `PrestazioneService`,
   `DisponibilitaService`, ognuno con audit log integrato. Eccezioni di dominio
   centralizzate in `services/exceptions.py`
   (`NotFound/Forbidden/Conflict/ValidationError`).
4. **Router amministrativi** in `app/api/v1/admin/` protetti via RBAC
   (`require_admin`, ruolo `admin`), con gestione errori centralizzata tramite
   `exception_handler` in `main.py`.
5. **Validazione della prenotazione**: la coppia medico-prestazione viene sempre
   verificata; le richieste non valide restituiscono `400`.
6. **Endpoint** `GET /medici/{id}/prestazioni` e `GET /auth/me` (per il ruolo
   lato front-end), entrambi riservati agli utenti autenticati.
7. **Front-end**: tendina prestazioni popolata in base al medico,
   selezione slot tramite **calendario settimanale scorrevole**, e **area
   amministrativa** visibile solo agli utenti `admin`.
8. **Seed**: 5 medici, 10 prestazioni, associazioni e disponibilita
   realistiche, utente amministratore.

## Avvio del back-end

> Nota: `requirements.txt` si trova nella **root del progetto**, non in
> `backend/`. Avviando dal folder `backend/`, installa le dipendenze con
> `..\requirements.txt` (Windows) oppure `../requirements.txt` (macOS/Linux).

### Windows (PowerShell)

```powershell
cd backend
python -m venv .venv
.venv\Scripts\activate
# Se l'attivazione e' bloccata dalla policy, esegui prima:
#   Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process
# poi riprova ad attivare il venv.
pip install -r ..\requirements.txt
uvicorn app.main:app --reload
```

### macOS / Linux

```bash
cd backend
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
- **Admin:   admin@example.com        /  Admin123!**

## Front-end
Apri `frontend/index.html` nel browser (con il back-end avviato).

- **Prenota una visita**: scegli il medico -> la tendina delle prestazioni si
  popola con le sole prestazioni erogate da quel medico -> seleziona uno slot
  sul calendario settimanale (scorri le settimane con le frecce) -> conferma.
- **Le mie prenotazioni**: elenco e annullamento.
- **Amministrazione** (solo `admin`): CRUD Medici, CRUD Prestazioni, gestione
  Associazioni medico-prestazione, **Gestione Utenti** (crea/modifica/elimina
  utenti con ruolo e password; creando un utente *paziente* si registra anche il
  profilo con nome/cognome/codice fiscale), e **Disponibilita** con flusso a 3 passi:
  (1) scegli il medico, (2) genera slot ricorrenti indicando periodo, giorni della
  settimana, fascia oraria e durata, (3) rivedi gli slot su un calendario
  settimanale ed eliminane singolarmente quelli non voluti (gli slot gia prenotati
  non sono eliminabili).

- **Agenda** (segreteria `operatore` e `admin`): vista di **tutte** le
  prenotazioni con nome paziente/medico/prestazione, filtro per stato e azioni
  **Riprogramma / Completa / Annulla** su qualsiasi appuntamento.
- **Prenota per conto** (segreteria): nella scheda *Prenota*, la segreteria
  seleziona il paziente in cima e poi prenota normalmente scegliendo medico,
  prestazione e slot.

> Nota sui ruoli: prenotare per se stessi e "Le mie prenotazioni" sono per gli
> account **paziente** (es. `mario.rossi@example.com`); la **segreteria**
> (`operatore`) prenota *per conto* dei pazienti e gestisce l'agenda di tutti.
> L'endpoint `/appuntamenti` (prenotazione personale) risponde `403` a un account
> non paziente.

## API principali

### Pubbliche / paziente / operatore
| Metodo | Endpoint | Ruolo | Descrizione |
|--------|----------|-------|-------------|
| POST | `/api/v1/auth/register` | pubblico | Registrazione paziente |
| POST | `/api/v1/auth/login` | pubblico | Login (JWT) |
| GET  | `/api/v1/auth/me` | autenticato | Utente corrente (ruolo) |
| GET  | `/api/v1/medici` | autenticato | Elenco medici |
| GET  | `/api/v1/medici/{id}/prestazioni` | autenticato | **Prestazioni del medico** |
| GET  | `/api/v1/medici/{id}/disponibilita` | autenticato | Slot liberi |
| GET  | `/api/v1/prestazioni` | autenticato | Catalogo prestazioni |
| POST | `/api/v1/appuntamenti` | paziente | Prenota (valida medico-prestazione) |
| GET  | `/api/v1/appuntamenti` | paziente | Le mie prenotazioni |
| PATCH| `/api/v1/appuntamenti/{id}` | paziente | Annulla |
| GET  | `/api/v1/appuntamenti/tutti` | operatore/admin | **Agenda completa** (paziente/medico/prestazione) |
| POST | `/api/v1/appuntamenti/operatore` | operatore/admin | **Prenota per conto** di un paziente |
| PATCH| `/api/v1/appuntamenti/tutti/{id}` | operatore/admin | **Modifica** (annulla / completa / riprogramma) |
| GET  | `/api/v1/pazienti` | operatore/admin | Elenco pazienti (per prenotare per conto) |

### Amministrative (ruolo `admin`, RBAC)
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
| POST | `/api/v1/admin/disponibilita/genera` | **Generazione ricorrente** di slot (periodo + giorni + orari + durata) |
| PUT/DELETE | `/api/v1/admin/disponibilita/{id}` | Modifica / eliminazione |
| GET/POST | `/api/v1/admin/utenti` | **Gestione utenti**: elenco / creazione (email, password, ruolo) |
| PUT/DELETE | `/api/v1/admin/utenti/{id}` | Modifica (incl. password) / eliminazione |

Tutte le operazioni di scrittura amministrative e di segreteria sono tracciate
nell'`AuditLog`. L'elenco completo delle azioni registrate e' in
[`docs/NOTE.md`](docs/NOTE.md).

## Test

```
cd backend
pytest
```

I test (cartella `backend/tests/`) usano un database SQLite isolato
(`conftest.py`) e coprono: CRUD medici/prestazioni/disponibilita, associazioni,
blocco delle prenotazioni non valide, autorizzazioni RBAC, endpoint pubblico e
audit log.

## Diagramma ER
Vedi [`docs/ER.md`](docs/ER.md) (entita: Utente, Paziente, Medico, Prestazione,
MedicoPrestazione, Disponibilita, Appuntamento, AuditLog).

## Struttura
- `backend/app/api`          -> livello API (router REST, incl. `admin/`)
- `backend/app/services`     -> regole di business (+ `exceptions.py`)
- `backend/app/repositories` -> accesso ai dati
- `backend/app/models`       -> entita ORM (SQLAlchemy)
- `backend/app/schemas`      -> DTO (Pydantic)
- `backend/app/core`         -> configurazione e sicurezza (JWT, hashing)
- `backend/app/db`           -> base, sessione, seed
- `frontend/`                -> interfaccia utente (booking + admin)
- `docs/`                    -> diagrammi ER e note di progetto