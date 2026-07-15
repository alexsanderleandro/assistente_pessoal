"""Schemas Pydantic (contrato da API), separados dos models do banco
para não misturar validação de entrada/saída com a estrutura de persistência."""
from datetime import datetime

from pydantic import BaseModel


class MonitoredPageCreate(BaseModel):
    url: str
    nome_amigavel: str


class MonitoredPageOut(BaseModel):
    id: int
    url: str
    nome_amigavel: str
    criado_em: datetime

    class Config:
        from_attributes = True
