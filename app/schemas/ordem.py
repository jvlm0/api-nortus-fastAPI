from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

from app.schemas.cliente import ClienteResponse
from app.schemas.veiculo import VeiculoResponse
from app.schemas.servico import ServicoCreate, ServicoResponse
from app.schemas.produto import ItemProdutoCreate, ItemProdutoResponse


class ProblemaOrdem(BaseModel):
    descricao: str
    solucao: Optional[str] = None


class OrdemCreate(BaseModel):
    observacao: Optional[str] = None
    cod_veiculo: int
    cod_cliente: int
    servicos: Optional[List[ServicoCreate]] = None
    produtos: Optional[List[ItemProdutoCreate]] = None
    problemas: Optional[List[ProblemaOrdem]] = None


class OrdemUpdate(BaseModel):
    cod_ordem: int
    observacao: Optional[str] = None
    cod_veiculo: Optional[int] = None
    cod_cliente: Optional[int] = None
    servicos: Optional[List[ServicoCreate]] = None
    produtos: Optional[List[ItemProdutoCreate]] = None
    servicosRemovidos: Optional[List[int]] = None
    produtosRemovidos: Optional[List[int]] = None
    problemas: Optional[List[ProblemaOrdem]] = None


class OrdemResponse(BaseModel):
    cod_ordem: int
    status: str
    observacao: Optional[str] = None
    cliente: ClienteResponse
    veiculo: VeiculoResponse
    servicos: Optional[List[ServicoResponse]] = None
    produtos: Optional[List[ItemProdutoResponse]] = None
    problemas: Optional[List[ProblemaOrdem]] = None
    imagens: Optional[List[str]] = None


class OrdemResponsePaginated(BaseModel):
    page: int
    page_size: int
    total_pages: int
    data: List[OrdemResponse]


# ---------- Ordens Fechadas ----------

class OrdemFechadaResponse(BaseModel):
    cod_ordem: int
    observacao: Optional[str] = None
    data_fechamento: Optional[datetime] = None
    total_ordem: Optional[float] = None
    cliente: ClienteResponse
    veiculo: VeiculoResponse


class OrdensFechadasResponse(BaseModel):
    data_inicio: str
    data_fim: str
    total_ordens: int
    soma_total: float
    data: List[OrdemFechadaResponse]


# ---------- Ordens Faturadas ----------

class OrdemFaturadaResponse(BaseModel):
    cod_docfiscord: int
    cod_ordem: int
    total: float
    observacao: Optional[str] = None
    nome_cliente: str
    placa: Optional[str] = None
    modelo: Optional[str] = None


class OrdensFaturadasResponse(BaseModel):
    data_inicio: str
    data_fim: str
    total_ordens: int
    soma_total: float
    data: List[OrdemFaturadaResponse]
