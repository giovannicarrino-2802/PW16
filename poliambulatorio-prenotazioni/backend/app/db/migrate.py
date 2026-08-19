"""Migrazione non distruttiva v1 -> v2.

Crea le tabelle mancanti (in particolare `medico_prestazione`) senza toccare i
dati gia presenti. `create_all` non ricrea ne' altera le tabelle esistenti.

Uso:
    cd backend
    python -m app.db.migrate
"""
from app.db.base import Base
from app.db.session import engine
# Import necessario per registrare TUTTI i modelli nel metadata
from app.models import (utente, paziente, medico, prestazione, medico_prestazione,
                        disponibilita, appuntamento, audit_log)  # noqa: F401


def run():
    Base.metadata.create_all(bind=engine)
    print("Migrazione completata: tabelle mancanti create (incl. medico_prestazione).")


if __name__ == "__main__":
    run()
