"""Test delle funzionalita di segreteria (prenotazione per conto, agenda,
modifica prenotazioni) e della gestione utenti da parte dell'admin."""
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def _token(email, pwd):
    r = client.post("/api/v1/auth/login", data={"username": email, "password": pwd})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def _h(email, pwd):
    return {"Authorization": "Bearer " + _token(email, pwd)}


def _admin():
    return _h("admin@example.com", "Admin123!")


def _operatore():
    return _h("segreteria@example.com", "Segreteria123!")


def _paziente():
    return _h("mario.rossi@example.com", "Password123!")


def _slot_e_prestazione(medico_headers):
    """Ritorna (medico_id, prestazione_id, slot_id) validi e associati."""
    medici = client.get("/api/v1/medici", headers=medico_headers).json()
    for m in medici:
        prest = client.get(f"/api/v1/medici/{m['id']}/prestazioni", headers=medico_headers).json()
        slots = client.get(f"/api/v1/medici/{m['id']}/disponibilita", headers=medico_headers).json()
        if prest and slots:
            return m["id"], prest[0]["id"], slots[0]["id"]
    raise AssertionError("Nessun medico con prestazioni e slot disponibili")


# --------------------------------------------------------------------------
# RBAC di base sui nuovi endpoint
# --------------------------------------------------------------------------
def test_agenda_richiede_staff():
    assert client.get("/api/v1/appuntamenti/tutti", headers=_paziente()).status_code == 403
    assert client.get("/api/v1/appuntamenti/tutti", headers=_operatore()).status_code == 200
    assert client.get("/api/v1/appuntamenti/tutti", headers=_admin()).status_code == 200


def test_lista_pazienti_staff():
    assert client.get("/api/v1/pazienti", headers=_paziente()).status_code == 403
    r = client.get("/api/v1/pazienti", headers=_operatore())
    assert r.status_code == 200
    assert any(p["codice_fiscale"] == "RSSMRA80A01F205X" for p in r.json())


# --------------------------------------------------------------------------
# Segreteria prenota per conto del paziente + agenda + modifica
# --------------------------------------------------------------------------
def test_segreteria_prenota_per_paziente_e_modifica():
    op = _operatore()
    pazienti = client.get("/api/v1/pazienti", headers=op).json()
    paziente_id = pazienti[0]["id"]
    mid, pid, sid = _slot_e_prestazione(op)

    # Prenotazione per conto del paziente
    r = client.post("/api/v1/appuntamenti/operatore", headers=op,
                    json={"paziente_id": paziente_id, "disponibilita_id": sid, "prestazione_id": pid})
    assert r.status_code == 201, r.text
    app_id = r.json()["id"]

    # Compare nell'agenda con i dati arricchiti
    agenda = client.get("/api/v1/appuntamenti/tutti", headers=op).json()
    riga = next(a for a in agenda if a["id"] == app_id)
    assert riga["paziente_nome"] and riga["medico_nome"] and riga["prestazione_nome"]

    # Riprogramma su un altro slot libero dello stesso medico
    slots = client.get(f"/api/v1/medici/{mid}/disponibilita", headers=op).json()
    nuovo = next((s for s in slots if s["id"] != sid), None)
    if nuovo:
        r = client.patch(f"/api/v1/appuntamenti/tutti/{app_id}", headers=op,
                         json={"disponibilita_id": nuovo["id"]})
        assert r.status_code == 200, r.text

    # Completa
    r = client.patch(f"/api/v1/appuntamenti/tutti/{app_id}", headers=op, json={"stato": "completata"})
    assert r.status_code == 200 and r.json()["stato"] == "completata"


def test_segreteria_prenota_paziente_inesistente():
    op = _operatore()
    _, pid, sid = _slot_e_prestazione(op)
    r = client.post("/api/v1/appuntamenti/operatore", headers=op,
                    json={"paziente_id": 999999, "disponibilita_id": sid, "prestazione_id": pid})
    assert r.status_code == 404


def test_paziente_non_usa_endpoint_operatore():
    hp = _paziente()
    _, pid, sid = _slot_e_prestazione(hp)
    r = client.post("/api/v1/appuntamenti/operatore", headers=hp,
                    json={"paziente_id": 1, "disponibilita_id": sid, "prestazione_id": pid})
    assert r.status_code == 403


# --------------------------------------------------------------------------
# Gestione utenti (admin)
# --------------------------------------------------------------------------
def test_crud_utente_operatore():
    h = _admin()
    r = client.post("/api/v1/admin/utenti", headers=h,
                    json={"email": "nuovo.operatore@example.com", "password": "Operatore123!",
                          "ruolo": "operatore"})
    assert r.status_code == 201, r.text
    uid = r.json()["id"]
    assert r.json()["ruolo"] == "operatore"

    # login del nuovo operatore
    assert client.post("/api/v1/auth/login",
                       data={"username": "nuovo.operatore@example.com",
                             "password": "Operatore123!"}).status_code == 200

    # cambio password
    r = client.put(f"/api/v1/admin/utenti/{uid}", headers=h, json={"password": "Cambiata123!"})
    assert r.status_code == 200
    assert client.post("/api/v1/auth/login",
                       data={"username": "nuovo.operatore@example.com",
                             "password": "Cambiata123!"}).status_code == 200

    # eliminazione
    assert client.delete(f"/api/v1/admin/utenti/{uid}", headers=h).status_code == 204


def test_crea_utente_paziente_con_profilo():
    h = _admin()
    r = client.post("/api/v1/admin/utenti", headers=h,
                    json={"email": "nuovo.paziente@example.com", "password": "Paziente123!",
                          "ruolo": "paziente", "nome": "Ada", "cognome": "Lovelace",
                          "codice_fiscale": "LVLADA90A01F205Z"})
    assert r.status_code == 201, r.text

    # il paziente compare nell'elenco pazienti della segreteria
    pazienti = client.get("/api/v1/pazienti", headers=_operatore()).json()
    assert any(p["codice_fiscale"] == "LVLADA90A01F205Z" for p in pazienti)


def test_crea_utente_paziente_senza_dati_400():
    h = _admin()
    r = client.post("/api/v1/admin/utenti", headers=h,
                    json={"email": "incompleto@example.com", "password": "Paziente123!",
                          "ruolo": "paziente"})
    assert r.status_code == 400


def test_utenti_rbac_e_self_delete():
    # paziente non accede
    assert client.get("/api/v1/admin/utenti", headers=_paziente()).status_code == 403
    # admin non puo' eliminare se stesso
    utenti = client.get("/api/v1/admin/utenti", headers=_admin()).json()
    me = next(u for u in utenti if u["email"] == "admin@example.com")
    assert client.delete(f"/api/v1/admin/utenti/{me['id']}", headers=_admin()).status_code == 403


def test_email_duplicata_409():
    h = _admin()
    r = client.post("/api/v1/admin/utenti", headers=h,
                    json={"email": "admin@example.com", "password": "Qualcosa123!",
                          "ruolo": "operatore"})
    assert r.status_code == 409
