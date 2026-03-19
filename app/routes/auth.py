from fastapi import APIRouter, Depends
from fastapi.concurrency import run_in_threadpool
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import BaseModel
from app.repositories import auth_repository
from app.utils.auth import criar_tokens, renovar_access_token, security


router = APIRouter(prefix="/auth", tags=["Autenticação"])


class LoginRequest(BaseModel):
    username: str
    senha: str


@router.post("/login")
async def login(credenciais: LoginRequest):

    data = await run_in_threadpool(
        auth_repository.buscar_usuario_login,
        credenciais.username,
        credenciais.senha
    )

    access_token, refresh_token = criar_tokens(data)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "usuario": data["username"],
        "nome": data["nome"],
        "is_admin": data["is_admin"]
    }


@router.post("/refresh")
async def refresh(credentials: HTTPAuthorizationCredentials = Depends(security)):

    novo_access_token = await run_in_threadpool(renovar_access_token, credentials)

    return {
        "access_token": novo_access_token,
        "token_type": "bearer"
    }
