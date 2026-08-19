# Modello dati - Diagramma ER

Sistema gestionale Poliambulatorio (v2.0). Le entita nuove/aggiornate rispetto
alla v1 sono **Medico**, **Prestazione**, **MedicoPrestazione** (nuova tabella di
associazione molti-a-molti) e **Disponibilita**.

```mermaid
erDiagram
    UTENTE ||--o| PAZIENTE : "ha profilo"
    UTENTE ||--o{ AUDIT_LOG : "genera"
    PAZIENTE ||--o{ APPUNTAMENTO : "prenota"
    MEDICO ||--o{ DISPONIBILITA : "offre"
    MEDICO ||--o{ MEDICO_PRESTAZIONE : "esegue"
    PRESTAZIONE ||--o{ MEDICO_PRESTAZIONE : "eseguibile da"
    MEDICO ||--o{ APPUNTAMENTO : "riceve"
    PRESTAZIONE ||--o{ APPUNTAMENTO : "richiesta in"
    DISPONIBILITA ||--o| APPUNTAMENTO : "occupato da"

    UTENTE {
        int id PK
        string email UK
        string password_hash
        string ruolo "paziente|operatore|admin"
        datetime creato_il
    }
    PAZIENTE {
        int id PK
        int utente_id FK,UK
        string nome
        string cognome
        string codice_fiscale UK
        string telefono
        date data_nascita
    }
    MEDICO {
        int id PK
        string nome
        string cognome
        string specializzazione
    }
    PRESTAZIONE {
        int id PK
        string nome
        int durata_min
        float prezzo
    }
    MEDICO_PRESTAZIONE {
        int id PK
        int medico_id FK
        int prestazione_id FK
    }
    DISPONIBILITA {
        int id PK
        int medico_id FK
        datetime inizio
        datetime fine
        bool occupato
    }
    APPUNTAMENTO {
        int id PK
        int paziente_id FK
        int medico_id FK
        int prestazione_id FK
        int disponibilita_id FK
        datetime inizio
        datetime fine
        string stato
        datetime creato_il
    }
    AUDIT_LOG {
        int id PK
        int utente_id FK
        string azione
        string entita
        int entita_id
        string dettagli
        datetime ts
    }
```

## Vincoli principali

- `MEDICO_PRESTAZIONE(medico_id, prestazione_id)` ha un vincolo di **unicita**
  (`uq_medico_prestazione`): la stessa coppia non puo' essere associata due volte.
- Un medico puo' eseguire **piu'** prestazioni; una prestazione puo' essere
  eseguita da **piu'** medici (molti-a-molti).
- Una prenotazione (`APPUNTAMENTO`) e' valida solo se la coppia
  `(medico_id, prestazione_id)` esiste in `MEDICO_PRESTAZIONE`.
- Uno slot `DISPONIBILITA` occupato non puo' essere prenotato di nuovo.

## DDL equivalente (SQLite)

```sql
CREATE TABLE medico_prestazione (
    id             INTEGER PRIMARY KEY,
    medico_id      INTEGER NOT NULL REFERENCES medico(id),
    prestazione_id INTEGER NOT NULL REFERENCES prestazione(id),
    CONSTRAINT uq_medico_prestazione UNIQUE (medico_id, prestazione_id)
);
```
