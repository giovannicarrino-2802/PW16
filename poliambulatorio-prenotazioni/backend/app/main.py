from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app.db.base import Base
from app.db.session import engine
# Import necessario a registrare i modelli in Base.metadata
from app.models import (utente, paziente, medico, prestazione, medico_prestazione,
                        disponibilita, appuntamento, audit_log)  # noqa: F401
from app.db import seed
from app.api.v1 import auth, medici, prestazioni, appuntamenti, pazienti
from app.api.v1.admin import (medici as admin_medici,
                              prestazioni as admin_prestazioni,
                              disponibilita as admin_disponibilita,
                              utenti as admin_utenti)
from app.services.exceptions import (NotFoundError, ForbiddenError,
                                     ConflictError, ValidationError)

Base.metadata.create_all(bind=engine)
seed.run()   # dati di esempio, idempotente

app = FastAPI(title="Piattaforma di prenotazione di visite specialistiche - API", version="1.0.0",
              description="Project Work PW16 - Sviluppo di una applicazione full-stack API-based per"
                          "un’organizzazione del settore sanitario" \
                          "Applicativo gestionale per poliambulatorio: prenotazioni, "
                          "gestione medici/prestazioni/disponibilita e area "
                          "amministrativa.")

# Auth via header Bearer, non cookie: credenziali cross-origin non necessarie.
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=False,
                   allow_methods=["*"], allow_headers=["*"])


# --- Mappatura eccezioni di dominio -> codici HTTP -------------------------
_STATUS = {
    NotFoundError: 404,
    ForbiddenError: 403,
    ConflictError: 409,
    ValidationError: 400,
}


def _service_error_handler(request: Request, exc: Exception):
    status_code = _STATUS.get(type(exc), 400)
    return JSONResponse(status_code=status_code, content={"detail": str(exc)})


for _exc in (NotFoundError, ForbiddenError, ConflictError, ValidationError):
    app.add_exception_handler(_exc, _service_error_handler)


# --- Router pubblici / paziente / operatore --------------------------------
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(medici.router, prefix="/api/v1/medici", tags=["medici"])
app.include_router(prestazioni.router, prefix="/api/v1/prestazioni", tags=["prestazioni"])
app.include_router(appuntamenti.router, prefix="/api/v1/appuntamenti", tags=["appuntamenti"])
app.include_router(pazienti.router, prefix="/api/v1/pazienti", tags=["pazienti"])

# --- Router amministrativi (RBAC: admin) -----------------------------------
app.include_router(admin_medici.router, prefix="/api/v1/admin/medici", tags=["admin-medici"])
app.include_router(admin_prestazioni.router, prefix="/api/v1/admin/prestazioni",
                   tags=["admin-prestazioni"])
app.include_router(admin_disponibilita.router, prefix="/api/v1/admin/disponibilita",
                   tags=["admin-disponibilita"])
app.include_router(admin_utenti.router, prefix="/api/v1/admin/utenti", tags=["admin-utenti"])


@app.get("/")
def root():
    return {"messaggio": "Poliambulatorio API attiva", "documentazione": "/docs"}
