from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from app.schemas.cliente import ClienteResponse
from app.schemas.veiculo import VeiculoResponse

class OrdemCreate(BaseModel):
    titulo: Optional[str] = None
    descricao: Optional[str] = None
    cod_veiculo: Optional[int] = None
    cod_cliente: Optional[int] = None


class OrdemUpdate(BaseModel): 
    cod_ordem: int
    titulo: Optional[str] = None
    descricao: Optional[str] = None
    cod_veiculo: Optional[int] = None
    cod_cliente: Optional[int] = None


class OrdemResponse(BaseModel):
    cod_ordem: int
    status: str
    titulo: Optional[str] = None
    descricao: Optional[str] = None
    cliente: ClienteResponse
    veiculo: VeiculoResponse