from pydantic import BaseModel
from datetime import date
from typing import List


class CtReceber(BaseModel):
    cod_ct_receber: int
    data_lancamento: date
    descricao: str
    valor: float
    cod_cliente: int
    nome_cliente: str


class CtReceberResponse(BaseModel):
    total: float
    cts_receber: List[CtReceber]