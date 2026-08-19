from pydantic import BaseModel, ConfigDict


class AssociazioneCreate(BaseModel):
    """Corpo della richiesta per associare una prestazione a un medico."""
    prestazione_id: int


class MedicoPrestazioneOut(BaseModel):
    id: int
    medico_id: int
    prestazione_id: int
    model_config = ConfigDict(from_attributes=True)
