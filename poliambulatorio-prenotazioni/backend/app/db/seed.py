from datetime import datetime, timedelta
from app.db.session import SessionLocal
from app.core.security import hash_password
from app.models.utente import Utente
from app.models.paziente import Paziente
from app.models.medico import Medico
from app.models.prestazione import Prestazione
from app.models.medico_prestazione import MedicoPrestazione
from app.models.disponibilita import Disponibilita


def _crea_medici(db):
    medici = {
        "bianchi": Medico(nome="Anna", cognome="Bianchi", specializzazione="Cardiologia"),
        "verdi":   Medico(nome="Luca", cognome="Verdi", specializzazione="Dermatologia"),
        "neri":    Medico(nome="Marco", cognome="Neri", specializzazione="Ortopedia"),
        "russo":   Medico(nome="Giulia", cognome="Russo", specializzazione="Ginecologia"),
        "gallo":   Medico(nome="Paolo", cognome="Gallo", specializzazione="Oculistica"),
    }
    db.add_all(list(medici.values()))
    db.commit()
    for m in medici.values():
        db.refresh(m)
    return medici


def _crea_prestazioni(db):
    prest = {
        "cardio":     Prestazione(nome="Visita cardiologica", durata_min=30, prezzo=120.0),
        "ecg":        Prestazione(nome="Elettrocardiogramma (ECG)", durata_min=20, prezzo=60.0),
        "derma":      Prestazione(nome="Visita dermatologica", durata_min=20, prezzo=90.0),
        "nei":        Prestazione(nome="Mappatura dei nei", durata_min=30, prezzo=110.0),
        "orto":       Prestazione(nome="Visita ortopedica", durata_min=30, prezzo=100.0),
        "infiltraz":  Prestazione(nome="Infiltrazione articolare", durata_min=20, prezzo=80.0),
        "gineco":     Prestazione(nome="Visita ginecologica", durata_min=30, prezzo=110.0),
        "eco":        Prestazione(nome="Ecografia ostetrica", durata_min=30, prezzo=130.0),
        "oculistica": Prestazione(nome="Visita oculistica", durata_min=25, prezzo=95.0),
        "campo":      Prestazione(nome="Esame del campo visivo", durata_min=20, prezzo=70.0),
    }
    db.add_all(list(prest.values()))
    db.commit()
    for p in prest.values():
        db.refresh(p)
    return prest


def _associa(db, medici, prest):
    # Ogni medico esegue le prestazioni della propria area.
    mappa = {
        "bianchi": ["cardio", "ecg"],
        "verdi":   ["derma", "nei"],
        "neri":    ["orto", "infiltraz"],
        "russo":   ["gineco", "eco"],
        "gallo":   ["oculistica", "campo"],
    }
    for chiave_medico, prestazioni in mappa.items():
        for chiave_prest in prestazioni:
            db.add(MedicoPrestazione(medico_id=medici[chiave_medico].id,
                                     prestazione_id=prest[chiave_prest].id))
    db.commit()


def _crea_disponibilita(db, medici):
    # Slot da 30 minuti, 09:00-13:00, nei prossimi 14 giorni feriali (Lun-Ven).
    oggi = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    for m in medici.values():
        for delta in range(1, 15):
            giorno = oggi + timedelta(days=delta)
            if giorno.weekday() >= 5:  # sabato/domenica esclusi
                continue
            for mezze_ore in range(8):  # 09:00 -> 13:00
                inizio = giorno.replace(hour=9) + timedelta(minutes=30 * mezze_ore)
                db.add(Disponibilita(medico_id=m.id, inizio=inizio,
                                     fine=inizio + timedelta(minutes=30)))
    db.commit()


def _crea_utenti(db):
    if not db.query(Utente).filter(Utente.email == "mario.rossi@example.com").first():
        u = Utente(email="mario.rossi@example.com",
                   password_hash=hash_password("Password123!"), ruolo="paziente")
        db.add(u); db.commit(); db.refresh(u)
        db.add(Paziente(utente_id=u.id, nome="Mario", cognome="Rossi",
                        codice_fiscale="RSSMRA80A01F205X", telefono="3331234567"))
        db.commit()
    if not db.query(Utente).filter(Utente.email == "segreteria@example.com").first():
        db.add(Utente(email="segreteria@example.com",
                      password_hash=hash_password("Segreteria123!"), ruolo="operatore"))
        db.commit()
    if not db.query(Utente).filter(Utente.email == "admin@example.com").first():
        db.add(Utente(email="admin@example.com",
                      password_hash=hash_password("Admin123!"), ruolo="admin"))
        db.commit()


def run():
    db = SessionLocal()
    try:
        if db.query(Medico).count() == 0:
            medici = _crea_medici(db)
            prest = _crea_prestazioni(db)
            _associa(db, medici, prest)
            _crea_disponibilita(db, medici)
        _crea_utenti(db)
    finally:
        db.close()
