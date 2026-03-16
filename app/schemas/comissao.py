from pydantic import BaseModel
from typing import List, Optional
from datetime import date


# ---------- Itens individuais ----------

class ComissaoProduto(BaseModel):
    cod_comprod: int
    percento: float
    valor_comissao: float
    cod_itprodord: int
    descricao: Optional[str] = None
    total: float
    data: Optional[date] = None
    cod_ordem: int
    obs_ordem: Optional[str] = None


class ComissaoServico(BaseModel):
    cod_comprod: int
    percento: float
    valor_comissao: float
    cod_despadic: int
    descricao: Optional[str] = None
    total: float
    data: Optional[date] = None
    cod_ordem: int
    obs_ordem: Optional[str] = None


# ---------- Agrupamento por funcionário ----------

class ComissaoFuncionario(BaseModel):
    cod_funcionario: int
    nome_funcionario: str
    total_comissao_produtos: float
    total_comissao_servicos: float
    total_comissao: float
    produtos: List[ComissaoProduto]
    servicos: List[ComissaoServico]


# ---------- Resposta geral ----------

class ComissoesResponse(BaseModel):
    data_inicio: date
    data_fim: date
    total_geral: float
    funcionarios: List[ComissaoFuncionario]
