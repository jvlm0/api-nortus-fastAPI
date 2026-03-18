from pydantic import BaseModel
from typing import Optional

class ClienteCreate(BaseModel):
    tipoPessoa: str
    nome: str
    telefone: Optional[str] = None
    cpfcnpj: Optional[str] = None


class ClienteUpdate(BaseModel):
    tipoPessoa: Optional[str] = None
    nome: Optional[str] = None
    telefone: Optional[str] = None
    cpfcnpj: Optional[str] = None


class ClienteResponse(BaseModel):
    COD_PESSOA: int
    nome: Optional[str] = None
    telefone: Optional[str] = None
    cpfcnpj: Optional[str] = None
