# Migrazione del database (v1 -> v2)

La v2 introduce la nuova tabella **`medico_prestazione`** e un seed piu' ricco
(5 medici, 10 prestazioni, associazioni e disponibilita realistiche, utente
amministratore). Non ci sono modifiche di colonna alle tabelle esistenti: la
nuova tabella viene creata automaticamente da `Base.metadata.create_all()`
all'avvio.

## Opzione A - Reset completo (consigliata per demo/sviluppo)

Il modo piu' semplice e' rigenerare il database da zero: il seed ripopola tutto.

```bash
cd backend
rm -f poliambulatorio.db        # elimina il vecchio database
uvicorn app.main:app --reload   # ricrea schema + seed (5 medici, 10 prestazioni...)
```

Al riavvio vengono create tutte le tabelle (inclusa `medico_prestazione`) e
inseriti i dati di esempio con le associazioni medico-prestazione.

## Opzione B - Migrazione non distruttiva (mantenere i dati esistenti)

Se occorre preservare i dati gia presenti, eseguire lo script di migrazione che:
1. crea la tabella `medico_prestazione` se assente;
2. NON tocca le altre tabelle.

```bash
cd backend
python -m app.db.migrate     # crea la sola tabella mancante
```

> Nota: dopo l'opzione B le associazioni medico-prestazione risulteranno vuote;
> vanno create dall'area amministrativa (o via API `POST /api/v1/admin/medici/{id}/prestazioni`).
> Finche' un medico non ha prestazioni associate, le sue prenotazioni verranno
> rifiutate (comportamento voluto).

## Opzione C - Alembic (produzione)

Il progetto usa SQLite con `create_all` per semplicita didattica. In un contesto
di produzione si consiglia Alembic:

```bash
pip install alembic
alembic init migrations
# configurare sqlalchemy.url e target_metadata = Base.metadata
alembic revision --autogenerate -m "add medico_prestazione"
alembic upgrade head
```
