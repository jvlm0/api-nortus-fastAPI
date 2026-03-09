from fastapi import APIRouter, Depends
from fastapi.concurrency import run_in_threadpool
from typing import List
from app.repositories import user_repository
from app.schemas.user import UsuarioCreate, UsuarioUpdate, UsuarioResponse
from app.utils.auth import verificar_admin


router = APIRouter(prefix="/users", tags=["Usuários do app"])


@router.post("", response_model=UsuarioResponse, status_code=201)
async def criar_usuario(usuario: UsuarioCreate, payload=Depends(verificar_admin)):
    return await run_in_threadpool(user_repository.criar_usuario, usuario)


@router.get("", response_model=List[UsuarioResponse])
async def listar_usuarios(payload=Depends(verificar_admin)):
    return await run_in_threadpool(user_repository.listar_usuarios)


@router.get("/{user_id}", response_model=UsuarioResponse)
async def buscar_usuario(user_id: int, payload=Depends(verificar_admin)):
    return await run_in_threadpool(user_repository.buscar_usuario, user_id)


@router.put("/{user_id}", response_model=UsuarioResponse)
async def atualizar_usuario(user_id: int, dados: UsuarioUpdate, payload=Depends(verificar_admin)):
    return await run_in_threadpool(user_repository.atualizar_usuario, user_id, dados)


@router.delete("/{user_id}")
async def deletar_usuario(user_id: int, payload=Depends(verificar_admin)):
    return await run_in_threadpool(user_repository.deletar_usuario, user_id)
