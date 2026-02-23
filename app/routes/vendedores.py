from fastapi import APIRouter, Depends
from fastapi.concurrency import run_in_threadpool
from app.repositories import vendedor_repository
from app.utils.auth import verificar_token
from app.utils.db_utils import get_user_db
from app.schemas.equipe import Vendedor
from typing import List


router = APIRouter(prefix="/vendedores", tags=["Vendedores"])


@router.get("", response_model=List[Vendedor])
async def listar_vendedores(token: dict = Depends(verificar_token)):

    usuario_id = int(token.get("sub"))

    dsn = await run_in_threadpool(get_user_db, usuario_id)

    return await run_in_threadpool(vendedor_repository.listar_vendedores, dsn)