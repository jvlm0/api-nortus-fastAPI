from pydantic import BaseModel
from typing import Optional

class VeiculoCreate(BaseModel):
    placa: str
    cod_cliente: int
    modelo: Optional[str] = None
    ano: Optional[str] = None
    kmatual: Optional[int] = None
    cor: Optional[str] = None
    chassi: Optional[str] = None
    marca: Optional[str] = None


class VeiculoResponse(BaseModel):
    placa: Optional[str] = None
    cod_veiculo: Optional[int] = None
    modelo: Optional[str] = None
    ano: Optional[str] = None
    kmatual: Optional[int] = None
    cor: Optional[str] = None
    chassi: Optional[str] = None
    marca: Optional[str] = None



class VeiculoUpdate(BaseModel):
    cod_veiculo: int
    cod_cliente: int
    modelo: Optional[str] = None
    ano: Optional[str] = None
    kmatual: Optional[int] = None