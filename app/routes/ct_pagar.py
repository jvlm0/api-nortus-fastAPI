from fastapi import APIRouter, Depends, Query
from fastapi.concurrency import run_in_threadpool
from app.repositories import ctP_repository
from app.schemas.ct_pagar import CtPagarResponse
from app.utils.db_utils import get_user_db
from app.utils.auth import verificar_token
from datetime import date

router = APIRouter(prefix="/contas-a-pagar", tags=["Contas a Pagar"])


@router.get("", response_model=CtPagarResponse)
async def listar_contas_a_pagar(
    data_inicio: date = Query(..., description="Data inicial do intervalo (YYYY-MM-DD)"),
    data_fim: date = Query(..., description="Data final do intervalo (YYYY-MM-DD)"),
    token: dict = Depends(verificar_token),
):
    usuario_id = int(token.get("sub"))
    dsn = await run_in_threadpool(get_user_db, usuario_id)
    return await run_in_threadpool(ctP_repository.list_ct_a_pagar, dsn, data_inicio, data_fim)
