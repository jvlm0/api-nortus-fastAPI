from fastapi import APIRouter, Query, Depends
from fastapi.concurrency import run_in_threadpool
from app.repositories import cliente_repository
from app.schemas.cliente import ClienteCreate
from app.utils.db_utils import get_user_db
from app.utils.auth import verificar_token

router = APIRouter(prefix="/clientes", tags=["Clientes"])


@router.get("")
async def buscar_cliente(q: str = Query(..., description="Nome ou telefone"),
                   page: int = Query(1, ge=1), 
                   page_size: int = Query(10, ge=1, le=100),
                   token: dict = Depends(verificar_token)):
    
    usuario_id = int(token.get("sub"))
    
    dsn = await run_in_threadpool(
        get_user_db,
        usuario_id
    )

    return await run_in_threadpool(
        cliente_repository.buscar_cliente,
        dsn,
        page,
        page_size,
        q
    )




@router.post("", status_code=201)
async def inserir_cliente(cliente: ClienteCreate, token: dict = Depends(verificar_token)):
    
    usuario_id = int(token.get("sub"))

    dsn = await run_in_threadpool(
        get_user_db,
        usuario_id
    )

    cod_cliente = await run_in_threadpool(
        cliente_repository.inserir_cliente,
        dsn,
        cliente
    )


    return {
        "status": "sucesso",
        "cod_cliente": cod_cliente
    }