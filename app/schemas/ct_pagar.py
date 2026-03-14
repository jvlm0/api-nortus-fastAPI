from pydantic import BaseModel
from datetime import date
from typing import List


class CtPagar(BaseModel):
    cod_ct_pagar: int
    data_lancamento: date
    descricao: str
    valor: float
    cod_fornecedor: int
    nome_fornecedor: str


class CtPagarResponse(BaseModel):
    total: float
    cts_pagar: List[CtPagar]