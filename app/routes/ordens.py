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


    ordens = await run_in_threadpool(
        ordem_repository.listar_ordens,
        dsn,
        page,
        page_size
    )

    return ordens



@router.patch("", status_code = 200) 
async def update_ordem(ordem: OrdemUpdate, token: dict = Depends(verificar_token)):

    usuario_id = int(token.get("sub"))
    
    dsn = await run_in_threadpool(
        get_user_db,
        usuario_id
    )

    result = await run_in_threadpool(
        ordem_repository.update_ordem,
        dsn,
        ordem
    )

    if result:
        return {
            "status": "sucesso"
        }



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