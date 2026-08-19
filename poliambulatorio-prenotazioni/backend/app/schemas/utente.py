from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, field_validator

RUOLI_VALIDI = ("paziente", "operatore", "admin")


class UtenteCreate(BaseModel):
    email: str
    password: str
    ruolo: str = "paziente"
    # Dati profilo paziente (obbligatori solo se ruolo == "paziente")
    nome: Optional[str] = None
    cognome: Optional[str] = None
    codice_fiscale: Optional[str] = None
    telefono: Optional[str] = None
    data_nascita: Optional[date] = None

    @field_validator("email")
    @classmethod
    def email_valida(cls, v):
        if not v or "@" not in v:
            raise ValueError("Email non valida")
        return v.strip().lower()

    @field_validator("password")
    @classmethod
    def password_min(cls, v):
        if not v or len(v) < 6:
            raise ValueError("La password deve avere almeno 6 caratteri")
        return v

    @field_validator("ruolo")
    @classmethod
    def ruolo_valido(cls, v):
        if v not in RUOLI_VALIDI:
            raise ValueError(f"Ruolo non valido (ammessi: {', '.join(RUOLI_VALIDI)})")
        return v


class UtenteUpdate(BaseModel):
    email: Optional[str] = None
    ruolo: Optional[str] = None
    password: Optional[str] = None

    @field_validator("email")
    @classmethod
    def email_valida(cls, v):
        if v is not None and (not v or "@" not in v):
            raise ValueError("Email non valida")
        return v.strip().lower() if v is not None else v

    @field_validator("password")
    @classmethod
    def password_min(cls, v):
        if v is not None and len(v) < 6:
            raise ValueError("La password deve avere almeno 6 caratteri")
        return v

    @field_validator("ruolo")
    @classmethod
    def ruolo_valido(cls, v):
        if v is not None and v not in RUOLI_VALIDI:
            raise ValueError(f"Ruolo non valido (ammessi: {', '.join(RUOLI_VALIDI)})")
        return v


class UtenteAdminOut(BaseModel):
    id: int
    email: str
    ruolo: str
    creato_il: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)
