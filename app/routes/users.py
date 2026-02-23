from fastapi import APIRouter, Depends
from fastapi.concurrency import run_in_threadpool
from app.repositories import user_repository
from app.schemas.user import UsuarioCreate, UsuarioResponse


router = APIRouter(prefix="/users", tags=["Usuários do app"])


@router.post("", response_model=UsuarioResponse, status_code=201)
async def criar_usuario(usuario: UsuarioCreate):

    return await run_in_threadpool(user_repository.criar_usuario, usuario)