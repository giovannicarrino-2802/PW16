from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

class AppuntamentoCreate(BaseModel):
    disponibilita_id: int
    prestazione_id: int

class AppuntamentoPerPaziente(BaseModel):
    """Prenotazione effettuata dalla segreteria per conto di un paziente."""
    paziente_id: int
    disponibilita_id: int
    prestazione_id: int

class AppuntamentoUpdate(BaseModel):
    stato: str

class AppuntamentoAdminUpdate(BaseModel):
    """Modifica di una prenotazione da parte di segreteria/admin: cambio stato
    (annullata/completata) oppure riprogrammazione su un nuovo slot."""
    stato: Optional[str] = None
    disponibilita_id: Optional[int] = None

class AppuntamentoOut(BaseModel):
    id: int
    medico_id: int
    prestazione_id: int
    inizio: datetime
    fine: datetime
    stato: str
    model_config = ConfigDict(from_attributes=True)

class AppuntamentoDettaglioOut(BaseModel):
    """Vista arricchita per l'agenda di segreteria/admin."""
    id: int
    paziente_id: int
    paziente_nome: str
    medico_id: int
    medico_nome: str
    prestazione_id: int
    prestazione_nome: str
    inizio: datetime
    fine: datetime
    stato: str
