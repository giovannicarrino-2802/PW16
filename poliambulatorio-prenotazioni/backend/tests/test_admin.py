"""Test delle funzionalita amministrative, delle associazioni medico-prestazione,
del blocco delle prenotazioni non valide, dell'RBAC e dell'audit log."""
from fastapi.testclient import TestClient
from app.main import app
from app.db.session import SessionLocal
from app.models.audit_log import AuditLog

client = TestClient(app)


def _token(email, pwd):
    r = client.post("/api/v1/auth/login", data={"username": email, "password": pwd})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def _admin():
    return {"Authorization": "Bearer " + _token("admin@example.com", "Admin123!")}


def _paziente():
    return {"Authorization": "Bearer " + _token("mario.rossi@example.com", "Password123!")}


# --------------------------------------------------------------------------
# RBAC
# --------------------------------------------------------------------------
def test_rbac_paziente_non_accede_admin():
    h = _paziente()
    assert client.get("/api/v1/admin/medici", headers=h).status_code == 403
    assert client.post("/api/v1/admin/medici", headers=h,
                       json={"nome": "X", "cognome": "Y", "specializzazione": "Z"}).status_code == 403


def test_rbac_senza_token():
    assert client.get("/api/v1/admin/medici").status_code == 401


def test_admin_accede():
    assert client.get("/api/v1/admin/medici", headers=_admin()).status_code == 200


# --------------------------------------------------------------------------
# CRUD Medici
# --------------------------------------------------------------------------
def test_crud_medico():
    h = _admin()
    r = client.post("/api/v1/admin/medici", headers=h,
                    json={"nome": "Elena", "cognome": "Conti", "specializzazione": "Neurologia"})
    assert r.status_code == 201, r.text
    mid = r.json()["id"]

    lista = client.get("/api/v1/admin/medici", headers=h).json()
    assert any(m["id"] == mid for m in lista)

    r = client.put(f"/api/v1/admin/medici/{mid}", headers=h,
                   json={"specializzazione": "Neurochirurgia"})
    assert r.status_code == 200
    assert r.json()["specializzazione"] == "Neurochirurgia"

    assert client.delete(f"/api/v1/admin/medici/{mid}", headers=h).status_code == 204
    lista = client.get("/api/v1/admin/medici", headers=h).json()
    assert not any(m["id"] == mid for m in lista)


# --------------------------------------------------------------------------
# CRUD Prestazioni (+ validazioni Pydantic)
# --------------------------------------------------------------------------
def test_crud_prestazione():
    h = _admin()
    r = client.post("/api/v1/admin/prestazioni", headers=h,
                    json={"nome": "Holter pressorio", "durata_min": 30, "prezzo": 85.0})
    assert r.status_code == 201, r.text
    pid = r.json()["id"]

    r = client.put(f"/api/v1/admin/prestazioni/{pid}", headers=h, json={"prezzo": 95.0})
    assert r.status_code == 200 and r.json()["prezzo"] == 95.0

    assert client.delete(f"/api/v1/admin/prestazioni/{pid}", headers=h).status_code == 204


def test_prestazione_validazione():
    h = _admin()
    assert client.post("/api/v1/admin/prestazioni", headers=h,
                       json={"nome": "Errata", "durata_min": 0, "prezzo": 10}).status_code == 422
    assert client.post("/api/v1/admin/prestazioni", headers=h,
                       json={"nome": "Errata", "durata_min": 20, "prezzo": -5}).status_code == 422


# --------------------------------------------------------------------------
# CRUD Disponibilita (+ validazione intervallo)
# --------------------------------------------------------------------------
def _nuovo_medico(h, spec="Endocrinologia"):
    return client.post("/api/v1/admin/medici", headers=h,
                       json={"nome": "Test", "cognome": "Medico", "specializzazione": spec}).json()["id"]


def test_crud_disponibilita():
    h = _admin()
    mid = _nuovo_medico(h, "Reumatologia")
    r = client.post("/api/v1/admin/disponibilita", headers=h,
                    json={"medico_id": mid, "inizio": "2030-01-07T09:00:00",
                          "fine": "2030-01-07T09:30:00"})
    assert r.status_code == 201, r.text
    sid = r.json()["id"]

    lista = client.get(f"/api/v1/admin/disponibilita?medico_id={mid}", headers=h).json()
    assert any(s["id"] == sid for s in lista)

    r = client.put(f"/api/v1/admin/disponibilita/{sid}", headers=h,
                   json={"fine": "2030-01-07T10:00:00"})
    assert r.status_code == 200

    assert client.delete(f"/api/v1/admin/disponibilita/{sid}", headers=h).status_code == 204


def test_disponibilita_intervallo_non_valido():
    h = _admin()
    mid = _nuovo_medico(h, "Pneumologia")
    # fine <= inizio -> 422 (validazione Pydantic)
    r = client.post("/api/v1/admin/disponibilita", headers=h,
                    json={"medico_id": mid, "inizio": "2030-02-01T10:00:00",
                          "fine": "2030-02-01T09:30:00"})
    assert r.status_code == 422


