from pydantic import BaseModel
from typing import Optional
from typing import List
from decimal import Decimal

from app.schemas.equipe import EquipeResponsavel, Vendedor




class ItemProdutoCreate(BaseModel):
    cod_subproduto: int
    quantidade: float
    valorUnitario: float
    desconto: float
    cods_vendedores: List[int]

class ProdutoResponse(BaseModel):
    cod_subproduto: int
    nome: str
    marca: str
    preco: Decimal


class ItemProdutoResponse(BaseModel):
    cod_itemProduto: int
    nome: str
    marca: str
    quantidade: Decimal
    valorUnitario: Decimal
    desconto: Decimal
    vendedores: List[Vendedor]
