import json
from fastapi import APIRouter, Query, Depends, UploadFile, File, Form
from typing import List, Optional

from fastapi.concurrency import run_in_threadpool
from app.repositories import ordem_repository
from app.schemas.ordem import OrdemCreate, OrdemUpdate, OrdemResponsePaginated, OrdemResponse
from app.utils.auth import verificar_token
from app.utils.db_utils import get_user_db
from app.utils.imagens_utils import salvar_imagens_ordem, listar_imagens_ordem, remover_imagens_ordem


router = APIRouter(prefix="/ordens", tags=["Ordens de Serviço"])

@router.post("", status_code=201)
async def inserir_ordem(
    dados: str = Form(...),
    imagens: Optional[List[UploadFile]] = File(default=None),
    token: dict = Depends(verificar_token)
):
    ordem = OrdemCreate(**json.loads(dados))

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

    urls_imagens = []
    if imagens:
        urls_imagens = await run_in_threadpool(
            salvar_imagens_ordem,
            cod_ordem,
            imagens
        )

    return {
        "status": "sucesso",
        "cod_ordem": cod_ordem,
        "imagens": urls_imagens
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
async def update_ordem(
    dados: str = Form(...),
    imagens: Optional[List[UploadFile]] = File(default=None),
    token: dict = Depends(verificar_token)
):
    ordem = OrdemUpdate(**json.loads(dados))

    usuario_id = int(token.get("sub"))
    dsn = await run_in_threadpool(get_user_db, usuario_id)

    await run_in_threadpool(ordem_repository.update_ordem, dsn, ordem)

    # Salva novas imagens diretamente no diretório definitivo da ordem
    if imagens:
        await run_in_threadpool(
            salvar_imagens_ordem,
            ordem.cod_ordem,
            imagens
        )

    ordem_atualizada = await run_in_threadpool(
        ordem_repository.get_ordem, dsn, ordem.cod_ordem
    )

    # Injeta as URLs das imagens salvas na resposta
    imagens_salvas = await run_in_threadpool(listar_imagens_ordem, ordem.cod_ordem)
    resposta = ordem_atualizada.dict() if hasattr(ordem_atualizada, 'dict') else dict(ordem_atualizada)
    resposta["imagens"] = imagens_salvas

    return resposta


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

    imagens_salvas = await run_in_threadpool(listar_imagens_ordem, int(cod_ordem))
    ordem.imagens = imagens_salvas

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
