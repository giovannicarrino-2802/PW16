"""Test su permessi e vincoli di integrita non coperti altrove:
- un paziente non puo' agire sulle prenotazioni di un altro paziente;
- una prenotazione non puo' essere spostata su uno slot gia occupato;
- uno slot gia prenotato non puo' essere eliminato dall'area amministrativa.
"""
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


def _scenario(spec, prestazione, giorno, n_slot=2):
    """Crea medico + prestazione associata + n slot futuri liberi.

    I test creano il proprio scenario invece di pescare dal seed, perche' il
    database e' condiviso fra i file della suite."""
    h = _admin()
    mid = client.post("/api/v1/admin/medici", headers=h,
                      json={"nome": "Vincoli", "cognome": "Test",
                            "specializzazione": spec}).json()["id"]
    pid = client.post("/api/v1/admin/prestazioni", headers=h,
                      json={"nome": prestazione, "durata_min": 30,
                            "prezzo": 60.0}).json()["id"]
    client.post(f"/api/v1/admin/medici/{mid}/prestazioni", headers=h,
                json={"prestazione_id": pid})
    slot_ids = []
    for i in range(n_slot):
        r = client.post("/api/v1/admin/disponibilita", headers=h, json={
            "medico_id": mid,
            "inizio": f"{giorno}T{9 + i:02d}:00:00",
            "fine": f"{giorno}T{9 + i:02d}:30:00",
        })
        assert r.status_code == 201, r.text
        slot_ids.append(r.json()["id"])
    return mid, pid, slot_ids


def _crea_paziente(email, cf, nome="Test", cognome="Paziente"):
    """Crea un utente paziente e ne restituisce gli header di autenticazione."""
    h = _admin()
    r = client.post("/api/v1/admin/utenti", headers=h,
                    json={"email": email, "password": "Paziente123!", "ruolo": "paziente",
                          "nome": nome, "cognome": cognome, "codice_fiscale": cf})
    assert r.status_code == 201, r.text
    return _h(email, "Paziente123!")


# --------------------------------------------------------------------------
# Permessi: un paziente non agisce sulle prenotazioni altrui
# --------------------------------------------------------------------------
def test_paziente_non_annulla_prenotazione_altrui():
    _, pid, slots = _scenario("Reumatologia", "Visita reumatologica", "2031-02-03", n_slot=1)
    ha = _crea_paziente("anna.verdi@example.com", "VRDNNA85B41F205K", "Anna", "Verdi")
    hb = _crea_paziente("bruno.neri@example.com", "NREBRN85B41F205J", "Bruno", "Neri")

    # Anna prenota
    r = client.post("/api/v1/appuntamenti", headers=ha,
                    json={"disponibilita_id": slots[0], "prestazione_id": pid})
    assert r.status_code == 201, r.text
    app_id = r.json()["id"]

    # Bruno prova ad annullare la prenotazione di Anna
    r = client.patch(f"/api/v1/appuntamenti/{app_id}", headers=hb, json={"stato": "annullata"})
    assert r.status_code == 403, r.text

    # La prenotazione di Anna e' rimasta attiva
    mie = client.get("/api/v1/appuntamenti", headers=ha).json()
    assert next(a for a in mie if a["id"] == app_id)["stato"] == "prenotata"

    # Bruno non vede la prenotazione di Anna fra le proprie
    assert all(a["id"] != app_id for a in client.get("/api/v1/appuntamenti", headers=hb).json())


# --------------------------------------------------------------------------
# Vincolo: riprogrammazione su slot gia occupato
# --------------------------------------------------------------------------
def test_riprogramma_su_slot_occupato():
    _, pid, slots = _scenario("Nefrologia", "Visita nefrologica", "2031-02-04", n_slot=2)
    op = _operatore()
    pazienti = client.get("/api/v1/pazienti", headers=op).json()
    p1, p2 = pazienti[0]["id"], pazienti[1]["id"]

    primo = client.post("/api/v1/appuntamenti/operatore", headers=op,
                        json={"paziente_id": p1, "disponibilita_id": slots[0],
                              "prestazione_id": pid}).json()["id"]
    client.post("/api/v1/appuntamenti/operatore", headers=op,
                json={"paziente_id": p2, "disponibilita_id": slots[1],
                      "prestazione_id": pid})

    # Il primo appuntamento non puo' spostarsi sullo slot del secondo
    r = client.patch(f"/api/v1/appuntamenti/tutti/{primo}", headers=op,
                     json={"disponibilita_id": slots[1]})
    assert r.status_code == 409, r.text


# --------------------------------------------------------------------------
# Vincolo: eliminazione di uno slot gia prenotato
# --------------------------------------------------------------------------
def test_elimina_slot_prenotato_bloccata():
    h = _admin()
    _, pid, slots = _scenario("Ematologia", "Visita ematologica", "2031-02-05", n_slot=1)
    sid = slots[0]

    op = _operatore()
    paziente_id = client.get("/api/v1/pazienti", headers=op).json()[0]["id"]
    app_id = client.post("/api/v1/appuntamenti/operatore", headers=op,
                         json={"paziente_id": paziente_id, "disponibilita_id": sid,
                               "prestazione_id": pid}).json()["id"]

    # Lo slot e' occupato: non deve essere eliminabile
    assert client.delete(f"/api/v1/admin/disponibilita/{sid}", headers=h).status_code == 409

    # Dopo l'annullamento lo slot torna libero ed e' eliminabile
    assert client.patch(f"/api/v1/appuntamenti/tutti/{app_id}", headers=op,
                        json={"stato": "annullata"}).status_code == 200
    assert client.delete(f"/api/v1/admin/disponibilita/{sid}", headers=h).status_code == 204
