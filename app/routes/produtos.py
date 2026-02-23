from fastapi import APIRouter, Query, Depends
from fastapi.concurrency import run_in_threadpool
from app.repositories import produto_repository
from app.utils.db_utils import get_user_db
from app.utils.auth import verificar_token

router = APIRouter(prefix="/produtos", tags=["Produtos"])


@router.get("")
async def buscar_produto(
    q: str = Query(..., description="Nome do produto"),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    token: dict = Depends(verificar_token)
):
    usuario_id = int(token.get("sub"))

    dsn = await run_in_threadpool(get_user_db, usuario_id)

    return await run_in_threadpool(
        produto_repository.buscar_produto, dsn, page, page_size, q
    )