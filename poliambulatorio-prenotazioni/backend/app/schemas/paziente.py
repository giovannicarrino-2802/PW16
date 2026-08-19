from datetime import date
from typing import Optional
from pydantic import BaseModel, ConfigDict


class PazienteOut(BaseModel):
    id: int
    utente_id: int
    nome: str
    cognome: str
    codice_fiscale: str
    telefono: Optional[str] = None
    data_nascita: Optional[date] = None
    model_config = ConfigDict(from_attributes=True)
