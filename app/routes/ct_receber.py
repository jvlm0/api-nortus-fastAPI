from fastapi import APIRouter, Depends, Query
from fastapi.concurrency import run_in_threadpool
from app.repositories import ctR_repository
from app.schemas.ct_receber import CtReceberResponse
from app.utils.db_utils import get_user_db
from app.utils.auth import verificar_token
from datetime import date

router = APIRouter(prefix="/contas-a-receber", tags=["Contas a Receber"])


@router.get("", response_model=CtReceberResponse)
async def listar_contas_a_receber(
    data_inicio: date = Query(..., description="Data inicial do intervalo (YYYY-MM-DD)"),
    data_fim: date = Query(..., description="Data final do intervalo (YYYY-MM-DD)"),
    token: dict = Depends(verificar_token),
):
    usuario_id = int(token.get("sub"))
    dsn = await run_in_threadpool(get_user_db, usuario_id)
    return await run_in_threadpool(ctR_repository.list_ct_a_receber, dsn, data_inicio, data_fim)
