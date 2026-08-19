from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, field_validator


class MedicoBase(BaseModel):
    nome: str
    cognome: str
    specializzazione: str

    @field_validator("nome", "cognome", "specializzazione")
    @classmethod
    def non_vuoto(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Il campo non puo' essere vuoto")
        return v.strip()


class MedicoCreate(MedicoBase):
    pass


class MedicoUpdate(BaseModel):
    nome: Optional[str] = None
    cognome: Optional[str] = None
    specializzazione: Optional[str] = None

    @field_validator("nome", "cognome", "specializzazione")
    @classmethod
    def non_vuoto(cls, v):
        if v is not None and not v.strip():
            raise ValueError("Il campo non puo' essere vuoto")
        return v.strip() if v is not None else v


class MedicoOut(BaseModel):
    id: int
    nome: str
    cognome: str
    specializzazione: str
    model_config = ConfigDict(from_attributes=True)


class SlotOut(BaseModel):
    id: int
    medico_id: int
    inizio: datetime
    fine: datetime
    model_config = ConfigDict(from_attributes=True)
