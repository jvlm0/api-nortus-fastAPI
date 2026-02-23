from fastapi import APIRouter, Query, HTTPException, Depends
from fastapi.concurrency import run_in_threadpool
from app.repositories import veiculo_repository
from app.schemas.veiculo import VeiculoCreate, VeiculoUpdate
from app.utils.db_utils import get_user_db
from app.utils.auth import verificar_token
from app.utils.consulta_placa import consulta_placa

router = APIRouter(prefix="/veiculos", tags=["Veículos"])


@router.get("/{placa}")
async def buscar_veiculo(placa: str, token: dict = Depends(verificar_token)):

    usuario_id = int(token.get("sub"))
    dsn = await run_in_threadpool(get_user_db, usuario_id)

    resultado = await run_in_threadpool(
        veiculo_repository.buscar_veiculo_por_placa, dsn, placa
    )

    if resultado:
        return {
            "cod_veiculo": resultado[0],
            "placa": resultado[1],
            "modelo": resultado[2],
            "ano": resultado[3],
            "cor": resultado[4],
            "marca": resultado[5]
        }

    # Não achou no banco — consulta API externa (já é async, await direto)
    veiculo = await consulta_placa(placa)

    if not veiculo:
        raise HTTPException(status_code=404, detail="Veículo não encontrado")

    cod_veiculo = await run_in_threadpool(
        veiculo_repository.inserir_veiculo, dsn, veiculo
    )

    return {
        "cod_veiculo": cod_veiculo,
        "placa": veiculo.placa,
        "modelo": veiculo.modelo,
        "ano": veiculo.ano,
        "cor": veiculo.cor,
        "marca": veiculo.marca
    }


@router.post("", status_code=201)
async def inserir_veiculo(veiculo: VeiculoCreate, token: dict = Depends(verificar_token)):

    usuario_id = int(token.get("sub"))
    dsn = await run_in_threadpool(get_user_db, usuario_id)

    cod_veiculo = await run_in_threadpool(
        veiculo_repository.inserir_veiculo, dsn, veiculo
    )

    return {"status": "sucesso", "cod_veiculo": cod_veiculo}


@router.patch("", status_code=200)
async def atualizar_veiculo(veiculo: VeiculoUpdate, token: dict = Depends(verificar_token)):

    usuario_id = int(token.get("sub"))
    dsn = await run_in_threadpool(get_user_db, usuario_id)

    await run_in_threadpool(veiculo_repository.atualizar_veiculo, dsn, veiculo)

    return {"status": "sucesso"}