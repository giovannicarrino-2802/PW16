"""Test del flusso di prenotazione del paziente: login, prestazioni del
medico, creazione della prenotazione e conflitto sullo slot occupato."""
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def _login(email, pwd):
    r = client.post("/api/v1/auth/login", data={"username": email, "password": pwd})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def _auth(email="mario.rossi@example.com", pwd="Password123!"):
    return {"Authorization": "Bearer " + _login(email, pwd)}


def test_login_demo():
    assert _login("mario.rossi@example.com", "Password123!")


def test_me_ritorna_ruolo():
    h = _auth()
    me = client.get("/api/v1/auth/me", headers=h).json()
    assert me["email"] == "mario.rossi@example.com"
    assert me["ruolo"] == "paziente"


def test_prenota_e_lista():
    h = _auth()
    medici = client.get("/api/v1/medici", headers=h).json()
    mid = medici[0]["id"]
    prest = client.get(f"/api/v1/medici/{mid}/prestazioni", headers=h).json()
    assert prest, "il medico deve avere prestazioni associate"
    pid = prest[0]["id"]
    slots = client.get(f"/api/v1/medici/{mid}/disponibilita", headers=h).json()
    assert slots
    r = client.post("/api/v1/appuntamenti", headers=h,
                    json={"disponibilita_id": slots[0]["id"], "prestazione_id": pid})
    assert r.status_code == 201, r.text
    assert len(client.get("/api/v1/appuntamenti", headers=h).json()) >= 1


def test_slot_occupato_genera_conflitto():
    h = _auth()
    medici = client.get("/api/v1/medici", headers=h).json()
    mid = medici[0]["id"]
    prest = client.get(f"/api/v1/medici/{mid}/prestazioni", headers=h).json()
    pid = prest[0]["id"]
    slots = client.get(f"/api/v1/medici/{mid}/disponibilita", headers=h).json()
    sid = slots[0]["id"]
    client.post("/api/v1/appuntamenti", headers=h,
                json={"disponibilita_id": sid, "prestazione_id": pid})
    r2 = client.post("/api/v1/appuntamenti", headers=h,
                     json={"disponibilita_id": sid, "prestazione_id": pid})
    assert r2.status_code == 409


def test_prestazioni_del_medico():
    """L'endpoint ritorna solo le prestazioni associate al medico e richiede
    un utente autenticato."""
    h = _auth()
    medici = client.get("/api/v1/medici", headers=h).json()
    mid = medici[0]["id"]
    prest = client.get(f"/api/v1/medici/{mid}/prestazioni", headers=h).json()
    assert isinstance(prest, list) and len(prest) >= 1
    for p in prest:
        assert "id" in p and "nome" in p
    # senza token l'endpoint non e' accessibile
    assert client.get(f"/api/v1/medici/{mid}/prestazioni").status_code == 401
