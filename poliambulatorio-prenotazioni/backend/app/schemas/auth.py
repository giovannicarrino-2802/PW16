from datetime import date
from typing import Optional
from pydantic import BaseModel, ConfigDict

class RegisterRequest(BaseModel):
    email: str
    password: str
    nome: str
    cognome: str
    codice_fiscale: str
    telefono: Optional[str] = None
    data_nascita: Optional[date] = None

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UserOut(BaseModel):
    id: int
    email: str
    ruolo: str
    model_config = ConfigDict(from_attributes=True)
