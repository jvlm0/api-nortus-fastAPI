from fastapi import APIRouter, Query, HTTPException, Depends
from datetime import datetime

from fastapi.concurrency import run_in_threadpool
from app.database import get_connection
from app.repositories import ordem_repository
from app.schemas.ordem import OrdemCreate, OrdemUpdate, OrdemResponsePaginated, OrdemResponse
from typing import List
from app.utils.auth import verificar_token
from app.utils.db_utils import get_user_db
from app.db_utils.servico_db import inserir_servicos, buscar_servicos, deletar_servicos
from app.db_utils.produto_db import inserir_produtos, buscar_produtos, deletar_produtos
from app.utils.ordem_calc import calculaTotal
from app.utils.ordem_utils import split_obs
from app.schemas.cliente import ClienteResponse
from app.schemas.veiculo import VeiculoResponse


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

        # insere no banco do cliente (VPN)
    ordens = await run_in_threadpool(
        ordem_repository.listar_ordens,
        dsn,
        page,
        page_size
    )

    return ordens



@router.patch("", status_code = 200) 
def update_ordem(ordem: OrdemUpdate, token: dict = Depends(verificar_token)):

    usuario_id = token.get("sub")
    caminho_banco = get_user_db(int(usuario_id))
    conn = get_connection(caminho_banco)
    cursor = conn.cursor()
    
    
    observacao = (ordem.titulo or "") + " - " + (ordem.descricao or "")

    try:

        
        sql = """
            UPDATE ordem set cod_cliente = ?, cod_equipamento = ?, OBSORDEM = ?
            WHERE COD_ORDEM = ?
            RETURNING cod_ordem;
        """
        cursor.execute(sql, (ordem.cod_cliente, ordem.cod_veiculo, observacao, ordem.cod_ordem))

        resultado = cursor.fetchone()[0]

        if not resultado:
            raise HTTPException(status_code=404, detail="Ordem não encontrada")
        
        if ordem.servicos != None:
            inserir_servicos(cursor, ordem.servicos, ordem.cod_ordem)
        if ordem.produtos != None:
            inserir_produtos(cursor, ordem.produtos, ordem.cod_ordem, datetime.now().strftime("%Y-%m-%d"))
        
        if ordem.servicosRemovidos != None:
            deletar_servicos(cursor, ordem.servicosRemovidos)
        
        if ordem.produtosRemovidos != None:
            deletar_produtos(cursor, ordem.produtosRemovidos)
        
        conn.commit()

        

        return {
            "status": "sucesso"
        }

    finally:
        cursor.close()
        conn.close()



@router.get("/{cod_ordem}", response_model=OrdemResponse)
def get_ordem(cod_ordem, token: dict = Depends(verificar_token)):

    usuario_id = token.get("sub")
    caminho_banco = get_user_db(int(usuario_id))
    conn = get_connection(caminho_banco)
    cursor = conn.cursor()


    try:
        sql = """
            SELECT ordem.cod_ordem,
                   ordem.status,
                   ordem.OBSORDEM,
                   cliente.cod_cliente,
                   pessoa.nome,
                   pessoa.telrel,
                   pessoa.cpfcnpj,
                   equipamento.cod_equipamento,
                   equipamento.descricao,
                   equipamento.placa,
                   equipamento.ano,
                   equipamento.kmatual
            FROM ordem
            LEFT JOIN cliente ON ordem.cod_cliente = cliente.cod_cliente
            LEFT JOIN pessoa ON cliente.cod_pessoa = pessoa.cod_pessoa
            LEFT JOIN equipamento ON ordem.cod_equipamento = equipamento.cod_equipamento
            WHERE ordem.cod_ordem = ?
        """

        cursor.execute(sql, (cod_ordem,))
        r = cursor.fetchone()
        
        titulo, descricao = r[2]

        cliente = ClienteResponse(COD_PESSOA=r[3], nome=r[4], telefone=r[5], cpfcnpj= r[6])

        veiculo = VeiculoResponse(cod_veiculo= r[7], 
                                  descricao = r[8], 
                                  placa= r[9], 
                                  ano= r[10], 
                                  kmatual=r[11])

        ordem = OrdemResponse(cod_ordem= r[0], 
                              status=r[1], 
                              titulo=titulo, 
                              descricao= descricao, 
                              cliente=cliente, 
                              veiculo=veiculo)

        ordem.servicos = buscar_servicos(cursor, ordem.cod_ordem)
        ordem.produtos = buscar_produtos(cursor, cod_ordem)

        return ordem

    finally:
        cursor.close()
        conn.close()
