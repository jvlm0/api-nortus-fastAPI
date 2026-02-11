from pydantic import BaseModel
from typing import Optional

class ClienteCreate(BaseModel):
    nome: str
    telefone: Optional[str] = None
    cpfcnpj: Optional[str] = None


class ClienteResponse(BaseModel):
    COD_PESSOA: int
    nome: Optional[str] = None
    telefone: Optional[str] = None
    cpfcnpj: Optional[str] = None