from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, model_validator, field_validator


class DisponibilitaBase(BaseModel):
    medico_id: int
    inizio: datetime
    fine: datetime

    @model_validator(mode="after")
    def fine_dopo_inizio(self):
        if self.fine <= self.inizio:
            raise ValueError("La fine deve essere successiva all'inizio")
        return self


class DisponibilitaCreate(DisponibilitaBase):
    pass


class DisponibilitaUpdate(BaseModel):
    medico_id: Optional[int] = None
    inizio: Optional[datetime] = None
    fine: Optional[datetime] = None
    occupato: Optional[bool] = None


class DisponibilitaOut(BaseModel):
    id: int
    medico_id: int
    inizio: datetime
    fine: datetime
    occupato: bool
    model_config = ConfigDict(from_attributes=True)


class DisponibilitaBatchCreate(BaseModel):
    """Generazione ricorrente di slot: per il medico indicato crea slot di
    `durata_min` minuti, nei `giorni` della settimana scelti (0=lunedi ...
    6=domenica), tra `ora_inizio` e `ora_fine`, dal giorno `data_inizio` al
    giorno `data_fine` (inclusi)."""
    medico_id: int
    data_inizio: date
    data_fine: date
    giorni: List[int]        # 0=Lun ... 6=Dom (weekday di Python)
    ora_inizio: str          # "HH:MM"
    ora_fine: str            # "HH:MM"
    durata_min: int = 30

    @field_validator("giorni")
    @classmethod
    def giorni_validi(cls, v):
        if not v:
            raise ValueError("Selezionare almeno un giorno della settimana")
        if any(g < 0 or g > 6 for g in v):
            raise ValueError("Giorni non validi (ammessi 0-6)")
        return sorted(set(v))

    @field_validator("durata_min")
    @classmethod
    def durata_positiva(cls, v):
        if v <= 0:
            raise ValueError("La durata deve essere maggiore di zero")
        return v

    @field_validator("ora_inizio", "ora_fine")
    @classmethod
    def ora_valida(cls, v):
        try:
            hh, mm = v.split(":")
            h, m = int(hh), int(mm)
            assert 0 <= h <= 23 and 0 <= m <= 59
        except Exception:
            raise ValueError("Formato ora non valido (atteso HH:MM)")
        return v

    @model_validator(mode="after")
    def coerenza(self):
        if self.data_fine < self.data_inizio:
            raise ValueError("La data di fine non puo' precedere quella di inizio")
        return self


class DisponibilitaBatchResult(BaseModel):
    creati: List[DisponibilitaOut]
    creati_count: int
    saltati: int
