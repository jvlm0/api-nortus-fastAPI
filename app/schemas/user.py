from pydantic import BaseModel, Field
from typing import Optional

class UsuarioCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    senha: str = Field(min_length=6)
    caminho_banco: str = Field(max_length=255)

class UsuarioUpdate(BaseModel):
    username: Optional[str] = Field(default=None, min_length=3, max_length=50)
    senha: Optional[str] = Field(default=None, min_length=6)
    caminho_banco: Optional[str] = Field(default=None, max_length=255)

class UsuarioResponse(BaseModel):
    id: int
    username: str
    caminho_banco: str
