from fastapi import APIRouter, Query, Depends

from fastapi.concurrency import run_in_threadpool
from app.repositories import ordem_repository
from app.schemas.ordem import OrdemCreate, OrdemUpdate, OrdemResponsePaginated, OrdemResponse
from app.utils.auth import verificar_token
from app.utils.db_utils import get_user_db



router = APIRouter(prefix="/ordens", tags=["Ordens de Serviço"])

@router.post("", status_code=201)
async def inserir_ordem(ordem: OrdemCreate, token: dict = Depends(verificar_token)):

    usuario_id = int(token.get("sub"))
    
    dsn = await run_in_threadpool(
        get_user_db,
        usuario_id
    )

    cod_ordem = await run_in_threadpool(
        ordem_repository.inserir_ordem,
        dsn,
        ordem
    )

    return {
        "status": "sucesso",
        "cod_ordem": cod_ordem
        }




@router.get("", response_model=OrdemResponsePaginated)
async def listar_ordens(page: int = Query(1, ge=1), 
                  page_size: int = Query(10, ge=1, le=100),   
                  token: dict = Depends(verificar_token)):

    usuario_id = int(token.get("sub"))

    dsn = await run_in_threadpool(
        get_user_db,
        usuario_id
    )


    return await run_in_threadpool(
        ordem_repository.listar_ordens,
        dsn,
        page,
        page_size
    )



@router.patch("", status_code=200)
async def update_ordem(ordem: OrdemUpdate, token: dict = Depends(verificar_token)):

    usuario_id = int(token.get("sub"))
    dsn = await run_in_threadpool(get_user_db, usuario_id)

    await run_in_threadpool(ordem_repository.update_ordem, dsn, ordem)

    ordem_atualizada = await run_in_threadpool(
        ordem_repository.get_ordem, dsn, ordem.cod_ordem
    )

    return ordem_atualizada


@router.get("/{cod_ordem}", response_model=OrdemResponse)
async def get_ordem(cod_ordem, token: dict = Depends(verificar_token)):

    usuario_id = int(token.get("sub"))

    dsn = await run_in_threadpool(
        get_user_db,
        usuario_id
    )


    ordem = await run_in_threadpool(
        ordem_repository.get_ordem,
        dsn,
        cod_ordem
    )

    return ordem

@router.delete("/{cod_ordem}")
async def delete_ordem(
    cod_ordem: int,
    trust: str,
    token: dict = Depends(verificar_token)
):

    usuario_id = int(token.get("sub"))

    dsn = await run_in_threadpool(
        get_user_db,
        usuario_id
    )


    count = await run_in_threadpool(
        ordem_repository.get_count_itens,
        dsn,
        cod_ordem
    )

    if (count == 0):
        cod_ordem_r = await run_in_threadpool(
            ordem_repository.delete_ordem,
            dsn,
            cod_ordem
        )

        return {
            "status": "sucesso",
            "cod_ordem": cod_ordem_r
        }
    if count > 0 and trust == 'n':
        return {
            "quantidade": count,
            "cod_ordem": cod_ordem
        }
    elif count > 0 and trust == 'y':
        cod_ordem_r = await run_in_threadpool(
            ordem_repository.delete_ordem,
            dsn,
            cod_ordem
        )

        return {
            "status": "sucesso",
            "cod_ordem": cod_ordem_r
        }
