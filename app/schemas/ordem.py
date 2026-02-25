from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from typing import List

from app.schemas.cliente import ClienteResponse
from app.schemas.veiculo import VeiculoResponse
from app.schemas.servico import ServicoCreate, ServicoResponse
from app.schemas.produto import ItemProdutoCreate, ItemProdutoResponse

class OrdemCreate(BaseModel):
    titulo: Optional[str] = None
    descricao: Optional[str] = None
    cod_veiculo: int
    cod_cliente: int
    servicos: Optional[List[ServicoCreate]] = None
    produtos: Optional[List[ItemProdutoCreate]] = None


class OrdemUpdate(BaseModel): 
    cod_ordem: int
    titulo: Optional[str] = None
    descricao: Optional[str] = None
    cod_veiculo: Optional[int] = None
    cod_cliente: Optional[int] = None
    servicos: Optional[List[ServicoCreate]] = None
    produtos: Optional[List[ItemProdutoCreate]] = None
    servicosRemovidos: Optional[List[int]] = None
    produtosRemovidos: Optional[List[int]] = None


class OrdemResponse(BaseModel):
    cod_ordem: int
    status: str
    titulo: Optional[str] = None
    descricao: Optional[str] = None
    cliente: ClienteResponse
    veiculo: VeiculoResponse
    servicos: Optional[List[ServicoResponse]] = None
    produtos: Optional[List[ItemProdutoResponse]] = None

    
class OrdemResponsePaginated(BaseModel):
    page: int
    page_size: int
    total_pages: int
    data: List[OrdemResponse]