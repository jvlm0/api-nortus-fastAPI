from pydantic import BaseModel

class EquipeResponsavel(BaseModel):
    cod_equipe: int
    nome: str

class Vendedor(BaseModel):
    cod_vendedor: int
    nome: str