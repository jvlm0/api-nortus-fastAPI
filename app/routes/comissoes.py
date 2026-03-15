from fastapi import APIRouter, Depends, Query
from fastapi.concurrency import run_in_threadpool
from app.repositories import comissao_repository
from app.schemas.comissao import ComissoesResponse
from app.utils.auth import verificar_token
from app.utils.db_utils import get_user_db

router = APIRouter(prefix="/comissoes", tags=["Comissões"])


@router.get("", response_model=ComissoesResponse)
async def listar_comissoes(
    dias: int = Query(default=30, ge=1, le=365, description="Número de dias para buscar comissões (1-365)"),
    token: dict = Depends(verificar_token),
):
    """
    Retorna comissões de produtos e serviços agrupadas por funcionário.

    - **dias**: janela de tempo retroativa a partir de hoje (padrão: 30 dias)
    """
    usuario_id = int(token.get("sub"))
    dsn = await run_in_threadpool(get_user_db, usuario_id)
    return await run_in_threadpool(comissao_repository.listar_comissoes, dsn, dias)