def test_genera_disponibilita_ricorrenti():
    """Generatore bulk: lun+gio, 09:00-11:00, slot 30' -> 4 slot per giorno."""
    h = _admin()
    mid = _nuovo_medico(h, "Nefrologia")
    r = client.post("/api/v1/admin/disponibilita/genera", headers=h, json={
        "medico_id": mid,
        "data_inizio": "2030-04-01",   # lunedi
        "data_fine": "2030-04-07",     # domenica successiva
        "giorni": [0, 3],              # lunedi e giovedi
        "ora_inizio": "09:00",
        "ora_fine": "11:00",
        "durata_min": 30,
    })
    assert r.status_code == 201, r.text
    body = r.json()
    # 1-7 aprile 2030: lunedi (1) e giovedi (4) -> 2 giorni * 4 slot = 8
    assert body["creati_count"] == 8
    assert body["saltati"] == 0
    slots = client.get(f"/api/v1/admin/disponibilita?medico_id={mid}", headers=h).json()
    assert len(slots) == 8

    # Rigenerando lo stesso periodo, tutti gli slot risultano sovrapposti -> saltati
    r2 = client.post("/api/v1/admin/disponibilita/genera", headers=h, json={
        "medico_id": mid, "data_inizio": "2030-04-01", "data_fine": "2030-04-07",
        "giorni": [0, 3], "ora_inizio": "09:00", "ora_fine": "11:00", "durata_min": 30,
    })
    assert r2.status_code == 201
    assert r2.json()["creati_count"] == 0
    assert r2.json()["saltati"] == 8


def test_genera_disponibilita_ora_non_valida():
    h = _admin()
    mid = _nuovo_medico(h, "Urologia")
    r = client.post("/api/v1/admin/disponibilita/genera", headers=h, json={
        "medico_id": mid, "data_inizio": "2030-05-01", "data_fine": "2030-05-31",
        "giorni": [0], "ora_inizio": "11:00", "ora_fine": "09:00", "durata_min": 30,
    })
    assert r.status_code == 400  # ora fine <= ora inizio (ValidationError di dominio)


# --------------------------------------------------------------------------
# Associazioni medico-prestazione
# --------------------------------------------------------------------------
def test_associazione_medico_prestazione():
    h = _admin()
    mid = _nuovo_medico(h, "Gastroenterologia")
    pid = client.post("/api/v1/admin/prestazioni", headers=h,
                      json={"nome": "Gastroscopia", "durata_min": 40, "prezzo": 200}).json()["id"]

    # inizialmente nessuna associazione
    assert client.get(f"/api/v1/admin/medici/{mid}/prestazioni", headers=h).json() == []

    r = client.post(f"/api/v1/admin/medici/{mid}/prestazioni", headers=h,
                    json={"prestazione_id": pid})
    assert r.status_code == 201, r.text

    # compare sia sull'endpoint admin sia su quello per utenti autenticati
    ass = client.get(f"/api/v1/admin/medici/{mid}/prestazioni", headers=h).json()
    assert any(p["id"] == pid for p in ass)
    pub = client.get(f"/api/v1/medici/{mid}/prestazioni", headers=_paziente()).json()
    assert any(p["id"] == pid for p in pub)

    # doppia associazione -> 409
    dup = client.post(f"/api/v1/admin/medici/{mid}/prestazioni", headers=h,
                      json={"prestazione_id": pid})
    assert dup.status_code == 409

    # rimozione
    assert client.delete(f"/api/v1/admin/medici/{mid}/prestazioni/{pid}",
                         headers=h).status_code == 204
    assert client.get(f"/api/v1/admin/medici/{mid}/prestazioni", headers=h).json() == []


# --------------------------------------------------------------------------
# Blocco prenotazioni non valide (prestazione non associata al medico)
# --------------------------------------------------------------------------
def test_prenotazione_non_valida_bloccata():
    ha = _admin()
    mid = _nuovo_medico(ha, "Allergologia")
    # slot futuro per il nuovo medico (nessuna prestazione associata)
    sid = client.post("/api/v1/admin/disponibilita", headers=ha,
                      json={"medico_id": mid, "inizio": "2030-03-10T09:00:00",
                            "fine": "2030-03-10T09:30:00"}).json()["id"]
    # una prestazione qualsiasi NON associata a questo medico
    pid = client.post("/api/v1/admin/prestazioni", headers=ha,
                      json={"nome": "Prick test", "durata_min": 20, "prezzo": 60}).json()["id"]

    hp = _paziente()
    r = client.post("/api/v1/appuntamenti", headers=hp,
                    json={"disponibilita_id": sid, "prestazione_id": pid})
    assert r.status_code == 400, r.text

    # dopo l'associazione la prenotazione diventa valida
    client.post(f"/api/v1/admin/medici/{mid}/prestazioni", headers=ha, json={"prestazione_id": pid})
    r2 = client.post("/api/v1/appuntamenti", headers=hp,
                     json={"disponibilita_id": sid, "prestazione_id": pid})
    assert r2.status_code == 201, r2.text


# --------------------------------------------------------------------------
# Audit log
# --------------------------------------------------------------------------
def test_audit_registra_operazioni_admin():
    h = _admin()
    r = client.post("/api/v1/admin/medici", headers=h,
                    json={"nome": "Audit", "cognome": "Prova", "specializzazione": "Test"})
    mid = r.json()["id"]
    db = SessionLocal()
    try:
        rec = (db.query(AuditLog)
               .filter(AuditLog.azione == "CREATE_MEDICO",
                       AuditLog.entita_id == mid)
               .first())
        assert rec is not None
    finally:
        db.close()
