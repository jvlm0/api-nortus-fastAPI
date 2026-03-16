from fastapi import APIRouter, Depends, Query
from fastapi.concurrency import run_in_threadpool
from app.repositories import comissao_repository
from app.schemas.comissao import ComissoesResponse
from app.utils.auth import verificar_token
from app.utils.db_utils import get_user_db
from datetime import date

router = APIRouter(prefix="/comissoes", tags=["Comissões"])


@router.get("", response_model=ComissoesResponse)
async def listar_comissoes(
    data_inicio: date = Query(..., description="Data inicial do intervalo (YYYY-MM-DD)"),
    data_fim: date = Query(..., description="Data final do intervalo (YYYY-MM-DD)"),
    token: dict = Depends(verificar_token),
):
    usuario_id = int(token.get("sub"))
    dsn = await run_in_threadpool(get_user_db, usuario_id)
    return await run_in_threadpool(comissao_repository.listar_comissoes, dsn, data_inicio, data_fim)
