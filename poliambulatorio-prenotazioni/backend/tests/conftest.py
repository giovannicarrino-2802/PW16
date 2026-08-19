"""Configurazione dei test: usa un database SQLite isolato.

Il DATABASE_URL viene impostato PRIMA di importare l'applicazione, cosi'
i test non toccano il database di sviluppo (poliambulatorio.db) e partono
sempre da uno stato pulito e ripopolato dal seed.
"""
import os
import pathlib

_TEST_DB = pathlib.Path(__file__).resolve().parent / "test_poliambulatorio.db"
os.environ["DATABASE_URL"] = "sqlite:///" + _TEST_DB.as_posix()

# Stato pulito a ogni esecuzione della suite
if _TEST_DB.exists():
    _TEST_DB.unlink()
