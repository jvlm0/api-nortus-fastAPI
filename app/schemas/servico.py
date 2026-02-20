from pydantic import BaseModel
from typing import Optional
from typing import List

from app.schemas.equipe import EquipeResponsavel, Vendedor




class ServicoCreate(BaseModel):
    descricao: str
    quantidade: float
    valorUnitario: float
    desconto: float
    cod_equipe: int
    cods_vendedores: List[int] 





class ServicoResponse(BaseModel):
    descricao: str
    quantidade: float
    valorUnitario: float
    desconto: float
    equipe: EquipeResponsavel
    vendedores: List[Vendedor]
