from fastapi import APIRouter, Query, Depends, HTTPException
from fastapi.concurrency import run_in_threadpool
from app.repositories import cliente_repository
from app.schemas.cliente import ClienteCreate, ClienteUpdate
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
        "cod_pessoa": cod_cliente
    }


@router.put("/{cod_cliente}")
async def atualizar_cliente(cod_cliente: int, cliente: ClienteUpdate, token: dict = Depends(verificar_token)):

    usuario_id = int(token.get("sub"))

    dsn = await run_in_threadpool(
        get_user_db,
        usuario_id
    )

    resultado = await run_in_threadpool(
        cliente_repository.atualizar_cliente,
        dsn,
        cod_cliente,
        cliente
    )

    if resultado is None:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")

    return {
        "status": "sucesso",
        "cod_cliente": resultado
    }
