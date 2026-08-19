from typing import Optional
from pydantic import BaseModel, ConfigDict, field_validator


class PrestazioneBase(BaseModel):
    nome: str
    durata_min: int
    prezzo: float

    @field_validator("nome")
    @classmethod
    def nome_non_vuoto(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Il nome non puo' essere vuoto")
        return v.strip()

    @field_validator("durata_min")
    @classmethod
    def durata_positiva(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("La durata deve essere maggiore di zero")
        return v

    @field_validator("prezzo")
    @classmethod
    def prezzo_non_negativo(cls, v: float) -> float:
        if v < 0:
            raise ValueError("Il prezzo non puo' essere negativo")
        return v


class PrestazioneCreate(PrestazioneBase):
    pass


class PrestazioneUpdate(BaseModel):
    nome: Optional[str] = None
    durata_min: Optional[int] = None
    prezzo: Optional[float] = None

    @field_validator("nome")
    @classmethod
    def nome_non_vuoto(cls, v):
        if v is not None and not v.strip():
            raise ValueError("Il nome non puo' essere vuoto")
        return v.strip() if v is not None else v

    @field_validator("durata_min")
    @classmethod
    def durata_positiva(cls, v):
        if v is not None and v <= 0:
            raise ValueError("La durata deve essere maggiore di zero")
        return v

    @field_validator("prezzo")
    @classmethod
    def prezzo_non_negativo(cls, v):
        if v is not None and v < 0:
            raise ValueError("Il prezzo non puo' essere negativo")
        return v


class PrestazioneOut(BaseModel):
    id: int
    nome: str
    durata_min: int
    prezzo: float
    model_config = ConfigDict(from_attributes=True)


class PrestazioneRef(BaseModel):
    """Vista sintetica usata dall'endpoint pubblico /medici/{id}/prestazioni."""
    id: int
    nome: str
    model_config = ConfigDict(from_attributes=True)
