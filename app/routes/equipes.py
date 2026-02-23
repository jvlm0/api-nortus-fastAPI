from fastapi import APIRouter, Depends
from fastapi.concurrency import run_in_threadpool
from app.repositories import equipe_repository
from app.utils.auth import verificar_token
from app.utils.db_utils import get_user_db
from app.schemas.equipe import EquipeResponsavel
from typing import List


router = APIRouter(prefix="/equipes", tags=["Equipes"])


@router.get("", response_model=List[EquipeResponsavel])
async def listar_equipes(token: dict = Depends(verificar_token)):

    usuario_id = int(token.get("sub"))

    dsn = await run_in_threadpool(get_user_db, usuario_id)

    return await run_in_threadpool(equipe_repository.listar_equipes, dsn)