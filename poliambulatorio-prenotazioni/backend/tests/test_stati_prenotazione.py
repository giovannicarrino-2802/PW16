"""Test sul ciclo di vita della prenotazione: `annullata` e `completata` sono
stati terminali e non ammettono ulteriori transizioni."""
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


def _scenario(spec, prestazione, giorno, n_slot=2):
    """Crea medico + prestazione associata + n slot futuri liberi.

    Ritorna (medico_id, prestazione_id, [slot_id, ...])."""
    h = _admin()
    mid = client.post("/api/v1/admin/medici", headers=h,
                      json={"nome": "Stati", "cognome": "Test",
                            "specializzazione": spec}).json()["id"]
    pid = client.post("/api/v1/admin/prestazioni", headers=h,
                      json={"nome": prestazione, "durata_min": 30,
                            "prezzo": 50.0}).json()["id"]
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


# --------------------------------------------------------------------------
# Paziente
# --------------------------------------------------------------------------
def test_paziente_non_annulla_due_volte():
    _, pid, slots = _scenario("Angiologia", "Ecocolordoppler", "2031-01-13", n_slot=1)
    hp = _paziente()
    app_id = client.post("/api/v1/appuntamenti", headers=hp,
                         json={"disponibilita_id": slots[0],
                               "prestazione_id": pid}).json()["id"]

    r = client.patch(f"/api/v1/appuntamenti/{app_id}", headers=hp, json={"stato": "annullata"})
    assert r.status_code == 200, r.text
    # Il secondo annullamento non deve liberare di nuovo lo slot
    r2 = client.patch(f"/api/v1/appuntamenti/{app_id}", headers=hp, json={"stato": "annullata"})
    assert r2.status_code == 409, r2.text


# --------------------------------------------------------------------------
# Segreteria / admin
# --------------------------------------------------------------------------
def test_segreteria_non_annulla_due_volte():
    _, pid, slots = _scenario("Epatologia", "Elastografia epatica", "2031-01-14", n_slot=1)
    op = _operatore()
    paziente_id = client.get("/api/v1/pazienti", headers=op).json()[0]["id"]
    app_id = client.post("/api/v1/appuntamenti/operatore", headers=op,
                         json={"paziente_id": paziente_id, "disponibilita_id": slots[0],
                               "prestazione_id": pid}).json()["id"]

    assert client.patch(f"/api/v1/appuntamenti/tutti/{app_id}", headers=op,
                        json={"stato": "annullata"}).status_code == 200
    r = client.patch(f"/api/v1/appuntamenti/tutti/{app_id}", headers=op,
                     json={"stato": "annullata"})
    assert r.status_code == 409, r.text


def test_riprogramma_solo_prenotazioni_attive():
    """Riprogrammare una prenotazione annullata libererebbe il vecchio slot,
    che nel frattempo puo' appartenere a un'altra prenotazione."""
    _, pid, slots = _scenario("Andrologia", "Visita andrologica", "2031-01-15", n_slot=2)
    op = _operatore()
    paziente_id = client.get("/api/v1/pazienti", headers=op).json()[0]["id"]
    app_id = client.post("/api/v1/appuntamenti/operatore", headers=op,
                         json={"paziente_id": paziente_id, "disponibilita_id": slots[0],
                               "prestazione_id": pid}).json()["id"]

    # Riprogrammazione valida su una prenotazione attiva
    r = client.patch(f"/api/v1/appuntamenti/tutti/{app_id}", headers=op,
                     json={"disponibilita_id": slots[1]})
    assert r.status_code == 200, r.text

    # Dopo l'annullamento la prenotazione e' terminata: niente riprogrammazione
    assert client.patch(f"/api/v1/appuntamenti/tutti/{app_id}", headers=op,
                        json={"stato": "annullata"}).status_code == 200
    r2 = client.patch(f"/api/v1/appuntamenti/tutti/{app_id}", headers=op,
                      json={"disponibilita_id": slots[0]})
    assert r2.status_code == 409, r2.text


def test_riprogramma_prenotazione_completata():
    _, pid, slots = _scenario("Algologia", "Visita algologica", "2031-01-16", n_slot=2)
    op = _operatore()
    paziente_id = client.get("/api/v1/pazienti", headers=op).json()[0]["id"]
    app_id = client.post("/api/v1/appuntamenti/operatore", headers=op,
                         json={"paziente_id": paziente_id, "disponibilita_id": slots[0],
                               "prestazione_id": pid}).json()["id"]

    assert client.patch(f"/api/v1/appuntamenti/tutti/{app_id}", headers=op,
                        json={"stato": "completata"}).status_code == 200
    r = client.patch(f"/api/v1/appuntamenti/tutti/{app_id}", headers=op,
                     json={"disponibilita_id": slots[1]})
    assert r.status_code == 409, r.text


def test_riprogramma_solo_stesso_medico():
    """La riprogrammazione sposta l'orario, non il medico: uno slot di un altro
    medico viene respinto anche se quel medico esegue la stessa prestazione."""
    h = _admin()
    _, pid, slots = _scenario("Immunologia", "Visita immunologica", "2031-01-17", n_slot=1)

    # Secondo medico che eroga la stessa prestazione, con un proprio slot
    altro_mid = client.post("/api/v1/admin/medici", headers=h,
                            json={"nome": "Altro", "cognome": "Medico",
                                  "specializzazione": "Immunologia clinica"}).json()["id"]
    client.post(f"/api/v1/admin/medici/{altro_mid}/prestazioni", headers=h,
                json={"prestazione_id": pid})
    altro_slot = client.post("/api/v1/admin/disponibilita", headers=h, json={
        "medico_id": altro_mid,
        "inizio": "2031-01-17T15:00:00",
        "fine": "2031-01-17T15:30:00",
    }).json()["id"]

    op = _operatore()
    paziente_id = client.get("/api/v1/pazienti", headers=op).json()[0]["id"]
    app_id = client.post("/api/v1/appuntamenti/operatore", headers=op,
                         json={"paziente_id": paziente_id, "disponibilita_id": slots[0],
                               "prestazione_id": pid}).json()["id"]

    r = client.patch(f"/api/v1/appuntamenti/tutti/{app_id}", headers=op,
                     json={"disponibilita_id": altro_slot})
    assert r.status_code == 409, r.text